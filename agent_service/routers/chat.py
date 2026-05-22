"""
对话 AI 助手 — 通用聊天端点
"""
import os
from pathlib import Path

import httpx
from fastapi import APIRouter, Body
from openai import AsyncOpenAI

router = APIRouter(prefix="/chat", tags=["AI 对话"])

_PROMPT_DIR = Path(__file__).parent.parent / "prompts"

SYSTEM_PROMPT = """你是一个贴心的个人 AI 助手，名叫 DayAgent。你的风格是：
- 温暖、鼓励、像朋友一样自然
- 回复简洁（通常 2-5 句），不要长篇大论
- 如果用户提到目标、计划、时间管理，给出具体可行的建议
- 如果用户情绪低落，先共情再鼓励
- 用中文回复，语气轻松不做作"""


def _build_http_client() -> httpx.AsyncClient:
    proxy = os.getenv("LLM_PROXY", "")
    kwargs: dict = {
        "timeout": httpx.Timeout(60.0, connect=15.0),
        "follow_redirects": True,
        "trust_env": False,
    }
    if proxy:
        kwargs["proxy"] = proxy
        kwargs["verify"] = False
    return httpx.AsyncClient(**kwargs)


def _create_llm_client() -> AsyncOpenAI:
    http_client = _build_http_client()
    return AsyncOpenAI(
        base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
        api_key=os.getenv("LLM_API_KEY", "sk-placeholder"),
        http_client=http_client,
    )


@router.post("")
async def chat(payload: dict = Body(...)) -> dict:
    """通用 AI 对话

    Body:
      { "userId": 1, "message": "...", "context": { ... } }
    """
    user_id = payload.get("userId", 1)
    message = (payload.get("message") or "").strip()
    context = payload.get("context")

    if not message:
        return {"reply": "你想聊什么？"}

    # 构建用户消息（可选包含上下文）
    user_content = message
    if context and isinstance(context, dict):
        ctx_parts = []
        active_goals = context.get("activeGoals")
        if isinstance(active_goals, list) and active_goals:
            goals_text = "\n".join(
                f"- [{g.get('type', '')}] {g.get('content', '')}"
                for g in active_goals[:5]
                if isinstance(g, dict)
            )
            if goals_text:
                ctx_parts.append(f"用户当前目标：\n{goals_text}")

        yesterday = context.get("yesterday")
        if yesterday and isinstance(yesterday, str):
            ctx_parts.append(f"用户昨日总结：{yesterday}")

        if ctx_parts:
            user_content = f"{message}\n\n背景信息：\n" + "\n".join(ctx_parts)

    model = os.getenv("LLM_MODEL", "deepseek-chat")
    ai_client = _create_llm_client()

    try:
        stream = await ai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.8,
            max_tokens=800,
            stream=True,
        )
        content = ""
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                content += delta

        if not content:
            return {"reply": "嗯...让我想想该怎么说。"}

        return {"reply": content.strip()}

    except Exception as e:
        import logging
        logging.getLogger("chat").error(f"LLM 调用失败: {e}")
        return {"reply": "我暂时无法回复，请稍后再试。"}
