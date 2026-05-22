"""快递查询工具 - 快递100 API

实时查询快递物流状态，支持主流快递公司。
免费额度：个人注册每天 100 次免费查询，够个人使用。

API 文档：https://api.kuaidi100.com/document/5f0e2c2d77bc4b0061b8ca3b
"""

import hashlib
import json
import os
from typing import Any

import httpx

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

# 物流状态常量
STATE_MAP: dict[str, str] = {
    "0": "在途",
    "1": "揽件",
    "2": "疑难",
    "3": "签收",
    "4": "退签",
    "5": "派件",
    "6": "退回",
}

_KUAIDI100_API = "https://poll.kuaidi100.com/poll/query.do"


def _lookup_carrier_code(carrier: str) -> str | None:
    """将中文快递公司名转为快递100编码。

    优先从对照表查，其次尝试直接用小写英文码。
    """
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


def _build_sign(param_json: str, key: str, customer: str) -> str:
    """构建快递100签名：MD5(param + key + customer) 并转大写"""
    raw = param_json + key + customer
    return hashlib.md5(raw.encode("utf-8")).hexdigest().upper()


async def query_parcel(
    tracking_no: str,
    carrier: str,
    customer: str | None = None,
    key: str | None = None,
) -> dict[str, Any]:
    """查询单条快递物流状态。

    Args:
        tracking_no: 快递单号
        carrier: 快递公司名称（中文或编码）
        customer: 快递100 customer ID，不传则从环境变量 KUAIDI100_CUSTOMER 读取
        key: 快递100 API key，不传则从环境变量 KUAIDI100_KEY 读取

    Returns:
        {
            "tracking_no": "SF1234567890",
            "carrier": "顺丰",
            "state": "在途",          # 签收/在途/派件/揽件/疑难/退签/退回
            "state_code": "0",
            "is_delivered": false,
            "latest_context": "...",  # 最新一条物流信息
            "latest_time": "...",     # 最新一条时间
            "details": [...]          # 完整物流轨迹（最多保留最近10条）
        }
    """
    customer = customer or os.getenv("KUAIDI100_CUSTOMER", "")
    key = key or os.getenv("KUAIDI100_KEY", "")

    result: dict[str, Any] = {
        "tracking_no": tracking_no,
        "carrier": carrier,
        "state": "查询失败",
        "state_code": "",
        "is_delivered": False,
        "latest_context": "",
        "latest_time": "",
        "details": [],
    }

    com = _lookup_carrier_code(carrier)
    if not com:
        result["state"] = f"不支持的快递公司：{carrier}"
        return result

    if not customer or not key:
        result["state"] = "快递100 API 未配置（缺少 KUAIDI100_CUSTOMER / KUAIDI100_KEY）"
        return result

    param_data = {"com": com, "num": tracking_no}
    param_json = json.dumps(param_data, ensure_ascii=False, separators=(",", ":"))
    sign = _build_sign(param_json, key, customer)

    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            resp = await client.post(
                _KUAIDI100_API,
                data={
                    "customer": customer,
                    "sign": sign,
                    "param": param_json,
                },
                timeout=10.0,
            )
            if resp.status_code != 200:
                result["state"] = f"快递100 API 请求失败（HTTP {resp.status_code}）"
                return result
            resp.raise_for_status()
        except httpx.TimeoutException:
            result["state"] = "快递100 API 超时"
            return result
        except Exception as e:
            result["state"] = f"快递100 API 请求异常：{e}"
            return result

    try:
        data = resp.json()
    except Exception:
        result["state"] = "快递100 返回数据解析失败"
        return result

    # 快递100 返回格式：{"message": "ok", "state": "0", "data": [...]}
    api_state = data.get("state", "")
    result["state"] = STATE_MAP.get(api_state, f"未知状态({api_state})")
    result["state_code"] = api_state
    result["is_delivered"] = (api_state == "3")

    details: list[dict[str, str]] = data.get("data", [])
    if details:
        # 只保留最近10条轨迹，倒序展示（最新的在前）
        result["details"] = details[:10]
        latest = details[0]
        result["latest_context"] = latest.get("context", "")
        result["latest_time"] = latest.get("time", "") or latest.get("ftime", "")

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
