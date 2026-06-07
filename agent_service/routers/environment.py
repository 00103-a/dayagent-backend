from fastapi import APIRouter,Query
from agent_service.tools.influx_client import query_latest, query_recent
from agent_service.agents.sensor_analysis import analyze_environment

router = APIRouter(prefix = "/environment", tags=["环境"])

@router.get("/insights")
async def get_environment_insights(
    user_id: str = Query("1", description = "用户 ID")
):
    latest = query_latest()
    recent = query_recent(minutes = 60)
    ai_insights = await analyze_environment(recent)
    alerts = _check_alerts(latest)

    return {
        "current_readings": latest,
        "alerts": alerts,
        "ai_insights": ai_insights,
    }


def _check_alerts(latest: dict) -> list[dict]:
      """根据阈值生成即时告警，不依赖 LLM"""
      if not latest:
          return []
      alerts = []
      if latest.get("co2", 0) > 1500:
          alerts.append({"type": "co2_high", "message": "CO2偏高，建议开窗通风", "level": "warning"})
      if latest.get("temperature", 0) > 30:
          alerts.append({"type": "temp_high", "message": "温度偏高，注意防暑",
  "level": "warning"})
      if latest.get("humidity", 0) > 85:
          alerts.append({"type": "hum_high", "message": "湿度较高，感觉闷热",
  "level": "info"})
      if latest.get("pm25", 0) > 75:
        alerts.append({"type": "pm25_high", "message": "PM2.5偏高，减少开窗", "level": "warning"})
      return alerts