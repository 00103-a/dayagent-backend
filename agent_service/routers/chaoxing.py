"""学习通抓取独立接口"""

from fastapi import APIRouter

from agent_service.tools.chaoxing import fetch_chaoxing_tasks

router = APIRouter(prefix="/chaoxing", tags=["学习通"])


@router.get("/tasks")
async def get_chaoxing_tasks():
    """获取学习通课程列表"""
    text = await fetch_chaoxing_tasks()
    return {"tasks_text": text}
