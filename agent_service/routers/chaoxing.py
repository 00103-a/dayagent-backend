"""学习通抓取独立接口"""

from fastapi import APIRouter

from agent_service.tools.chaoxing import fetch_chaoxing_tasks

router = APIRouter(prefix="/chaoxing", tags=["学习通"])


@router.get("/tasks")
async def get_chaoxing_tasks(
    username: str = Query("", description="学习通账号"),
    password: str = Query("", description="学习通密码"),
):
    """获取学习通课程列表"""
    text = await fetch_chaoxing_tasks(username=username, password=password)
    return {"tasks_text": text}
