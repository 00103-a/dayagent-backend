"""个性化新闻独立接口"""

from fastapi import APIRouter, Query

from agent_service.tools.news import get_personalized_news

router = APIRouter(prefix="/news", tags=["新闻"])


@router.get("")
async def get_news(
    goals: str = Query("", description="用户目标，逗号分隔"),
    yesterday_summary: str = Query("", description="昨日总结"),
):
    """获取个性化新闻（3~5条）"""
    goals_list = [g.strip() for g in goals.split(",") if g.strip()] if goals else []
    text = await get_personalized_news(goals_list, yesterday_summary)
    return {"news_text": text}
