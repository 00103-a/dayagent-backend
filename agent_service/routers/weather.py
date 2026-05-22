"""天气查询独立接口"""

from fastapi import APIRouter, Query

from agent_service.tools.weather import fetch_weather

router = APIRouter(prefix="/weather", tags=["天气"])


@router.get("")
async def get_weather(
    location: str = Query("北京", description="城市名称"),
    lat: float | None = Query(None, description="纬度"),
    lng: float | None = Query(None, description="经度"),
):
    """查询城市当日天气（支持城市名或经纬度定位）

    Returns:
        location: 城市名
        weather: 格式化天气展示文本
        condition_text: 和风天气实时天气状况文字（晴/多云/阴/雨/雪等）
        condition_icon: 和风天气实时天气图标代码
    """
    result = await fetch_weather(location, lat=lat, lng=lng)
    return {
        "location": location,
        "weather": result["weather"],
        "condition_text": result["condition_text"],
        "condition_icon": result["condition_icon"],
    }
