

from fastapi import APIRouter, HTTPException

from agent_service.schemas.plan_request import PlanRequest, PlanResponse

from agent_service.agents.planner import generate_plan



from agent_service.workflows.planning import collect_planning_context

router = APIRouter()





@router.post("/generate-plan", response_model=PlanResponse)
async def generate_plan_endpoint(req: PlanRequest) -> PlanResponse:
    """核心接口：生成今日规划"""
    settings = req.user_settings or {}
    llm_key = settings.get("llm_api_key", "")
    llm_base = settings.get("llm_base_url", "")
    llm_model = settings.get("llm_model", "")


    if not llm_key:
        raise HTTPException(status_code=400, detail={
            "error": "请先在设置中配置 DeepSeek API Key",
            "guide": "deepseek"
        })
    context = await collect_planning_context(req)
    


    # 3. 调 LLM 生成规划
    result = await generate_plan(
        weather_info=context.weather_info,
        chaoxing_tasks=context.chaoxing_tasks,
        course_info=context.course_info,
        yesterday_summary=req.yesterday_summary,
        goals=req.goals,
        memory_hint=context.memory_hint,
        parcells_info=context.parcels_summary,
        llm_api_key=llm_key,
        llm_base_url=llm_base,
        llm_model=llm_model,
    )

    # 4. 附加快递状态（Java 端用于更新数据库）
    result.parcels = context.parcel_statuses

    return result
