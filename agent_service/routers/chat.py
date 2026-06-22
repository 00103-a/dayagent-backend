"""AI chat endpoint.

Router 只处理 HTTP 形状，不写 Agent 逻辑。
真正的“分析需求/收集上下文/选工具/生成回复”都放在 workflow 里。
"""
from fastapi import APIRouter, Body

from agent_service.workflows.chat import run_chat_workflow

router = APIRouter(prefix="/chat", tags=["AI 对话"])


@router.post("")
async def chat(payload: dict = Body(...)) -> dict:
    """Agent-style chat.

    Java passes trusted user context and user settings. Python decides how to
    analyze the request and whether any agent tools are useful for the reply.
    """
    result = await run_chat_workflow(payload)
    # 返回 reply 之外的解释字段，给前端显示“参考了什么/用了什么工具”。
    # 这能帮助我们判断它是否真的像 Agent，而不是普通聊天框。
    return {
        "reply": result.reply,
        "need_analysis": result.need_analysis,
        "used_context": result.used_context,
        "tool_results": result.tool_results,
    }
