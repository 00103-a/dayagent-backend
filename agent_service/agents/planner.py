import os
import re
from pathlib import Path

import httpx
from openai import AsyncOpenAI

from agent_service.schemas.plan_request import PlanResponse

_PROMPT_DIR = Path(__file__).parent.parent / "prompts"


def _load_prompt(filename: str) -> str:
    path = _PROMPT_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _build_http_client() -> httpx.AsyncClient:
    proxy = os.getenv("LLM_PROXY", "")
    kwargs: dict = {
        "timeout": httpx.Timeout(60.0, connect=15.0),
        "follow_redirects": True,
        "trust_env": False,
    }
    if proxy:
        kwargs["proxy"] = proxy
        kwargs["verify"] = False
        print(f"[LLM] 使用代理: {proxy}")
    return httpx.AsyncClient(**kwargs)


def _extract_priorities(plan_text: str) -> list[str]:
    """Extract the 3 focus items from '## 今日重点' section."""
    # Find the section between "## 今日重点" and the next "## " heading
    match = re.search(r'##\s*今日重点\s*\n(.*?)(?=\n##\s|\Z)', plan_text, re.DOTALL)
    if not match:
        return []

    section = match.group(1).strip()
    items = []
    for line in section.split('\n'):
        line = line.strip()
        # Match lines starting with "- " or "1. " etc
        if re.match(r'^[-·•\d+\.\、\)]\s*', line):
            cleaned = re.sub(r'^[-·•\d+\.\、\)]\s*', '', line).strip()
            if len(cleaned) > 4:
                items.append(cleaned)

    return items[:5]  # Max 5


def _extract_warnings(plan_text: str) -> list[str]:
    """Extract warnings from '💡 深度提醒' or '小建议' sections."""
    warnings = []

    # Try "💡 深度提醒" section
    match = re.search(r'💡\s*深度提醒\s*\n(.*?)(?=\n##|\Z)', plan_text, re.DOTALL)
    if not match:
        # Fallback: "小建议" section
        match = re.search(r'💡\s*小建议\s*\n(.*?)(?=\n##|\Z)', plan_text, re.DOTALL)

    if match:
        section = match.group(1).strip()
        for line in section.split('\n'):
            line = line.strip()
            if line and len(line) > 6:
                cleaned = re.sub(r'^[-·•\d+\.\、\)]\s*', '', line).strip()
                if cleaned:
                    warnings.append(cleaned)

    # Also check for weather warnings
    weather_warn = re.search(r'⚠️?\s*(降温|大雨|高温|台风|暴雪|大风|寒潮|沙尘|雾霾).+', plan_text)
    if weather_warn and weather_warn.group(0) not in ' '.join(warnings):
        warnings.insert(0, weather_warn.group(0).strip())

    return warnings[:3]


def _extract_hero_insight(plan_text: str) -> str:
    """Extract the first-line AI insight (in quotes)."""
    lines = plan_text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Look for Chinese quoted text: \u201c...\u201d or \u0022...\u0022
        m = re.search(r'\u201c(.+?)\u201d', line)
        if not m:
            m = re.search(r'\u0022(.+?)\u0022', line)
        if m:
            return m.group(1).strip()
        # If first line is 15-50 chars and looks like a suggestion
        if 15 <= len(line) <= 50 and not line.startswith('#') and not line.startswith('-'):
            return line.strip()
        break
    return ""


def _build_user_message(
    weather_info: str,
    chaoxing_tasks: str,
    course_info: str,
    yesterday_summary: str,
    goals: list[str],
    memory_hint: str,
    parcells_info: str = "",
) -> str:
    goals_text = "\n".join(f"- {g}" for g in goals) if goals else "暂无"
    return f"""## 今日数据

### 天气
{weather_info}

### 学习通作业
{chaoxing_tasks}

### 教务课表
{course_info}

### 昨日总结
{yesterday_summary or "暂无"}

### 当前目标
{goals_text}

### 快递物流
{parcells_info or "暂无待查询的快递"}

### 长期记忆分析
{memory_hint or "暂无"}

请根据以上数据，给我今日汇报。"""


def _create_llm_client(
    llm_api_key: str = "",
    llm_base_url: str = "",
    llm_model: str = "",
) -> tuple[AsyncOpenAI, str, str]:
    """创建 LLM 客户端并返回 (client, model, system_prompt)"""
    system_prompt = _load_prompt("planner_prompt.txt")
    api_key = llm_api_key or os.getenv("LLM_API_KEY", "sk-placeholder")
    base_url = llm_base_url or os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
    model = llm_model or os.getenv("LLM_MODEL", "deepseek-chat")

    for var in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy", "LLM_PROXY"]:
        val = os.environ.get(var, "")
        if val:
            print(f"[LLM-诊断] 环境变量 {var}={val}")

    http_client = _build_http_client()
    print(f"[LLM-诊断] model={model}, base_url={base_url}")

    ai_client = AsyncOpenAI(
        base_url=base_url,
        api_key=api_key,
        http_client=http_client,
    )
    return ai_client, model, system_prompt


def _extract_and_clean(content: str) -> tuple[str, str, list[str], list[str]]:
    """从 LLM 原始输出中提取结构化字段并清理展示文本"""
    hero_insight = _extract_hero_insight(content)
    priorities = _extract_priorities(content)
    warnings = _extract_warnings(content)

    print(f"[LLM] 解析结果 — hero={hero_insight[:40] if hero_insight else 'EMPTY'}..., priorities={len(priorities)}条, warnings={len(warnings)}条")

    plan_display = content
    plan_display = re.sub(r'\n?##\s*今日重点\s*\n.*?(?=\n##\s|\Z)', '\n', plan_display, flags=re.DOTALL)
    plan_display = re.sub(r'\n{3,}', '\n\n', plan_display).strip()

    if hero_insight:
        plan_display = f"&ldquo;{hero_insight}&rdquo;\n\n{plan_display}"

    return plan_display, hero_insight, priorities, warnings


async def generate_plan(
    weather_info: str,
    chaoxing_tasks: str,
    course_info: str,
    yesterday_summary: str,
    goals: list[str],
    memory_hint: str,
    news_info: str = "",
    parcells_info: str = "",
    llm_api_key: str = "",
    llm_base_url: str = "",
    llm_model: str = "",
) -> PlanResponse:
    """调用 LLM 生成当日规划（stream=True 内部收集，降低首 token 延迟）"""

    user_message = _build_user_message(
        weather_info=weather_info,
        chaoxing_tasks=chaoxing_tasks,
        course_info=course_info,
        yesterday_summary=yesterday_summary,
        goals=goals,
        memory_hint=memory_hint,
        parcells_info=parcells_info,
    )

    ai_client, model, system_prompt = _create_llm_client(
        llm_api_key=llm_api_key,
        llm_base_url=llm_base_url,
        llm_model=llm_model,
    )

    try:
        stream = await ai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_tokens=2000,
            stream=True,
        )
        content = ""
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                content += delta
        if not content:
            content = "规划生成失败（空响应）"
    except Exception as e:
        import traceback
        content = f"LLM 调用失败：{e}"
        print(f"[LLM] 调用异常: {type(e).__name__}: {e}")
        traceback.print_exc()

    plan_display, _, priorities, warnings = _extract_and_clean(content)

    await ai_client.close()

    return PlanResponse(
        plan=plan_display,
        priorities=priorities,
        warnings=warnings,
    )


async def generate_plan_stream(
    weather_info: str,
    chaoxing_tasks: str,
    course_info: str,
    yesterday_summary: str,
    goals: list[str],
    memory_hint: str,
    parcells_info: str = "",
):
    """流式生成规划（async generator），供 SSE 端点使用

    用法：
        async for token in generate_plan_stream(...):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"
    """
    user_message = _build_user_message(
        weather_info=weather_info,
        chaoxing_tasks=chaoxing_tasks,
        course_info=course_info,
        yesterday_summary=yesterday_summary,
        goals=goals,
        memory_hint=memory_hint,
        parcells_info=parcells_info,
    )

    ai_client, model, system_prompt = _create_llm_client()

    try:
        stream = await ai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_tokens=2000,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta
    except Exception as e:
        import traceback
        print(f"[LLM] 流式调用异常: {type(e).__name__}: {e}")
        traceback.print_exc()
        yield f"\n\n[生成中断：{e}]"
    finally:
        await ai_client.close()
