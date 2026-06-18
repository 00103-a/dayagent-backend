import asyncio
from dataclasses import dataclass

from agent_service.agents.memory import analyze_history
from agent_service.schemas.plan_request import ParcelStatus, PlanRequest
from agent_service.tools.registry import get_tool


@dataclass
class PlanningContext:
    weather_info: dict
    course_info: str
    chaoxing_tasks: str
    parcels_summary: str
    parcel_statuses: list[ParcelStatus]
    memory_hint: str


async def collect_planning_context(req: PlanRequest) -> PlanningContext:
    settings = req.user_settings or {}
    weather_tool = get_tool("weather")
    course_tool = get_tool("course")
    chaoxing_tool = get_tool("chaoxing")
    parcel_tool = get_tool("parcel")

    weather_result, chaoxing_result, course_result, parcel_result = await asyncio.gather(
        weather_tool.run({
            "location": req.location,
            "api_key": settings.get("weather_api_key", ""),
        }),
        chaoxing_tool.run({
            "username": settings.get("chaoxing_username", ""),
            "password": settings.get("chaoxing_password", ""),
        }),
        course_tool.run({
            "semester_start": settings.get("semester_start", ""),
            "user_id": req.user_id,
        }),
        parcel_tool.run({
            "parcels": [p.model_dump() for p in req.parcels],
        }),
    )

    weather_info = weather_result.data if weather_result.ok else {
        "weather": "天气数据暂不可用",
        "condition_text": "",
        "condition_icon": "",
    }

    course_info = course_result.data.get("text", "") if course_result.ok else "今日课表暂不可用"
    chaoxing_tasks = chaoxing_result.data.get("text", "") if chaoxing_result.ok else "学习通任务暂不可用"

    parcel_data = parcel_result.data if parcel_result.ok else {
        "summary": "",
        "statuses": [],
    }

    parcel_statuses = [
        ParcelStatus(
            tracking_no=r["tracking_no"],
            carrier=r["carrier"],
            remark=r.get("remark", ""),
            state=r["state"],
            is_delivered=r["is_delivered"],
            latest_context=r["latest_context"],
            latest_time=r["latest_time"],
            details=r.get("details", []),
            pickup_code=r.get("pickup_code", ""),
            is_waiting_pickup=r.get("is_waiting_pickup", False),
        )
        for r in parcel_data.get("statuses", [])
    ]

    try:
        memory_hint = await analyze_history(req.user_id)
    except Exception as e:
        print(f"[Plan] 长期记忆分析降级: {e}")
        memory_hint = ""

    return PlanningContext(
        weather_info=weather_info,
        course_info=course_info,
        chaoxing_tasks=chaoxing_tasks,
        parcels_summary=parcel_data.get("summary", ""),
        parcel_statuses=parcel_statuses,
        memory_hint=memory_hint,
    )
