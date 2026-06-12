"""课表管理 API"""

import asyncio
import json
import os
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Body, Query, BackgroundTasks
from openai import AsyncOpenAI

from agent_service.tools.courses import (
    load_courses,
    save_courses,
    normalize_course,
    get_all_courses_text,
    _get_current_week,
    _is_week_active,
)
from agent_service.tools.jwc import browser_login_and_parse
# Background AI processing state (in-memory, resets on restart) — now per-user
_ai_states: dict[str, dict] = {}

COURSE_PARSE_PROMPT = """你是一个大学课表数据解析器。你会收到一批从教务系统课表页面抓取的原始 cell 文本，每个 cell 包含 day（1-7，1=周一）、time_slot（如"第一大节"）和 raw_text（该格子的文本内容）。

请从每个 cell 的 raw_text 中提取课程信息，返回严格的 JSON 数组。

## 提取规则

1. **name（课程名）**: raw_text 中最长的中文/英文课程名称，去除周次、教师、地点信息
2. **teacher（教师）**: 2-3字的中文人名，通常紧跟在课程名之后或数字之前。排除：讲课、实验、上机、考试、实习、三教、主教、田径场 等非人名词
3. **weeks（周次）**: 数字序列，可能是范围"1-16"或列表"2,4,6,8,10,12,14,16"。raw_text 中可能带有"周"字或"(周)"标记
4. **location（地点）**: 包含"教"字的教室号（如"三教3421"、"主教1101"），或纯数字教室号（3-4位数字），或"田径场"等特殊地点
5. **day/time_slot**: 直接使用输入中提供的值，不需要从 raw_text 中提取

## 重要规则

- 一个 cell 可能包含多门课程（用分隔线分开），需要拆分为多个课程对象
- 如果 raw_text 中无法识别出有效课程名，跳过该 cell
- 保持 weeks 为纯数字格式，去除"周"、"(周)"、"P" 等前缀/后缀
- day 保持为数字 1-7

## 输出格式

只返回 JSON 数组，不要有任何其他文字：

```json
[
  {
    "name": "Python数据分析",
    "day": 5,
    "time_slot": "第三大节",
    "location": "三教3421",
    "teacher": "宋彦儒",
    "weeks": "2,4,6,8,10,12,14,16"
  }
]
```"""


def _build_llm_http_client() -> httpx.AsyncClient:
    proxy = os.getenv("LLM_PROXY", "")
    kwargs: dict = {
        "timeout": httpx.Timeout(60.0, connect=15.0),
        "follow_redirects": True,
        "trust_env": False,
    }
    if proxy:
        kwargs["proxy"] = proxy
        kwargs["verify"] = False
    return httpx.AsyncClient(**kwargs)


def _create_llm_client(
    api_key: str = "",
    base_url: str = "",
) -> AsyncOpenAI:
    http_client = _build_llm_http_client()
    return AsyncOpenAI(
        base_url=base_url or os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
        api_key=api_key or os.getenv("LLM_API_KEY", "sk-placeholder"),
        http_client=http_client,
    )

router = APIRouter(prefix="/courses", tags=["课表管理"])


@router.post("/ai-import")
async def ai_import(payload: dict = Body(...), background_tasks: BackgroundTasks = BackgroundTasks()) -> dict:
    """AI 智能解析课表原始数据（异步后台处理）

    Body:
      { "cells": [ { "day": 1, "time_slot": "第一大节", "raw_text": "..." }, ... ],
        "user_id": "..." }

    接收 raw cells 后立即返回，AI 解析在后台进行。
    前端通过 GET /courses/ai-status?user_id=xxx 查询进度，完成后自动 reload。
    """
    cells = payload.get("cells")
    if not cells or not isinstance(cells, list):
        raise HTTPException(status_code=400, detail="缺少 cells 数组")
    if len(cells) == 0:
        raise HTTPException(status_code=400, detail="cells 不能为空")

    user_id = str(payload.get("user_id", ""))

    state = _ai_states.get(user_id)
    if state and state["processing"]:
        return {"status": "busy", "message": "已有解析任务进行中，请稍后再试"}

    # Extract optional per-user LLM config
    llm_key = payload.get("llm_api_key") or os.getenv("LLM_API_KEY", "sk-placeholder")
    llm_base = payload.get("llm_base_url") or os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
    llm_model = payload.get("llm_model") or os.getenv("LLM_MODEL", "deepseek-chat")

    # Reset state and start background processing
    _ai_states[user_id] = {"processing": True, "error": None, "done": False, "count": 0}

    background_tasks.add_task(
        _process_cells_background, cells, llm_key, llm_base, llm_model, user_id
    )

    return {
        "status": "ok",
        "count": len(cells),
        "message": f"已收到 {len(cells)} 个 cell，正在后台 AI 解析...",
    }


@router.get("/ai-status")
async def ai_status(user_id: str = Query("")) -> dict:
    """查询后台 AI 解析进度"""
    state = _ai_states.get(user_id, {})
    return {
        "processing": state.get("processing", False),
        "done": state.get("done", False),
        "error": state.get("error"),
        "count": state.get("count", 0),
    }


@router.post("/browser-import")
async def browser_import(user_id: str = Query("")) -> dict:
    """桌面端浏览器自动导入课表（Playwright 自动化）

    启动 Chromium 浏览器，用户在浏览器中手动登录教务系统，
    登录后自动检测课表页面并解析课程数据。

    Query:
      user_id: 用户 ID
    """
    try:
        courses = await browser_login_and_parse(timeout_seconds=300)
    except RuntimeError as e:
        raise HTTPException(status_code=408, detail=f"导入超时：{e}")

    if not courses:
        raise HTTPException(status_code=400, detail="未能解析到课程数据，请确认已进入课表页面")

    # Normalize courses before saving
    normalized = [normalize_course(c) for c in courses]
    save_courses(normalized, user_id)

    current_week = _get_current_week()
    return {
        "status": "ok",
        "count": len(normalized),
        "courses": normalized,
        "current_week": current_week,
        "total_weeks": 20,
        "message": f"成功导入 {len(normalized)} 门课程",
    }


async def _process_cells_background(
    cells: list,
    llm_key: str = "",
    llm_base: str = "",
    llm_model: str = "",
    user_id: str = "",
) -> None:
    """后台任务：调用 LLM 解析 raw cells，保存课程"""
    LLM_TIMEOUT = 90  # seconds per LLM call
    state = _ai_states.get(user_id, {"processing": True, "error": None, "done": False, "count": 0})
    try:
        # Build user message
        cell_lines = []
        for i, cell in enumerate(cells):
            day = cell.get("day", "?")
            ts = cell.get("time_slot", "?")
            raw = str(cell.get("raw_text", ""))
            cell_lines.append(f"[{i}] day={day}, time_slot={ts}\n{raw}")

        user_message = "请解析以下课表 cell 数据：\n\n" + "\n".join(cell_lines)
        print(f"[AI-IMPORT] starting background task: {len(cells)} cells, {len(user_message)} chars")

        model = llm_model or os.getenv("LLM_MODEL", "deepseek-chat")
        ai_client = _create_llm_client(api_key=llm_key, base_url=llm_base)

        try:
            stream = await asyncio.wait_for(
                ai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": COURSE_PARSE_PROMPT},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0.3,
                    max_tokens=4000,
                    stream=True,
                ),
                timeout=LLM_TIMEOUT,
            )
            content = ""
            chunk_count = 0
            async for chunk in stream:
                chunk_count += 1
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    content += delta

            print(f"[AI-IMPORT] stream: {chunk_count} chunks, {len(content)} chars")
            if not content:
                import traceback as tb
                print("[AI-IMPORT] stream empty, retrying stream=False...")
                resp = await asyncio.wait_for(
                    ai_client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": COURSE_PARSE_PROMPT},
                            {"role": "user", "content": user_message},
                        ],
                        temperature=0.3,
                        max_tokens=4000,
                        stream=False,
                    ),
                    timeout=LLM_TIMEOUT,
                )
                content = resp.choices[0].message.content if resp.choices else ""
                print(f"[AI-IMPORT] non-stream: {len(content) if content else 0} chars")

            if not content:
                state["error"] = "AI 返回空响应"
                return
        except asyncio.TimeoutError:
            print("[AI-IMPORT] LLM call timed out")
            state["error"] = "AI 调用超时，请重试"
            return
        finally:
            await ai_client.close()

        # Parse LLM JSON response
        courses_raw = _parse_llm_course_json(content)
        if not courses_raw:
            state["error"] = "AI 未能解析出有效课程"
            return

        # Normalize and fill missing fields from raw cells via regex
        courses = []
        for c in courses_raw:
            name = str(c.get("name", "")).strip()
            if not name:
                continue
            day = c.get("day")
            if not isinstance(day, int) or day < 1 or day > 7:
                continue
            teacher = str(c.get("teacher", "")).strip()
            location = str(c.get("location", "")).strip()
            weeks = str(c.get("weeks", "")).strip()
            time_slot = str(c.get("time_slot", "")).strip()

            # Fallback: fill missing fields from matching raw cell
            if not teacher or not location or not weeks:
                raw = _find_matching_cell(cells, day, time_slot)
                if raw:
                    if not teacher:
                        teacher = _extract_teacher(raw)
                    if not location:
                        location = _extract_location(raw)
                    if not weeks:
                        weeks = _extract_weeks(raw)

            courses.append(normalize_course({
                "name": name,
                "day": day,
                "time_slot": time_slot,
                "location": location,
                "teacher": teacher,
                "weeks": weeks,
            }))

        if not courses:
            state["error"] = "AI 解析结果中无有效课程"
            return

        save_courses(courses, user_id)
        state["done"] = True
        state["count"] = len(courses)
        print(f"[AI-IMPORT] done: {len(courses)} courses saved for user={user_id}")

    except Exception as e:
        import traceback
        print(f"[AI-IMPORT] background error: {e}")
        traceback.print_exc()
        state["error"] = str(e)
    finally:
        state["processing"] = False


def _parse_llm_course_json(content: str) -> list[dict]:
    """从 LLM 返回的文本中提取 JSON 数组"""
    # Try direct JSON parse first
    text = content.strip()
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Try to extract JSON array from markdown code blocks
    import re
    m = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if m:
        try:
            result = json.loads(m.group(1))
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    # Try to find JSON array between [ and ]
    m = re.search(r'\[\s*\{[\s\S]*\}\s*\]', text)
    if m:
        try:
            result = json.loads(m.group(0))
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    return []


def _find_matching_cell(cells: list, day, time_slot: str) -> str:
    """Find the raw_text from a cell matching the given day and time_slot."""
    for cell in cells:
        if cell.get("day") == day and cell.get("time_slot", "") == time_slot:
            return str(cell.get("raw_text", ""))
    # Fallback: match by day only
    for cell in cells:
        if cell.get("day") == day:
            return str(cell.get("raw_text", ""))
    return ""


def _extract_teacher(raw: str) -> str:
    """Extract teacher name (2-3 Chinese chars before a digit sequence)."""
    import re
    # 2-3 Chinese chars immediately before week numbers or standalone digits
    m = re.search(r'([\u4e00-\u9fff]{2,3})\d', raw)
    if m:
        name = m.group(1)
        # Filter out non-name words
        if name not in ('实验室', '田径场', '体育馆', '语音室'):
            return name
    return ""


def _extract_location(raw: str) -> str:
    """Extract classroom location from raw text."""
    import re
    # Pattern: X教DDDD (三教3421, 主教1101)
    m = re.search(
        r'[一二三四五六七八九十东西南北主分]*教\d+',
        raw
    )
    if m:
        return m.group(0)
    # Standalone 3-4 digit room number
    m = re.search(r'\b(\d{3,4})\b', raw)
    if m and '教' not in raw:
        return m.group(1)
    # Special locations
    m = re.search(r'(田径场|体育馆|实验室\d*|机房\d*|语音室\d*)', raw)
    if m:
        return m.group(1)
    return ""


def _extract_weeks(raw: str) -> str:
    """Extract weeks pattern from raw text."""
    import re
    # Range: "1-16" with optional "(周)" or "周"
    m = re.search(r'(\d+[-－]\d+)\s*(?:\(?周\)?)?', raw)
    if m:
        weeks = m.group(1)
        suffix = ""
        if "周" in raw[m.end():m.end()+5]:
            suffix = "(周)"
        # Check for course type
        type_m = re.search(r'(讲课|实验|实践|上机|实习)', raw)
        if type_m:
            return f"{weeks}{suffix} {type_m.group(1)}"
        return f"{weeks}{suffix}"
    # List: "2,4,6,8"
    m = re.search(r'(\d+(?:[,，]\d+)+)\s*(?:\(?周\)?)?', raw)
    if m:
        weeks = m.group(1)
        type_m = re.search(r'(讲课|实验|实践|上机|实习)', raw)
        if type_m:
            return f"{weeks}(周) {type_m.group(1)}"
        return f"{weeks}(周)"
    return ""


@router.get("")
async def list_courses(
    week: Optional[str] = Query(None, description="周次筛选：'current'=仅本周 或 具体周号如'5'"),
    semester_start: str = Query("", description="学期开始日期，用于计算当前周"),
    user_id: str = Query("", description="用户 ID"),
) -> dict:
    """查看已导入的课表，支持按教学周筛选"""
    import logging
    logger = logging.getLogger("courses")

    courses = load_courses(user_id)

    # 周次筛选
    current_week = _get_current_week(semester_start)
    filter_week = None
    if week == "current" and current_week is not None:
        filter_week = current_week
    elif week and week.isdigit():
        filter_week = int(week)

    # Debug logging
    print(f"[courses API] GET /courses week={week!r} current_week={current_week} filter_week={filter_week} total_courses={len(courses)}")
    print(f"[courses API] SEMESTER_START env: {os.getenv('SEMESTER_START', 'NOT SET')}")

    if filter_week is not None:
        before_count = len(courses)
        courses = [
            c for c in courses
            if _is_week_active(c.get("weeks", ""), filter_week)
        ]
        print(f"[courses API] Filtered: {before_count} → {len(courses)} courses (week {filter_week})")

    return {
        "count": len(courses),
        "courses": courses,
        "text": get_all_courses_text(user_id),
        "current_week": current_week,
        "semester_start": os.getenv("SEMESTER_START", ""),
    }


@router.delete("")
async def clear_courses(user_id: str = Query("")) -> dict:
    """清空课表"""
    save_courses([], user_id)
    return {"status": "ok", "message": "课表已清空"}
