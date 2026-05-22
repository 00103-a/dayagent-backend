"""
课表存储与管理模块

手动导入课表，JSON 文件存储。在 /generate-plan 中替代教务抓取。
"""

import json
import os
import re
from datetime import date, datetime, timedelta
from pathlib import Path

from pydantic import BaseModel, Field

_DATA_DIR = Path(__file__).parent.parent / "data"
_COURSES_FILE = _DATA_DIR / "courses.json"

_WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

# 大节课次 → 具体时间
_TIME_SLOT_MAP: dict[str, str] = {
    "第一大节": "8:30-10:05",
    "第二大节": "10:25-12:00",
    "第三大节": "14:00-15:35",
    "第四大节": "15:35-17:30",
    "第五大节": "19:00-20:35",
}


def _get_time_for_slot(time_slot: str) -> str:
    """根据节次名称获取时间，如 第一大节 → 8:30-10:05"""
    # 精确匹配
    if time_slot in _TIME_SLOT_MAP:
        return _TIME_SLOT_MAP[time_slot]
    # 模糊匹配：尝试从字符串中提取"第X大节"
    import re
    m = re.search(r"第[一二三四五六七八九十]+大节", time_slot)
    if m and m.group(0) in _TIME_SLOT_MAP:
        return _TIME_SLOT_MAP[m.group(0)]
    return ""


# ── 学期周次 ────────────────────────────────────────────────────────────────

def _parse_semester_start(semester_start: str = "") -> date | None:
    """解析学期第一周的周一日期。优先用传入值，其次环境变量"""
    val = semester_start or os.getenv("SEMESTER_START", "")
    if val:
        try:
            return datetime.strptime(val, "%Y-%m-%d").date()
        except ValueError:
            pass
    return None


def _get_current_week(semester_start: str = "") -> int | None:
    """返回当前是学期第几周（从 1 开始）。无配置则返回 None"""
    start = _parse_semester_start(semester_start)
    if start is None:
        return None
    today = date.today()
    if today < start:
        return None
    return (today - start).days // 7 + 1


def _parse_week_numbers(weeks_str: str) -> set[int]:
    """解析周次字符串为周号集合。如 '1-16[01-02节](讲课)' → {1,2,...,16}"""
    result: set[int] = set()
    if not weeks_str:
        return result

    # 先提取纯周次部分，去掉节次信息
    # 去掉 [xx-xx节] 这类内容
    weeks_str = re.sub(r'\[.*?\]', '', weeks_str)
    # 去掉 (讲课)(实验) 这类内容（保留(周)）
    weeks_str = re.sub(r'\((?!周)[^)]*\)', '', weeks_str)
    # 去掉"周"字本身
    weeks_str = weeks_str.replace('周', '')

    parts = re.split(r'[,，]', weeks_str)
    for part in parts:
        part = part.strip()
        part = re.sub(r'^P', '', part)
        part = re.sub(r'[^\d\-]', '', part)  # 只保留数字和横线
        if not part:
            continue

        range_match = re.match(r'^(\d+)-(\d+)$', part)
        if range_match:
            s, e = int(range_match.group(1)), int(range_match.group(2))
            if 1 <= s <= 30 and 1 <= e <= 30:  # 合理范围保护
                result.update(range(s, e + 1))
            continue

        if re.match(r'^\d+$', part):
            n = int(part)
            if 1 <= n <= 30:  # 合理范围保护
                result.add(n)

    return result


def _is_week_active(weeks_str: str, current_week: int | None) -> bool:
    """判断课程在指定周是否上课。current_week 为 None 时不筛选"""
    if current_week is None:
        return True
    active = _parse_week_numbers(weeks_str)
    if not active:
        return True  # 无周次信息时默认全上
    return current_week in active


class Course(BaseModel):
    name: str = Field(..., description="课程名称")
    day: int = Field(..., ge=1, le=7, description="星期几，1=周一")
    time_slot: str = Field(default="", description="节次，如 1-2节")
    location: str = Field(default="", description="上课地点")
    teacher: str = Field(default="", description="授课教师")
    weeks: str = Field(default="", description="上课周次，如 1-16周")


def _ensure_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _clean_course_name(raw: str) -> str:
    """从原始课程名中提取干净的课程名。"""
    if not raw:
        return ""

    # Remove square-bracketed content (e.g. [01-02节])
    candidate = re.sub(r"\[.*?\]", "", raw)

    # Split by long dash sequences (---, ——); keep the first segment
    candidate = re.split(r"[-—]{2,}", candidate)[0]

    # Strip parenthesized content
    candidate = re.sub(r"[（()].*?[）()]", "", candidate)

    # Two strategies for the two school formats:
    # Format A (with " - "): "课程名1- 课程名教师名1-16[节次]"
    #   → use lazy lookahead: stop at first "digits + -/,"
    # Format B (no separator): "Java程序设计周翔2,4,6,..."
    #   → use greedy 3-group: name + teacher(2-3字) + weeks(digit)
    # Pick the shortest result that contains no digits.

    results = []

    # Method 1: greedy 3-group for "name+teacher(2-3字)+weeks(digit)" format
    m1 = re.match(r"^([\u4e00-\u9fffA-Za-z ]+)([\u4e00-\u9fff]{2,3})(\d[\d,\-]*)", candidate)
    if m1 and not re.search(r"\d", m1.group(1)):
        results.append(m1.group(1).strip())

    # Method 2: lazy lookahead for "name before digits+separator" format
    m2 = re.match(r"^([\u4e00-\u9fffA-Za-z ]+?)(?=\s*\d+\s*[-—,]|\s+P\d|\s+P(?:\s|$)|\s*\d+\s*$|$)", candidate)
    if m2 and not re.search(r"\d", m2.group(1)):
        results.append(m2.group(1).strip())

    if results:
        candidate = min(results, key=len)  # shortest = most correct

    candidate = candidate.strip()
    return candidate or raw


def _extract_teacher(raw: str, clean_name: str = "") -> str:
    """从原始课程名中提取教师名（2-3字中文名）。"""
    if not raw:
        return ""

    no_brackets = re.sub(r"\[.*?\]", "", raw)

    # Work with the last --- segment (most complete metadata)
    parts = re.split(r"[-—]{2,}", no_brackets)
    target = parts[-1] if len(parts) > 1 else no_brackets

    # Strategy: find the clean course name in the target, then extract
    # the 2-3 Chinese chars right after it (before the digits).
    if clean_name and clean_name in target:
        idx = target.rfind(clean_name)  # last occurrence — teacher is after the repeated name
        after = target[idx + len(clean_name):]
        # Skip leading P (experiment marker) and whitespace
        after = re.sub(r"^\s*P\s*", "", after)  # skip leading space+P (experiment marker)
        m = re.match(r"^([\u4e00-\u9fff]{2,3})\d", after)
        if m:
            name = m.group(1)
            if name not in ("三教", "主教", "田径场", "讲课", "实验", "上机", "考试", "实习", "课程", "辅导", "答疑"):
                return name

    # Fallback: find all 2-3 Chinese char sequences before a digit,
    # use the last valid one (closest to the weeks at the end).
    matches = re.findall(r"([\u4e00-\u9fff]{2,3})\d", target)
    for name in reversed(matches):
        if name not in ("三教", "主教", "田径场", "讲课", "实验", "上机", "考试", "实习", "课程", "辅导", "答疑"):
            return name
    return ""


def _extract_weeks(raw: str) -> str:
    """从原始课程名中提取周次信息。"""
    if not raw:
        return ""

    # Work with the last --- segment (most complete metadata)
    parts = re.split(r"[-—]{2,}", raw)
    target = parts[-1] if len(parts) > 1 else raw

    # Pattern 1: digit(s) right before [xx节] (school format, most reliable)
    m = re.search(r"(P?\d+(?:[,\-]\d+)*)\s*\[", target)
    if m:
        weeks = m.group(1)
        if weeks:
            return re.sub(r"^P", "", weeks)  # strip P prefix

    # Pattern 2: digit(s) followed by 周
    m = re.search(r"(P?\d+(?:[,\-]\d+)*)\s*周", target)
    if m:
        weeks = m.group(1)
        if weeks:
            return re.sub(r"^P", "", weeks)  # strip P prefix

    # Pattern 3: comma-separated long list (e.g. 2,4,6,8,10,12,14,16)
    m = re.search(r"(\d+(?:[,，]\d+){2,})", target)
    if m:
        return m.group(1)

    # Pattern 4: simple range (e.g. 1-16)
    m = re.search(r"(\d+[-—]\d+)", target)
    if m:
        return m.group(1)

    return ""


def normalize_course(course: dict) -> dict:
    """清洗课程数据：提取教师、周次，清理课程名。"""
    raw_name = course.get("name", "")
    clean_name = _clean_course_name(raw_name)
    teacher = course.get("teacher", "") or _extract_teacher(raw_name, clean_name)
    weeks = course.get("weeks", "") or _extract_weeks(raw_name)

    return {
        "name": clean_name,
        "day": course.get("day", 1),
        "time_slot": course.get("time_slot", ""),
        "location": course.get("location", ""),
        "teacher": teacher,
        "weeks": weeks,
    }


def load_courses() -> list[dict]:
    """读取课表 JSON 文件，返回课程字典列表"""
    if not _COURSES_FILE.exists():
        return []
    try:
        return json.loads(_COURSES_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def save_courses(courses: list[dict]) -> None:
    """保存课程列表到 JSON 文件"""
    _ensure_dir()
    _COURSES_FILE.write_text(
        json.dumps(courses, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_today_courses(semester_start: str = "") -> str:
    """
    返回今日课程的自然语言描述，自动过滤非本周课程。
    """
    courses = load_courses()
    if not courses:
        return "课表未导入：请先通过 POST /courses/import 导入课表数据"

    today = date.today()
    current_week = _get_current_week(semester_start)
    weekday = today.weekday()  # 0=周一
    day_name = _WEEKDAY_NAMES[weekday]
    day_index = weekday + 1  # 1=周一

    # Debug logging
    print(f"[COURSES] 今天={today}, 星期{day_index}({day_name}), 第{current_week}周")
    print(f"[COURSES] SEMESTER_START={os.getenv('SEMESTER_START', 'NOT SET')}")
    print(f"[COURSES] 课表共 {len(courses)} 门课程")

    for c in courses:
        name = c.get('name', '')
        day = c.get('day')
        weeks = c.get('weeks', '')

        if day == day_index:
            active = _is_week_active(weeks, current_week)
            week_nums = _parse_week_numbers(weeks)
            print(f"[COURSES-DEBUG] 课程={name}")
            print(f"  weeks字段原始值={repr(weeks)}")
            print(f"  解析出周次集合={week_nums}")
            print(f"  当前第{current_week}周")
            print(f"  是否上课={active}")
            print(f"  day={day}, 今天day_index={day_index}")

    # 筛选今日 + 本周的课程
    today_courses = [
        c for c in courses
        if c.get("day") == day_index and _is_week_active(c.get("weeks", ""), current_week)
    ]

    print(f"[COURSES] 过滤后今日课程数: {len(today_courses)}")
    for c in today_courses:
        print(f"[COURSES]  -> {c.get('name')}")

    week_info = f"第{current_week}周" if current_week else ""

    if not today_courses:
        msg = f"今日（{day_name}）" + (f" {week_info}" if week_info else "") + "无课程安排"
        return msg

    header = f"今日（{day_name}）" + (f" {week_info}" if week_info else "") + "课程："
    lines = [header]
    for c in sorted(today_courses, key=lambda x: x.get("time_slot", "")):
        ts = c.get("time_slot", "")
        time_str = _get_time_for_slot(ts)
        slot_display = f"{ts}（{time_str}）" if time_str else ts
        parts = [f"{slot_display} {c['name']}"]
        if c.get("teacher"):
            parts.append(f"（{c['teacher']}）")
        if c.get("location"):
            parts.append(f" @{c['location']}")
        if c.get("weeks"):
            parts.append(f" [{c['weeks']}]")
        lines.append("  " + "".join(parts))
    return "\n".join(lines)


def get_all_courses_text() -> str:
    """返回完整课表的自然语言描述"""
    courses = load_courses()
    if not courses:
        return "课表未导入"

    grouped: dict[int, list[dict]] = {}
    for c in courses:
        grouped.setdefault(c.get("day", 1), []).append(c)

    lines = ["完整课表："]
    for day_idx in range(1, 8):
        day_name = _WEEKDAY_NAMES[day_idx - 1]
        day_courses = grouped.get(day_idx, [])
        if not day_courses:
            continue
        lines.append(f"\n{day_name}：")
        for c in sorted(day_courses, key=lambda x: x.get("time_slot", "")):
            ts = c.get("time_slot", "")
            time_str = _get_time_for_slot(ts)
            slot_display = f"{ts}（{time_str}）" if time_str else ts
            parts = [f"  {slot_display} {c['name']}"]
            if c.get("teacher"):
                parts.append(f"（{c['teacher']}）")
            if c.get("location"):
                parts.append(f" @{c['location']}")
            if c.get("weeks"):
                parts.append(f" [{c['weeks']}]")
            lines.append("".join(parts))
    return "\n".join(lines)
