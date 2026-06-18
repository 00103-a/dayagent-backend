"""快递查询工具 - uapis.cn 免费 API

API 文档：https://uapis.cn/docs/api-reference/get-misc-tracking-query
"""


import os
from typing import Any
import re
import httpx

_WAITING_PICKUP_PATTERNS = [
      r"已到达.*(?:驿站|网点|代收点|服务站|菜鸟)",
      r"已到.*(?:驿站|网点|代收点)",                
      r"待领取",
      r"取件码",
      r"请.*取件",
      r"凭.*取件",
      r"快递柜",
      r"丰巢",
      r"自提柜",
      r"存入.*柜",
      r"妈妈驿站",
      r"兔喜",
      r"快递超市",
      r"摩西管家",
      r"邻里驿站",
      r"熊猫快收",
      r"乐收",
]

# 快递公司中文名 → 快递100编码 对照表
_CARRIER_CODE_MAP: dict[str, str] = {
    "顺丰": "shunfeng",
    "顺丰速运": "shunfeng",
    "圆通": "yuantong",
    "圆通速递": "yuantong",
    "中通": "zhongtong",
    "中通快递": "zhongtong",
    "申通": "shentong",
    "申通快递": "shentong",
    "韵达": "yunda",
    "韵达快递": "yunda",
    "京东": "jd",
    "京东物流": "jd",
    "EMS": "ems",
    "邮政": "ems",
    "中国邮政": "ems",
    "极兔": "jtexpress",
    "极兔速递": "jtexpress",
    "德邦": "debangwuliu",
    "德邦快递": "debangwuliu",
    "百世": "baishiwuliu",
    "百世快递": "baishiwuliu",
    "丹鸟": "danniao",
    "菜鸟": "cainiao",
    "丰网": "fengwang",
    "宅急送": "zhaijisong",
    "优速": "youshuwuliu",
    "天天": "tiantian",
    "天天快递": "tiantian",
}

_TRACKING_API = "https://uapis.cn/api/v1/misc/tracking/query"

def  _check_waiting_pickup(tracks:list[dict]) -> bool:
     """从物流轨迹判断是否已到站但未取"""
     for track in tracks[:3]:
        text = track.get("context","")
        for pattern in _WAITING_PICKUP_PATTERNS:
            if re.search(pattern,text):
                return True
     return False


def _lookup_carrier_code(carrier: str) -> str | None:

    if not carrier:
        return None
    # 精确匹配
    if carrier in _CARRIER_CODE_MAP:
        return _CARRIER_CODE_MAP[carrier]
    # 模糊匹配（用户可能填"顺丰快递"但表里只有"顺丰"）
    for name, code in _CARRIER_CODE_MAP.items():
        if carrier in name or name in carrier:
            return code
    # 如果已经是英文编码，直接使用
    if carrier.isascii() and carrier.islower():
        return carrier
    return None


#提取函数

def _extract_pickup_code(tracks: list[dict]) -> str:
    for track in tracks[:3]:
        text = track.get("context", "")
        m = re.search(r"取件码[：:为]?\s*([A-Za-z0-9\-]{4,12})","text")
        if m:
            return text
        return ""



async def query_parcel(
    tracking_no: str,
    carrier: str,
) -> dict[str, Any]:
    """查询单条快递物流状态（uapis.cn 免费 API）。"""

    result: dict[str, Any] = {
        "tracking_no": tracking_no,
        "carrier": carrier,
        "state": "查询失败",
        "state_code": "",
        "pickup_code": "",
        "is_delivered": False,
        "latest_context": "",
        "latest_time": "",
        "details": [],
        "is_waiting_pickup": False
    }

    params: dict[str,str] = {"tracking_number":tracking_no}
    com = _lookup_carrier_code(carrier)

    if com:
        params["carrier_code"] = com

    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            resp = await client.get(
                _TRACKING_API,
                params=params,
                timeout=10.0,
            )
            if resp.status_code == 400:
                result["state"] = "参数错误"
                return result
            if resp.status_code == 404:
                result["state"] = "暂无物流信息"
                return result
            if resp.status_code != 200:
                result["state"] = f"API 请求失败(HTTP {resp.status_code})"
                return result
        except httpx.TimeoutException:
            result["state"] = " API 超时"
            return result
        except Exception as e:
            result["state"] = f" API 请求异常：{e}"
            return result

    try:
        data = resp.json()
    except Exception:
        result["state"] = " 返回数据解析失败"
        return result

    result["state"] = data.get("status","未知")
    result["state_code"] = data.get("status_code","")
    result["is_delivered"] = data.get("is_completed",False)
    if not result["carrier"]:
        result["carrier"] = data.get("carrier_name","")

    tracks: list[dict[str, str]] = data.get("tracks", [])
    if tracks:
        # 只保留最近10条轨迹，倒序展示（最新的在前）
        result["details"] = tracks[:10]
        latest = tracks[0]
        result["latest_context"] = latest.get("context", "")
        result["latest_time"] = latest.get("time", "") 
    if _check_waiting_pickup(tracks) and not result["is_delivered"]:
        result["state"] = "待取件" + "（" + result["state"] + "）"
        result["is_waiting_pickup"] = True
        result["pickup_code"] = _extract_pickup_code(tracks=tracks)
    

    return result


async def query_parcels_batch(
    parcels: list[dict[str, str]],
    pre_queried: list[dict[str, Any]] | None = None,
) -> str:
    """批量查询快递状态，返回汇总文本。

    Args:
        parcels: 来自 Java 的快递列表，每项为
            {"tracking_no": "xxx", "carrier": "顺丰", "remark": "耳机"}
        pre_queried: 已经查好的详细结果，传了就不重复调 API

    Returns:
        快递状态汇总文本，可直接嵌入 LLM prompt
    """
    if not parcels:
        return "暂无待查询的快递"

    if pre_queried is not None:
        results = pre_queried
    else:
        results = await query_parcels_detailed(parcels)

    lines: list[str] = []
    for r in results:
        remark = r.get("remark", "")
        label = f"[{remark}] " if remark else ""
        tracking_no = r["tracking_no"]
        carrier = r["carrier"]          # 用查询结果里的 carrier（与输入一致）
        state = r["state"]

        line = f"- {label}{carrier} {tracking_no}：{state}"
        if r["latest_context"] and r["state"] not in ("查询失败", "不支持的快递公司"):
            line += f"（{r['latest_context']}）"
        if r["latest_time"]:
            line += f" [{r['latest_time']}]"
        lines.append(line)

    return "\n".join(lines) if lines else "暂无待查询的快递"


async def query_parcels_detailed(
    parcels: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """批量查询快递状态，返回结构化数据。

    供 router 层使用，方便把更新后的状态传回 Java 端更新数据库。
    """
    results: list[dict[str, Any]] = []
    for p in parcels:
        tracking_no = p.get("tracking_no", "")
        carrier = p.get("carrier", "")
        if not tracking_no:
            continue
        r = await query_parcel(tracking_no, carrier)
        r["remark"] = p.get("remark", "")
        results.append(r)
    return results
from agent_service.tools.base import Tool,ToolResult

class ParcelTool(Tool):
    name="parcel"
    description="查询当前快递状态"

    async def run(self,params:dict) -> ToolResult:
        parcels = params.get("parcels",[])
        if not parcels:
            return ToolResult(
                ok=True,
                data={
                    "summary": "",
                    "statuses": [],
                },
            )
        try:
            detailed = await query_parcels_detailed(parcels)
            summary = await query_parcels_batch(parcels, detailed) 
            return ToolResult(ok = True, 
                data={
                "summary": summary,
                "statuses": detailed,
            })
        except Exception as e:
            return ToolResult(ok = False, data = {
                "summary": "",
                "statuses": [],
            },
            error = f"查询失败: {e}" 
            )
        
        
        

