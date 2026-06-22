

from fastapi import APIRouter, HTTPException

from agent_service.schemas.plan_request import PlanRequest, PlanResponse
from agent_service.workflows.planning import run_planning_workflow


router = APIRouter()





@router.post("/generate-plan", response_model=PlanResponse)
async def generate_plan_endpoint(req: PlanRequest) -> PlanResponse:
    """核心接口：生成今日规划"""
    settings = req.user_settings or {}
    llm_key = settings.get("llm_api_key", "")

    if not llm_key:
        raise HTTPException(status_code=400, detail={
            "error": "请先在设置中配置 DeepSeek API Key",
            "guide": "deepseek"
        })
    return await run_planning_workflow(req)
