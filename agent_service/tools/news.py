"""热榜新闻模块 - uapis.cn 免费 API

  API 
  文档：https://uapis.cn/docs/api-reference/get-misc-hotboard-query
"""
from agent_service.tools.base import Tool, ToolResult
import asyncio
from typing import Any                              

import httpx

HOTBOARD_API = "https://uapis.cn/api/v1/misc/hotboard"
_DEFAULT_TYPES = ["weibo", "zhihu", "baidu", "bilibili"]

async def query_hotboard(hotboard_type: str) -> list[dict[str, str]]:
    params = {"type": hotboard_type}
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            resp = await client.get(HOTBOARD_API, params=params,timeout=10.0)
            if resp.status_code != 200:
                  print(f"[Hotboard] {hotboard_type} 请求失败 HTTP{resp.status_code}")
                  return []
        except httpx.TimeoutException:
             print(f"[Hotboard] {hotboard_type} 超时")
             return []
        except Exception as e:
             print(f"[Hotboard] {hotboard_type} 异常: {e}")
             return []
    try:
         data = resp.json()
    except Exception:
         return []
    items = data.get("list", [])
    result: list[dict[str, str]] = []
    for item in items[:5]:
          result.append({
              "title": item.get("title", ""),
              "hot_value": str(item.get("hot_value", "")),
              "url": item.get("url", ""),
              "source": hotboard_type,
              "abstract": item.get("extra", {}).get("abstract", ""),
          })
    return result

async def get_personalized_news(
    goals: list[str],
    yesterday_summary: str,
    llm_key: str = "",
    llm_base_url: str = "",
    llm_model: str = "",
    news_api_key: str = "",
  ) -> str:
    """拉多平台热榜，返回格式化文本。"""
    results = await asyncio.gather(*(query_hotboard(t) for t in _DEFAULT_TYPES))
    all_items: list[dict[str, str]] = []
    for items in results:
         all_items.extend(items)
    if not all_items:
          return "暂无热榜数据"
    
    lines: list[str] = []
    source_names = {"weibo": "微博", "zhihu": "知乎", "baidu": "百度","bilibili": "B站"}
    for source in _DEFAULT_TYPES:
        items = [i for i in all_items if i["source"] == source][:5]
        if not items:
            continue  
        lines.append(f"\n【{source_names.get(source, source)}】")
        for idx, item in enumerate(items, 1):
              hot = item["hot_value"]
              hot_str = f"（热度: {hot}）" if hot else ""
              lines.append(f"  {idx}. {item['title']} {hot_str}")

    return "\n".join(lines) if lines else "暂无热榜数据"
  
class NewsTool(Tool):
      name = "news"
      description = "查询各平台实时热榜，了解当前网络热点"

      async def run(self, params: dict) -> ToolResult:
          goals = params.get("goals", [])
          try:
              text = await get_personalized_news(goals, "")
              return ToolResult(ok=True, data={"text": text})
          except Exception as e:
              return ToolResult(ok=False, data={}, error=f"热榜查询失败: {e}")
       