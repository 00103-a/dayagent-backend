import asyncio

from fastapi import APIRouter, HTTPException

from agent_service.schemas.plan_request import PlanRequest, PlanResponse, ParcelStatus
from agent_service.tools.weather import fetch_weather
from agent_service.tools.chaoxing import fetch_chaoxing_tasks
from agent_service.tools.courses import get_today_courses
# news 已从规划 Prompt 剥离，前端独立调用 GET /news 接口
from agent_service.tools.parcel import query_parcels_detailed, query_parcels_batch
from agent_service.agents.planner import generate_plan
from agent_service.agents.memory import analyze_history

router = APIRouter()


async def _get_course_info(semester_start: str = "", user_id: str = "") -> str:
    """读取本地课表（同步操作，用 async wrapper 方便 gather）"""
    return get_today_courses(semester_start, user_id)


async def _get_parcel_info(
    parcels: list,
    kuaidi100_customer: str = "",
    kuaidi100_key: str = "",
) -> tuple[str, list[ParcelStatus]]:
    """查询快递状态，返回 (汇总文本, 结构化状态列表)"""
    if not parcels:
        return "", []

    parcel_dicts = [p.model_dump() for p in parcels]

    # Pass per-user kuaidi100 credentials
    detailed = await query_parcels_detailed(
        parcel_dicts,
        customer=kuaidi100_customer if kuaidi100_customer else None,
        key=kuaidi100_key if kuaidi100_key else None,
    )
    summary = await query_parcels_batch(parcel_dicts, pre_queried=detailed)

    statuses = [
        ParcelStatus(
            tracking_no=r["tracking_no"],
            carrier=r["carrier"],
            remark=r.get("remark", ""),
            state=r["state"],
            is_delivered=r["is_delivered"],
            latest_context=r["latest_context"],
            latest_time=r["latest_time"],
            details=r.get("details", []),
        )
        for r in detailed
    ]
    return summary, statuses


@router.post("/generate-plan", response_model=PlanResponse)
async def generate_plan_endpoint(req: PlanRequest) -> PlanResponse:
    """核心接口：生成今日规划"""
    settings = req.user_settings or {}
    llm_key = settings.get("llm_api_key", "")
    llm_base = settings.get("llm_base_url", "")
    llm_model = settings.get("llm_model", "")
    weather_key = settings.get("weather_api_key", "")

    if not llm_key:
        raise HTTPException(status_code=400, detail={
            "error": "请先在设置中配置 DeepSeek API Key",
            "guide": "deepseek"
        })

    # 1. 并行拉取多源数据（互不依赖，asyncio.gather 同时发请求）
    weather_info, chaoxing_tasks, course_info, (parcels_summary, parcel_statuses) = await asyncio.gather(
        fetch_weather(req.location, api_key=weather_key),
        fetch_chaoxing_tasks(
            username=settings.get("chaoxing_username", ""),
            password=settings.get("chaoxing_password", ""),
        ),
        _get_course_info(semester_start=settings.get("semester_start", ""), user_id=req.user_id),
        _get_parcel_info(
            req.parcels,
            kuaidi100_customer=settings.get("kuaidi100_customer", ""),
            kuaidi100_key=settings.get("kuaidi100_key", ""),
        ),
    )

    # 2. 长期记忆分析（第二阶段，数据库不可用时降级）
    try:
        memory_hint = await analyze_history(req.user_id)
    except Exception as e:
        print(f"[Plan] 长期记忆分析降级: {e}")
        memory_hint = ""

    # 3. 调 LLM 生成规划
    result = await generate_plan(
        weather_info=weather_info,
        chaoxing_tasks=chaoxing_tasks,
        course_info=course_info,
        yesterday_summary=req.yesterday_summary,
        goals=req.goals,
        memory_hint=memory_hint,
        parcells_info=parcels_summary,
        llm_api_key=llm_key,
        llm_base_url=llm_base,
        llm_model=llm_model,
    )

    # 4. 附加快递状态（Java 端用于更新数据库）
    result.parcels = parcel_statuses

    return result
