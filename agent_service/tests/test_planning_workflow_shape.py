import asyncio

from agent_service.schemas.plan_request import PlanRequest
from agent_service.workflows.planning import (
    PlanningContext,
    ToolContext,
    collect_planning_context,
    collect_tool_context,
)


async def main():
    req = PlanRequest(
        user_id="1",
        location="南昌",
        user_settings={},
        parcels=[],
    )

    tool_context = await collect_tool_context(req)
    assert isinstance(tool_context, ToolContext)
    assert isinstance(tool_context.weather_info, dict)
    assert isinstance(tool_context.course_info, str)
    assert isinstance(tool_context.chaoxing_tasks, str)
    assert isinstance(tool_context.parcels_summary, str)
    assert isinstance(tool_context.parcel_statuses, list)

    planning_context = await collect_planning_context(req)
    assert isinstance(planning_context, PlanningContext)
    assert isinstance(planning_context.weather_info, dict)
    assert isinstance(planning_context.course_info, str)
    assert isinstance(planning_context.chaoxing_tasks, str)
    assert isinstance(planning_context.parcels_summary, str)
    assert isinstance(planning_context.parcel_statuses, list)
    assert isinstance(planning_context.memory_hint, str)

    print("planning workflow shape ok")


if __name__ == "__main__":
    asyncio.run(main())