"""个性化新闻独立接口"""

from fastapi import APIRouter, Query

from agent_service.tools.news import get_personalized_news

router = APIRouter(prefix="/news", tags=["新闻"])


@router.get("")
async def get_news(
    goals: str = Query("", description="用户目标，逗号分隔"),
    yesterday_summary: str = Query("", description="昨日总结"),
    llm_key: str = Query("", description="用户的 LLM API Key"),
    llm_base_url: str = Query("", description="LLM API 地址"),
    llm_model: str = Query("", description="LLM 模型名"),
    news_api_key: str = Query("", description="用户的天行数据 API Key"),
):
    """获取个性化新闻（3~5条）"""
    goals_list = [g.strip() for g in goals.split(",") if g.strip()] if goals else []
    text = await get_personalized_news(
        goals_list, yesterday_summary,
        llm_key=llm_key, llm_base_url=llm_base_url,
        llm_model=llm_model, news_api_key=news_api_key,
    )
    return {"news_text": text}
