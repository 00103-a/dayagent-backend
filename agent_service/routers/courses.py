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
# Background AI processing state (in-memory, resets on restart)
_ai_state: dict = {"processing": False, "error": None, "done": False, "count": 0}

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


@router.post("/import")
async def json_import(payload: dict = Body(...)) -> dict:
    """手动导入课表 JSON 数据

    Body:
      { "courses": [ { "name": "...", "day": 1, "time_slot": "1-2节",
                       "location": "...", "teacher": "...", "weeks": "1-16" }, ... ] }
    """
    raw_courses = payload.get("courses")
    if not raw_courses or not isinstance(raw_courses, list):
        raise HTTPException(status_code=400, detail="缺少 courses 数组")
    if len(raw_courses) == 0:
        raise HTTPException(status_code=400, detail="courses 不能为空")

    courses = []
    for i, c in enumerate(raw_courses):
        if not isinstance(c, dict):
            raise HTTPException(status_code=400, detail=f"courses[{i}] 应为对象")
        name = str(c.get("name", "")).strip()
        if not name:
            raise HTTPException(status_code=400, detail=f"courses[{i}].name 不能为空")
        day = c.get("day")
        if not isinstance(day, int) or day < 1 or day > 7:
            raise HTTPException(status_code=400, detail=f"courses[{i}].day 应为 1-7 的整数")
        courses.append(normalize_course({
            "name": name,
            "day": day,
            "time_slot": str(c.get("time_slot", "")),
            "location": str(c.get("location", "")),
            "teacher": str(c.get("teacher", "")),
            "weeks": str(c.get("weeks", "")),
        }))

    save_courses(courses)
    current_week = _get_current_week()
    return {
        "status": "ok",
        "count": len(courses),
        "courses": courses,
        "current_week": current_week,
        "total_weeks": 20,
        "message": f"成功导入 {len(courses)} 门课程",
    }


@router.post("/ai-import")
async def ai_import(payload: dict = Body(...), background_tasks: BackgroundTasks = BackgroundTasks()) -> dict:
    """AI 智能解析课表原始数据（异步后台处理）

    Body:
      { "cells": [ { "day": 1, "time_slot": "第一大节", "raw_text": "..." }, ... ] }

    接收 raw cells 后立即返回，AI 解析在后台进行。
    前端通过 GET /courses/ai-status 查询进度，完成后自动 reload。
    """
    cells = payload.get("cells")
    if not cells or not isinstance(cells, list):
        raise HTTPException(status_code=400, detail="缺少 cells 数组")
    if len(cells) == 0:
        raise HTTPException(status_code=400, detail="cells 不能为空")

    if _ai_state["processing"]:
        return {"status": "busy", "message": "已有解析任务进行中，请稍后再试"}

    # Extract optional per-user LLM config
    llm_key = payload.get("llm_api_key") or os.getenv("LLM_API_KEY", "sk-placeholder")
    llm_base = payload.get("llm_base_url") or os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
    llm_model = payload.get("llm_model") or os.getenv("LLM_MODEL", "deepseek-chat")

    # Reset state and start background processing
    _ai_state["processing"] = True
    _ai_state["done"] = False
    _ai_state["error"] = None
    _ai_state["count"] = 0

    background_tasks.add_task(
        _process_cells_background, cells, llm_key, llm_base, llm_model
    )

    return {
        "status": "ok",
        "count": len(cells),
        "message": f"已收到 {len(cells)} 个 cell，正在后台 AI 解析...",
    }


@router.get("/ai-status")
async def ai_status() -> dict:
    """查询后台 AI 解析进度"""
    return {
        "processing": _ai_state["processing"],
        "done": _ai_state["done"],
        "error": _ai_state["error"],
        "count": _ai_state["count"],
    }


async def _process_cells_background(
    cells: list,
    llm_key: str = "",
    llm_base: str = "",
    llm_model: str = "",
) -> None:
    """后台任务：调用 LLM 解析 raw cells，保存课程"""
    LLM_TIMEOUT = 90  # seconds per LLM call
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
                _ai_state["error"] = "AI 返回空响应"
                return
        except asyncio.TimeoutError:
            print("[AI-IMPORT] LLM call timed out")
            _ai_state["error"] = "AI 调用超时，请重试"
            return
        finally:
            await ai_client.close()

        # Parse LLM JSON response
        courses_raw = _parse_llm_course_json(content)
        if not courses_raw:
            _ai_state["error"] = "AI 未能解析出有效课程"
            return

        # Normalize and save
        courses = []
        for c in courses_raw:
            name = str(c.get("name", "")).strip()
            if not name:
                continue
            day = c.get("day")
            if not isinstance(day, int) or day < 1 or day > 7:
                continue
            courses.append(normalize_course({
                "name": name,
                "day": day,
                "time_slot": str(c.get("time_slot", "")),
                "location": str(c.get("location", "")),
                "teacher": str(c.get("teacher", "")),
                "weeks": str(c.get("weeks", "")),
            }))

        if not courses:
            _ai_state["error"] = "AI 解析结果中无有效课程"
            return

        save_courses(courses)
        _ai_state["done"] = True
        _ai_state["count"] = len(courses)
        print(f"[AI-IMPORT] done: {len(courses)} courses saved")

    except Exception as e:
        import traceback
        print(f"[AI-IMPORT] background error: {e}")
        traceback.print_exc()
        _ai_state["error"] = str(e)
    finally:
        _ai_state["processing"] = False


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


@router.get("")
async def list_courses(
    week: Optional[str] = Query(None, description="周次筛选：'current'=仅本周 或 具体周号如'5'"),
    semester_start: str = Query("", description="学期开始日期，用于计算当前周"),
) -> dict:
    """查看已导入的课表，支持按教学周筛选"""
    import logging
    logger = logging.getLogger("courses")

    courses = load_courses()

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
        "text": get_all_courses_text(),
        "current_week": current_week,
        "semester_start": os.getenv("SEMESTER_START", ""),
    }


@router.delete("")
async def clear_courses() -> dict:
    """清空课表"""
    save_courses([])
    return {"status": "ok", "message": "课表已清空"}
