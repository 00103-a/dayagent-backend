"""
个性化新闻模块

流程：
1. 从用户目标和近期总结中提取关键词
2. 拉取当日新闻（数据源待定，接口预留）
3. 调用 LLM 根据关键词筛选 3~5 条相关新闻
4. 返回筛选结果，融合进 /generate-plan

返回格式：[{"title": "", "summary": "", "url": ""}]
"""

import asyncio
import os
from typing import Any

import httpx
from openai import AsyncOpenAI


# ── 新闻数据源配置 ────────────────────────────────────────────────────────────────
_NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
# 支持多源：用逗号分隔，如 "guonei/index,guoji/index"
# 每个 URL 会并行拉取，结果合并后统一筛选
_NEWS_API_URLS = [u.strip() for u in os.getenv("NEWS_API_URL", "").split(",") if u.strip()]

# 每个数据源拉取条数（合并后会去重+LLM筛选，最终只展示3~5条）
_PER_SOURCE_NUM = 20


async def _fetch_single_source(url: str, source_label: str) -> list[dict[str, str]]:
    """从单个新闻源拉取数据"""
    import json as _json

    params: dict[str, object] = {"key": _NEWS_API_KEY, "num": _PER_SOURCE_NUM}

    extra_params_str = os.getenv("NEWS_API_PARAMS", "")
    if extra_params_str:
        try:
            extra = _json.loads(extra_params_str)
            params.update(extra)
        except _json.JSONDecodeError:
            pass

    try:
        async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                print(f"[News] {source_label} 返回非 200: {resp.status_code}")
                return []
            data = resp.json()
            if data.get("code") != 200:
                print(f"[News] {source_label} API 错误: code={data.get('code')}, msg={data.get('msg', '')}")
                return []
            items = _parse_news_response(data)
            # 标记来源
            for item in items:
                item["source"] = source_label
            print(f"[News] {source_label}: 拉到 {len(items)} 条")
            return items
    except Exception as e:
        print(f"[News] {source_label} 拉取异常: {e}")
        return []


async def fetch_raw_news() -> list[dict[str, str]]:
    """
    从所有配置的新闻源并行拉取新闻，合并后去重返回。

    NEWS_API_URL 支持逗号分隔的多源：
      https://apis.tianapi.com/guonei/index,https://apis.tianapi.com/guoji/index

    返回 [{"title": "", "summary": "", "url": "", "ctime": "", "source": ""}, ...]
    """
    if not _NEWS_API_KEY or not _NEWS_API_URLS:
        return []

    # 并行拉取所有数据源
    tasks = []
    for url in _NEWS_API_URLS:
        # 从 URL 提取来源名（如 "guonei"、"guoji"）
        label = url.rstrip("/").split("/")[-2] if "/index" in url else url.split("/")[-1]
        tasks.append(_fetch_single_source(url, label))

    results = await asyncio.gather(*tasks)

    # 合并 + URL 去重
    seen_urls: set[str] = set()
    merged: list[dict[str, str]] = []
    for items in results:
        for item in items:
            url = item.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                merged.append(item)
            elif not url:
                merged.append(item)

    print(f"[News] 合并后共 {len(merged)} 条（去重前 {sum(len(r) for r in results)} 条）")
    return merged


def _parse_news_response(data: dict[str, Any]) -> list[dict[str, str]]:
    """
    解析各新闻 API 的返回结构，统一为 [{"title": "", "summary": "", "url": ""}]。

    支持结构：
      - {"newslist": [...]}                  — 顶层直接列表
      - {"result": {"newslist": [...]}}  — 天行数据嵌套结构
      - {"data": [...]} / {"data": {"list": [...]}}  — 聚合数据等
    """
    def _extract_items(container: dict[str, Any]) -> list[dict[str, Any]] | None:
        """从容器中提取新闻条目列表"""
        # 直接查常见列表键
        for list_key in ("newslist", "articles", "news", "list"):
            items = container.get(list_key)
            if isinstance(items, list) and items:
                return items  # type: ignore[return-value]
        return None

    # 先查顶层是否有直接列表
    for key in ("newslist", "result", "data", "articles", "news"):
        val = data.get(key)
        if val is None:
            continue
        # 值是列表 → 直接使用
        if isinstance(val, list):
            items = val
        # 值是字典 → 深入查找嵌套列表（天行数据返回 {"result": {"newslist": [...]}}）
        elif isinstance(val, dict):
            items = _extract_items(val)
            if items is None:
                continue
        else:
            continue

        if items:
            parsed = []
            for item in items[:30]:
                if isinstance(item, dict):
                    parsed.append({
                        "title": str(item.get("title", item.get("name", ""))).strip(),
                        "summary": str(item.get("description", item.get("summary", item.get("digest", "")))).strip(),
                        "url": str(item.get("url", item.get("link", item.get("href", "")))).strip(),
                        "ctime": str(item.get("ctime", item.get("pubDate", item.get("time", "")))).strip(),
                    })
            return [p for p in parsed if p["title"]]

    return []


# ── 关键词提取 ────────────────────────────────────────────────────────────────────


def extract_keywords_basic(goals: list[str], yesterday_summary: str) -> list[str]:
    """
    从目标列表和昨日总结中简单提取关键词（不依赖 LLM 的快速方案）。

    规则：
    1. 从 goals 中提取名词/动词短语（按顿号、空格、逗号拆分）
    2. 从 yesterday_summary 中按同样规则提取
    3. 去重并返回
    """
    import re

    raw: list[str] = []
    for text in goals:
        # 去掉括号内容（如"每天刷2道LeetCode（算法保持）" → "每天刷2道LeetCode"）
        text = re.sub(r"[（(][^)）]*[)）]", "", text)
        # 提取中文/英文关键词段
        parts = re.split(r"[，,、\s]+", text)
        raw.extend(p for p in parts if len(p) >= 2)

    if yesterday_summary:
        # 从总结中提取可能的主题词（2-8个汉字或2-20个英文单词）
        cleaned = re.sub(r"[（(][^)）]*[)）]", "", yesterday_summary)
        parts = re.split(r"[，,。；;、\s]+", cleaned)
        raw.extend(p for p in parts if 2 <= len(p) <= 20)

    # 去重并过滤通用词
    seen: set[str] = set()
    keywords: list[str] = []
    stop_words = {"的", "了", "和", "是", "在", "不", "也", "都", "要", "有", "我",
                  "今天", "昨天", "然后", "一个", "这个", "那个", "一下", "一点",
                  "完成", "做了", "搞了", "弄了", "感觉", "觉得", "比较", "没有"}
    for kw in raw:
        kw = kw.strip()
        if kw and kw not in stop_words and kw not in seen:
            seen.add(kw)
            keywords.append(kw)

    return keywords[:10]  # 最多 10 个关键词


async def extract_keywords_llm(
    goals: list[str],
    yesterday_summary: str,
) -> list[str]:
    """
    用 LLM 从目标和总结中提取 3~8 个核心关键词。
    优先使用此方案以获得更精准的关键词，API Key 未配时降级到 basic 方案。
    """
    if not goals and not yesterday_summary:
        return _default_keywords()

    goals_text = "\n".join(f"- {g}" for g in goals) if goals else "暂无"
    user_msg = f"""用户当前目标：
{goals_text}

用户昨日总结：
{yesterday_summary or "暂无"}

请从以上内容中提取 3~8 个核心关键词（如"算法"、"前端"、"考研复试"、"Java"等）。
关键词应当是用户关心的领域、技术栈、考试或主题。
只返回关键词列表，每行一个，不要编号，不要解释。"""

    llm_key = os.getenv("LLM_API_KEY", "")
    if not llm_key or llm_key == "sk-placeholder":
        return extract_keywords_basic(goals, yesterday_summary)

    try:
        proxy = os.getenv("LLM_PROXY", "")
        kwargs: dict = {"timeout": httpx.Timeout(30.0, connect=10.0), "trust_env": False}
        if proxy:
            kwargs["proxy"] = proxy
            kwargs["verify"] = False
        http_client = httpx.AsyncClient(**kwargs)

        ai_client = AsyncOpenAI(
            base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
            api_key=llm_key,
            http_client=http_client,
        )

        model = os.getenv("LLM_MODEL", "deepseek-chat")
        resp = await ai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个关键词提取助手。只返回关键词列表。"},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=200,
        )

        await http_client.aclose()

        content = resp.choices[0].message.content or ""
        keywords = [line.strip("-•· 1234567890.、") for line in content.strip().split("\n")]
        keywords = [kw.strip() for kw in keywords if kw.strip()]
        return keywords[:8] if keywords else _default_keywords()

    except Exception as e:
        proxy = os.getenv("LLM_PROXY", "")
        hint = ""
        if proxy and "connect" in str(e).lower():
            hint = f"（代理 {proxy} 不可达，请检查代理是否启动，或在 .env 中清空 LLM_PROXY 走直连）"
        elif "connect" in str(e).lower():
            hint = "（网络不通，可尝试在 .env 中设置 LLM_PROXY 代理）"
        print(f"[News] LLM 关键词提取失败，降级到 basic: {type(e).__name__}: {e}{hint}")
        return extract_keywords_basic(goals, yesterday_summary)


def _default_keywords() -> list[str]:
    return ["科技", "校园", "考试"]


# ── 个性化新闻筛选 ────────────────────────────────────────────────────────────────


async def filter_news_by_llm(
    raw_news: list[dict[str, str]],
    keywords: list[str],
    max_pick: int = 5,
) -> list[dict[str, str]]:
    """
    调用 LLM 根据关键词从原始新闻中筛选出最相关的。

    Args:
        raw_news: 原始新闻列表
        keywords: 关键词列表
        max_pick: 最多选取条数（默认 5）

    Returns:
        筛选后的新闻列表，按相关度排序
    """
    if not raw_news:
        return []

    llm_key = os.getenv("LLM_API_KEY", "")
    if not llm_key or llm_key == "sk-placeholder":
        return raw_news[:max_pick]

    # 构建新闻索引供 LLM 筛选
    news_index = ""
    for i, item in enumerate(raw_news):
        title = item.get("title", "")
        summary = item.get("summary", "")[:100]
        news_index += f"[{i}] {title}\n"
        if summary:
            news_index += f"    摘要: {summary}\n"
        news_index += "\n"

    keywords_str = "、".join(keywords)

    try:
        proxy = os.getenv("LLM_PROXY", "")
        kwargs: dict = {"timeout": httpx.Timeout(45.0, connect=10.0), "trust_env": False}
        if proxy:
            kwargs["proxy"] = proxy
            kwargs["verify"] = False
        http_client = httpx.AsyncClient(**kwargs)

        ai_client = AsyncOpenAI(
            base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
            api_key=llm_key,
            http_client=http_client,
        )

        model = os.getenv("LLM_MODEL", "deepseek-chat")
        resp = await ai_client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一个个性化新闻筛选助手。用户关心这些关键词：" + keywords_str + "\n"
                        f"请从新闻列表中选择 {max_pick} 条与用户最相关的。\n"
                        "只返回选中新闻的索引编号，每行一个，不要其他内容。\n"
                        "例如：\n0\n3\n7"
                    ),
                },
                {"role": "user", "content": news_index},
            ],
            temperature=0.2,
            max_tokens=100,
        )

        await http_client.aclose()

        content = resp.choices[0].message.content or ""
        # 解析 LLM 返回的索引
        import re
        indices: list[int] = []
        for line in content.strip().split("\n"):
            match = re.search(r"\b(\d+)\b", line)
            if match:
                idx = int(match.group(1))
                if 0 <= idx < len(raw_news):
                    indices.append(idx)

        if not indices:
            return raw_news[:max_pick]

        # 按 LLM 返回的顺序取结果（去重保序）
        seen: set[int] = set()
        result: list[dict[str, str]] = []
        for idx in indices:
            if idx not in seen and len(result) < max_pick:
                seen.add(idx)
                result.append(raw_news[idx])
        return result

    except Exception as e:
        proxy = os.getenv("LLM_PROXY", "")
        hint = ""
        if proxy and "connect" in str(e).lower():
            hint = f"（代理 {proxy} 不可达）"
        elif "connect" in str(e).lower():
            hint = "（网络不通）"
        print(f"[News] LLM 筛选失败，返回前 3 条: {type(e).__name__}: {e}{hint}")
        return raw_news[:max_pick]


# ── 对外主函数 ────────────────────────────────────────────────────────────────────


async def get_personalized_news(
    goals: list[str],
    yesterday_summary: str,
) -> str:
    """
    对外主函数：获取个性化新闻，返回格式化的自然语言文本。

    流程：
    1. 从 goals + summary 提取关键词
    2. 拉取原始新闻
    3. LLM 筛选 3~5 条相关新闻
    4. 格式化为文本

    Returns:
        格式化的新闻文本，直接嵌入规划 prompt。无新闻时返回空字符串。
    """
    # Step 1: 提取关键词
    keywords = await extract_keywords_llm(goals, yesterday_summary)
    if not keywords:
        keywords = _default_keywords()

    # Step 2: 拉取原始新闻
    raw_news = await fetch_raw_news()

    if not raw_news:
        return ""

    # Step 3: 按来源分组，独立筛选（确保每个来源都有新闻入选）
    source_groups: dict[str, list[dict[str, str]]] = {}
    for item in raw_news:
        src = item.get("source", "other")
        source_groups.setdefault(src, []).append(item)

    # 每个来源筛 2~3 条，只有一个来源时筛 3~5 条
    per_source = 2 if len(source_groups) > 1 else 5
    all_selected: list[dict[str, str]] = []
    for src, items in source_groups.items():
        picked = await filter_news_by_llm(items, keywords, max_pick=per_source)
        all_selected.extend(picked)

    if not all_selected:
        return ""

    # Step 4: 格式化
    source_labels = {
        "guonei": "国内", "world": "国际", "social": "社会",
        "keji": "科技", "tiyu": "体育", "toutiao": "头条",
    }

    lines = []
    for item in all_selected:
        title = item["title"]
        tag = source_labels.get(item.get("source", ""), item.get("source", ""))
        prefix = f"[{tag}] " if tag else ""
        summary = item.get("summary", "")
        skip_summaries = {"查看详情", "查看原文", "阅读全文", "阅读全文>", "点击查看", ""}
        if summary in skip_summaries:
            summary = ""
        if summary:
            lines.append(f"· {prefix}{title} — {summary[:60]}")
        else:
            lines.append(f"· {prefix}{title}")

    source_names = {source_labels.get(item.get("source", ""), item.get("source", ""))
                    for item in all_selected}
    source_hint = "+".join(sorted(s for s in source_names if s)) if source_names else ""
    header = f"（{'、'.join(keywords[:5])}"
    if source_hint:
        header += f" | {source_hint}"
    header += "）"

    if lines:
        lines.insert(0, header)
    return "\n".join(lines)
