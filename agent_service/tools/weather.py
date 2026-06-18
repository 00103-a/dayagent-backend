import os
import logging
import httpx

logger = logging.getLogger(__name__)

# 常见城市 → 和风天气 Location ID 对照表
# 来源: https://github.com/qwd/LocationList
_CITY_ID_MAP = {
    "北京": "101010100",
    "上海": "101020100",
    "广州": "101280101",
    "深圳": "101280601",
    "杭州": "101210101",
    "南京": "101190101",
    "武汉": "101200101",
    "成都": "101270101",
    "重庆": "101040100",
    "西安": "101110101",
    "天津": "101030100",
    "苏州": "101190401",
    "长沙": "101250101",
    "合肥": "101220101",
    "郑州": "101180101",
    "济南": "101120101",
    "青岛": "101120201",
    "厦门": "101230201",
    "福州": "101230101",
    "大连": "101070201",
    "南昌": "101240101",
    "昆明": "101290101",
    "南宁": "101300101",
    "贵阳": "101260101",
    "兰州": "101160101",
    "沈阳": "101070101",
    "哈尔滨": "101050101",
    "石家庄": "101090101",
    "太原": "101100101",
    "呼和浩特": "101080101",
    "乌鲁木齐": "101130101",
    "拉萨": "101140101",
    "西宁": "101150101",
    "银川": "101170101",
    "海口": "101310101",
}


def _normalize_host(host: str) -> str:
    """确保 host 带有 https:// 协议前缀"""
    if host and not host.startswith("http"):
        return "https://" + host
    return host


async def fetch_weather(
    location: str, lat: float | None = None, lng: float | None = None,
    api_key: str = "",
    weather_host: str = "",
) -> dict:
    """获取城市当日天气。数据源：和风天气 Web API

    支持城市名称或经纬度定位。有坐标时优先用坐标反查城市 ID。
    返回 dict: {weather, condition_text, condition_icon}
      - weather: 格式化展示文本
      - condition_text: 和风天气实时天气文字（晴/多云/阴/雨/雪等）
      - condition_icon: 和风天气实时天气图标代码
    """
    api_key = api_key or os.getenv("WEATHER_API_KEY", "")
    print(f"[weather] api_key received: '{api_key[:8]}...' (len={len(api_key)})" if api_key else "[weather] api_key is EMPTY")
    if not api_key:
        return {
            "weather": "天气 API Key 未配置（请在 App 设置中填写 Weather API Key）",
            "condition_text": "",
            "condition_icon": "",
        }

    host = _normalize_host(weather_host or os.getenv("WEATHER_API_HOST", "https://api.qweather.com"))
    geo_host = _normalize_host(os.getenv("GEO_API_HOST", host))

    async with httpx.AsyncClient(trust_env=False) as client:
        # 有经纬度时，组装 "lng,lat" 格式传给 Geo API 反查城市
        lookup_value = f"{lng},{lat}" if (lat is not None and lng is not None) else location

        # Step 1: 拿到城市 ID 和显示名
        city_id, display_name = await _lookup_city_id(
            client, api_key, geo_host, lookup_value
        )
        if not city_id:
            return {
                "weather": f"{location}：未找到该城市的天气 ID",
                "condition_text": "",
                "condition_icon": "",
            }

        # Step 2: 查询实时天气
        result = await _fetch_weather_now(client, api_key, host, city_id)
        if result is None:
            return {
                "weather": f"{display_name}：天气数据获取失败",
                "condition_text": "",
                "condition_icon": "",
            }

        weather_text, condition_text, condition_icon = result
        return {
            "weather": f"{display_name}今日天气：{weather_text}",
            "condition_text": condition_text,
            "condition_icon": condition_icon,
        }


async def _lookup_city_id(
    client: httpx.AsyncClient, api_key: str, geo_host: str, location: str
) -> tuple[str | None, str]:
    """通过和风天气 GeoAPI 查城市 ID 和显示名；先查本地表再调 API

    Returns:
        (city_id, display_name) — city_id 为 None 表示未找到，display_name 用于展示
    """
    # 先试本地表（快，不消耗 API 额度）
    for name, cid in _CITY_ID_MAP.items():
        if location in name or name in location:
            return cid, name

    # 本地没有，调 Geo API
    # 路径说明：geoapi.qweather.com 用 /v2/city/lookup，
    # api.qweather.com / 自定义域名用 /geo/v2/city/lookup
    if "geoapi.qweather.com" in geo_host:
        url = f"{geo_host}/v2/city/lookup"
    else:
        url = f"{geo_host}/geo/v2/city/lookup"
    try:
        resp = await client.get(
            url,
            params={"location": location, "key": api_key},
            timeout=5.0,
        )
        if resp.status_code == 200:
            data = resp.json()
            locations = data.get("location")
            if locations:
                loc = locations[0]
                city_id = loc["id"]
                # 优先用 district（区县级），其次 name（城市级）
                display = loc.get("district") or loc.get("name") or location
                logger.info(f"GeoAPI 查到 {location} -> {city_id} ({display})")
                return city_id, display
            logger.warning(f"GeoAPI 未找到城市: {location}, resp={data}")
        else:
            logger.warning(f"GeoAPI 返回非 200: {resp.status_code}, url={url}")
    except Exception as e:
        logger.error(f"GeoAPI 调用失败: {url}, error={e}")

    return None, location


async def _fetch_weather_now(
    client: httpx.AsyncClient, api_key: str, weather_host: str, city_id: str
) -> tuple[str, str, str] | None:
    """调用和风天气实时天气接口

    Returns:
        (formatted_text, condition_text, condition_icon) 或 None
        - formatted_text: "晴，温度 25°C，体感温度 26°C，北风 2 级，相对湿度 65%"
        - condition_text: 和风天气实时天气文字，如 "晴"、"多云"、"小雨"
        - condition_icon: 和风天气实时天气图标代码，如 "100"
    """
    url = f"{weather_host}/v7/weather/now"
    try:
        resp = await client.get(
            url,
            params={"location": city_id, "key": api_key},
            timeout=5.0,
        )
        if resp.status_code != 200:
            logger.warning(f"Weather API 返回非 200: {resp.status_code}, url={url}")
            return None

        now = resp.json()["now"]
        condition_text = now["text"]
        condition_icon = now["icon"]
        formatted = (
            f"{condition_text}，"
            f"温度 {now['temp']}°C，"
            f"体感温度 {now['feelsLike']}°C，"
            f"{now['windDir']} {now['windScale']} 级，"
            f"相对湿度 {now['humidity']}%"
        )
        return formatted, condition_text, condition_icon
    except Exception as e:
        logger.error(f"Weather API 调用失败: {url}, error={e}")
        return None


# ============================================================
# 新外壳：把上面的逻辑包装成"统一接口工具"
# ============================================================
# 阅读顺序：先看下面 6 行，理解 WeatherTool 长什么样；
#          再回来看它如何复用前面的 fetch_weather。
# ============================================================

from typing import Optional

# 从同目录的 base.py 里拿"操作手册"（Tool 模板 + ToolResult 形状）。
from agent_service.tools.base import Tool, ToolResult


class WeatherTool(Tool):
    """天气工具，遵守 base.py 里的 Tool 契约。

    它的"干活逻辑"全部复用前面已经写好的 fetch_weather 函数，
    这个类只负责：把外部传进来的统一参数（params dict）翻译成
    fetch_weather 需要的参数，再把 fetch_weather 的返回包装成 ToolResult。

    类比：fetch_weather 是一个熟练工，懂怎么查天气；
         WeatherTool 是他的工服和工牌，让他符合公司规范，
         别人（工作流/LLM）一眼就能认出他、按统一方式指挥他。
    """

    # ---- 自我介绍（为以后 agent 化埋的种子）----
    name = "weather"
    description = "查询某城市的实时天气，包括温度、风力、天气状况等。"

    # ---- 干活的那个动作（契约要求叫 run，参数要求是 dict）----
    async def run(self, params: dict) -> ToolResult:
        """params 里期待这些 key（缺了会用默认值兜底）：
            - location  : 城市名，如 "南昌"        （必需）
            - lat       : 经度，可选
            - lng       : 纬度，可选
            - api_key   : 和风天气 API Key，可选（缺时走环境变量）
            - host      : API host，可选
        """

        # ---- Step 1: 从 params 这个 dict 里"取"参数 ----
        # params.get(key, default) 的含义：
        #   如果 params 里有这个 key，就取它的值；没有就用 default。
        # 这比位置参数健壮——调用方忘了传 api_key 也不会报错，只是走环境变量。
        location = params.get("location", "")
        lat: Optional[float] = params.get("lat")
        lng: Optional[float] = params.get("lng")
        api_key: str = params.get("api_key", "")
        weather_host: str = params.get("host", "")

        # ---- Step 2: 调用原有逻辑（一行没动）----
        # 这里直接复用前面定义的 fetch_weather 函数。
        # 这就是"外壳"的含义——它自己不干活，它负责把活派给会干的人。
        try:
            raw = await fetch_weather(
                location=location,
                lat=lat,
                lng=lng,
                api_key=api_key,
                weather_host=weather_host,
            )
        except Exception as e:
            # ---- 异常也统一包装：绝不让一个工具的崩溃拖垮整个工作流 ----
            # WHY 这样做：以前 fetch_weather 出错会直接抛异常，
            # 上层（routers/plan.py 的 gather）一旦有一个工具炸了，整个 gather 就炸了。
            # 包装成 ToolResult(ok=False, error=...) 后，上层可以选择"跳过这个工具继续跑"。
            return ToolResult(ok=False, data={}, error=f"天气查询异常: {e}")

        # ---- Step 3: 把原始返回包装成统一的 ToolResult ----
        # fetch_weather 成功时返回 dict，失败时也返回 dict（但 condition_text 为空）。
        # 我们用 condition_text 是否为空，作为"真正成功"的判断依据。
        is_ok = bool(raw.get("condition_text"))
        return ToolResult(
            ok=is_ok,
            data=raw,
            error="" if is_ok else "天气数据为空或未配置 API Key",
        )
