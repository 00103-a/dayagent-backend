import os
from pathlib import Path
import httpx
from openai import AsyncOpenAI

_PROMPT_DIR = Path(__file__).parent.parent / "prompts"
def _load_prompt(filename: str) -> str:
    """加载prompt模板文件"""
    path = _PROMPT_DIR / filename
    if path.exists():
        return path.read_text(encoding = "utf-8")
    return ""

def _build_client() -> AsyncOpenAI:
    proxy = os.getenv("LLM_PROXY","")
    kwargs = {
        "api_key": os.getenv("DEEPSEEK_API_KEY", "sk-xxx"),
        "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        "http_client": httpx.AsyncClient(
              timeout=httpx.Timeout(60.0, connect=15.0),
              follow_redirects=True,
              trust_env=False,
          ),
    }
    if proxy:
        kwargs["http_client"].proxy = proxy
    return AsyncOpenAI(**kwargs)

async def analyze_environment(
        sensor_readings: list[dict],
        courses: list = None,
        goals: list = None
) -> str:
    if not sensor_readings:
        return "暂无环境数据，开启传感器后可获取实时分析。"
    latest = sensor_readings[-1]
    trend_text = ""
    if len(sensor_readings) >= 6:
        first = sensor_readings[0]
        temp_change = latest.get("temperature",0) - first.get("temperature",0)
        co2_change = latest.get("co2", 0) - first.get("co2", 0)
        if abs(temp_change) > 1:
            trend_text += f"温度{'上升' if temp_change > 0 else '下降'}了{abs(temp_change):.1f}°C。"
        if co2_change > 100:
              trend_text +=f"CO2持续上升（+{co2_change:.0f}ppm），房间可能通风不佳。"
    context = f"""当前环境数据：
    -温度：{latest.get('temperature')}°C
    - 湿度：{latest.get('humidity')}%
    - CO2：{latest.get('co2')}ppm
    - 光照：{latest.get('light')}lux
    - PM2.5：{latest.get('pm25')}μg/m³
    趋势：{trend_text if trend_text else "变化平稳"}"""

    if courses:
        context += f"\n 今日课程： {courses}"
    if goals:
        context += f"\n用户目标：{goals}"
    system_prompt = _load_prompt("sensor_prompt.txt")
    client = _build_client()
    try:
        response = await client.chat.completions.create(
            model = os.getenv("DEEPSEEK_MODEL","deepseek-chat"),
            messages=[
                {"role":"system","content":system_prompt},
                {"role":"user","content":context}
            ],
            temperature = 0.7,
            max_tokens = 200,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[LLM]分析失败:{e}")
        return _rule_based_advice(latest)

def _rule_based_advice(latest: dict) -> str:

    advice = []
    co2 = latest.get("co2", 0)
    temp = latest.get("temperature", 0)
    hum = latest.get("humidity", 0)

    if co2 and co2 > 1500:
          advice.append("CO2 偏高，建议开窗通风。")
    if temp and temp > 30:
          advice.append("温度偏高，注意防暑降温。")
    if hum and hum > 85:
          advice.append("湿度较高，室内可能有些闷。")

    return "\n".join(advice) if advice else "当前环境状况良好，安心工作吧。"