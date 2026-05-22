"""
教务系统课表抓取 — 江西理工大学（金智教育 Wisedu + 苏文 CAS）

方案：Playwright 启动 Chromium 浏览器 → 用户手动登录 → 系统自动检测课表 → 抓取 HTML → 解析入库

为什么不自动登录：深信服 aTrust VPN 网关在外网拦截所有教务请求返回 JS 壳，纯 HTTP 无法突破。
"""

import asyncio
import re
import sys
from urllib.parse import quote as url_quote

# Windows 必须用 ProactorEventLoop，否则 Playwright 子进程无法启动
# （main.py 也设了，但 uvicorn reload worker 可能不继承，这里补一刀）
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from bs4 import BeautifulSoup

# ── 常量 ────────────────────────────────────────────────────────────────────

_CAS_LOGIN_URL = "https://authserver.jxust.edu.cn/authserver/login"
_CAS_SERVICE = "https://jw.jxust.edu.cn/jsxsd/"
_SCHEDULE_URL = "https://jw.jxust.edu.cn/jsxsd/xskb/xskb_list.do"

_WEEKDAY_MAP = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "日": 7}


# ── 课表 HTML 解析 ────────────────────────────────────────────────────────────

def _extract_course_name(cell_text: str) -> str:
    """从 cell_text 中提取纯课程名，在第一个周次/数字信息前截断"""
    # 先找到第一个周次信息的位置
    week_pos = re.search(
        r'\d+[-－]\d+\(周\)'        # 1-16(周)
        r'|\d+,\d+'                 # 2,4,6
        r'|\d+[-－]\d+(?=\D)'       # 1-16
        r'|P\d+\(周\)'             # P3(周)
        r'|[\u4e00-\u9fff]{2}(?=\d)',  # 教师名后跟数字
        cell_text
    )

    if week_pos:
        candidate = cell_text[:week_pos.start()].strip()
    else:
        candidate = cell_text

    # 去掉连续横线及之后内容（多门课分隔符）
    candidate = re.split(r'[-－]{2,}', candidate)[0].strip()

    # 遇到"数字+横线"的组合立即截断（如 "Python数据分析1-Python数据分析"）
    candidate = re.split(r'\d+[-－]', candidate)[0].strip()

    # 遇到纯数字开始的位置截断（如 "数据库系统概论13-16三教" → "数据库系统概论"）
    num_start = re.search(r'\d', candidate)
    if num_start and num_start.start() > 1:
        before = candidate[:num_start.start()].strip()
        # 如果数字前的内容以汉字结尾，说明后面的数字是周次信息
        if re.search(r'[\u4e00-\u9fff]$', before):
            candidate = before

    # 去掉末尾独立数字（周次碎片，如 " 1"）
    candidate = re.sub(r'\s+\d+\s*$', '', candidate).strip()

    # 去掉末尾教师名（2-3个汉字，不在黑名单中）
    _not_teacher = {
        "周次", "讲课", "实验", "上机", "实践", "理论", "实习", "考试",
        "备注", "生产", "安排", "概论", "逻辑", "系统", "分析", "原理",
        "主义", "基本", "大学", "程序", "心理", "幸福", "数据",
        "体育", "英语", "形势", "政策", "数字", "设计", "工程",
    }
    teacher_end = re.search(r'\s*([\u4e00-\u9fff]{2,3})$', candidate)
    if teacher_end:
        name = teacher_end.group(1)
        if name not in _not_teacher and len(candidate) > len(name) + 1:
            candidate = re.sub(r'\s*[\u4e00-\u9fff]{2,3}$', '', candidate).strip()

    # 去掉末尾杂符号
    candidate = re.sub(r'[\s\-\_\.\,，\[\]]+$', '', candidate).strip()

    return candidate if len(candidate) >= 2 else ""


def _parse_cell_detail(cell_text: str) -> tuple[str, str, str]:
    """从课表 cell 的拼接文本中提取 (teacher, location, weeks)

    Cell 文本格式（金智教育把字段全拼在一个字符串里）:
      课程名 + 周次 + 教室 + 课程名(重复) + 教师 + 周次 + [时间] + 教室 + (类型)
      可能用 ------ 分隔多个时间段
    """
    teacher = ""
    location = ""
    weeks_all: list[str] = []

    parts = re.split(r'-{5,}', cell_text)
    for part in parts:
        part = part.strip()
        if not part or "备注" in part:
            continue

        # 提取周次 — 同时匹配带(周)和不带(周)的格式
        w_matches = re.findall(
            r'[\d,，\-]+\(周\)'          # 标准格式：1-16(周), 2,4,6(周)
            r'|P\d+\(周\)'              # 隔周格式：P3(周)
            r'|\d+[-－]\d+(?=\D|$)'     # 无(周)范围：1-16
            r'|(?<!\d)[\d,，]+(?=三教|[A-Za-z\u4e00-\u9fff])',  # 无(周)列举
            part
        )
        weeks_all.extend(w_matches)

        # 提取教师: 紧挨着周次前的 2 个汉字（用 {2} 避免贪婪吞课程名尾字）
        teacher_matches = re.findall(
            r'([\u4e00-\u9fff]{2})(?=[\d,\-]+\(周\)|P\d+\(周\))',
            part
        )
        _not_teacher = {
            "周次", "讲课", "实验", "上机", "实践", "理论", "实习", "考试",
            "备注", "生产", "安排", "概论", "逻辑", "系统", "分析", "原理",
            "主义", "基本", "大学", "程序", "心理", "幸福", "数据",
            "体育", "英语", "形势", "政策", "数字", "设计", "工程",
            "导论", "基础", "技术", "方法", "应用", "结构", "组成",
            "网络", "操作", "电子", "电路", "信号", "通信", "控制",
            "管理", "经济", "营销", "会计", "财务", "商务", "法学",
        }
        for tm in teacher_matches:
            if tm not in _not_teacher:
                teacher = tm

        # 提取地点: 4 位教室号 / "三教"+"数字" / "田径场"
        loc_match = re.search(r'(三教\d+|\d{4}(?=[^\d]|$)|田径场\d*)', part)
        if loc_match and not location:
            location = loc_match.group(1)

    weeks = ",".join(sorted(set(weeks_all))) if weeks_all else ""
    return teacher, location, weeks


def parse_schedule_to_courses(html: str) -> list[dict]:
    """从课表 HTML 表格解析结构化课程列表

    处理 rowspan/colspan 合并单元格。
    返回: [{"name":"", "day":1, "time_slot":"第一大节", "location":"1404", "teacher":"来俊", "weeks":"1-16(周)"}, ...]
    """
    soup = BeautifulSoup(html, "lxml")

    table = soup.find("table", {"class": ["infolist_tab", "table", "gridtable"]})
    if table is None:
        table = soup.find("table")
    if table is None:
        raise RuntimeError("未找到课表表格，请确认已登录教务并打开课表页面")

    rows = table.find_all("tr")
    if len(rows) < 2:
        raise RuntimeError("课表表格行数不足")

    # ── 构建网格（展开 rowspan/colspan） ──────────────────────
    max_cols = 0
    all_cells_info: list[list[dict]] = []
    for row in rows:
        cells = row.find_all(["td", "th"])
        total_cols = sum(int(c.get("colspan", 1)) for c in cells)
        max_cols = max(max_cols, total_cols)
        all_cells_info.append([
            {"text": c.get_text(strip=True), "rowspan": int(c.get("rowspan", 1)), "colspan": int(c.get("colspan", 1))}
            for c in cells
        ])

    num_rows = len(rows)
    grid = [[""] * max_cols for _ in range(num_rows)]
    for ri, row_cells in enumerate(all_cells_info):
        ci = 0
        for cell_info in row_cells:
            while ci < max_cols and grid[ri][ci] != "":
                ci += 1
            if ci >= max_cols:
                break
            for dr in range(cell_info["rowspan"]):
                for dc in range(cell_info["colspan"]):
                    rr, cc = ri + dr, ci + dc
                    if rr < num_rows and cc < max_cols:
                        grid[rr][cc] = cell_info["text"]
            ci += cell_info["colspan"]

    # ── 表头 → day 映射 ───────────────────────────────────────
    col_day: list[int | None] = []
    for c in range(max_cols):
        header_text = grid[0][c]
        day_idx = None
        for ch, d in _WEEKDAY_MAP.items():
            if ch in header_text:
                day_idx = d
                break
        col_day.append(day_idx)

    # ── 逐行解析 ──────────────────────────────────────────────
    courses: list[dict] = []
    seen = set()

    for ri in range(1, num_rows):
        raw_time_slot = grid[ri][0] if max_cols > 0 else ""
        if not raw_time_slot or "备注" in raw_time_slot:
            continue

        time_slot = raw_time_slot
        tm = re.search(r"第[一二三四五六七八九十]+大?节", raw_time_slot)
        if tm:
            time_slot = tm.group(0)

        for ci in range(1, max_cols):
            if ci >= len(col_day) or col_day[ci] is None:
                continue

            cell_text = grid[ri][ci]
            if not cell_text or cell_text in ("&nbsp;", "\xa0", "无", ""):
                continue

            # 诊断日志：打印原始 cell 内容
            print(f"[JWC-DEBUG] 原始cell: {repr(cell_text[:120])}")
            teacher, location, weeks = _parse_cell_detail(cell_text)
            print(f"[JWC-DEBUG] 解析结果 → teacher={teacher}, location={location}, weeks={weeks}")

            # 提取课程名
            course_name = _extract_course_name(cell_text)
            print(f"[JWC-DEBUG] 课程名 → {course_name}")
            if not course_name or len(course_name) < 2:
                continue

            dedup_key = f"{col_day[ci]}_{ri}_{course_name}"
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            teacher, location, weeks = _parse_cell_detail(cell_text)

            courses.append({
                "name": course_name,
                "day": col_day[ci],
                "time_slot": time_slot,
                "location": location,
                "teacher": teacher,
                "weeks": weeks,
            })

    if not courses:
        raise RuntimeError("未能提取到任何课程，请确认课表页面有数据")

    print(f"[JWC] 解析成功，提取到 {len(courses)} 门课程")
    return courses


# ── 浏览器内详情获取 ────────────────────────────────────────────────────────────

async def _try_enrich_from_page(page) -> list[dict] | None:
    """在课表页面上尝试获取课程详情（教师/地点/周次）

    策略:
      1. 导航到课表详情页 xskb/xskb_list.do（最可靠）
      2. 检查 cell 的 onclick/title 属性
      3. 找"详细"/"列表"/"周次"链接切换视图
      4. 逐个点击课程格子收集弹窗详情

    返回带详情的课程列表，失败返回 None
    """
    # ── 策略 1: 导航到课表详情页 ────────────────────────────
    try:
        print("[JWC-Browser] 策略1: 导航到课表详情页...")
        await page.goto(_SCHEDULE_URL, wait_until="networkidle", timeout=15000)
        await page.wait_for_timeout(1500)
        html = await page.content()
        if "课表" in html or "课程" in html or "节" in html:
            try:
                courses = parse_schedule_to_courses(html)
                if any(c.get("teacher") or c.get("location") or c.get("weeks") for c in courses):
                    print("[JWC-Browser] 详情页有完整数据!")
                    return courses
            except Exception:
                pass
            print(f"[JWC-Browser] 详情页 HTML 长度: {len(html)}, 无完整字段")
    except Exception as e:
        print(f"[JWC-Browser] 策略1 失败: {e}")

    # ── 策略 2: 检查 cell 的 onclick/title ──────────────────
    try:
        cell_data = await page.evaluate("""() => {
            const cells = document.querySelectorAll('table td');
            const info = [];
            for (const cell of cells) {
                const onclick = cell.getAttribute('onclick') || '';
                const title = cell.getAttribute('title') || '';
                const text = (cell.textContent || '').trim();
                if (text.length > 2 && (onclick + title).length > 10) {
                    info.push({text: text.substring(0, 60), onclick: onclick.substring(0, 300), title: title.substring(0, 200)});
                }
            }
            return info.slice(0, 5);
        }""")
        if cell_data:
            print(f"[JWC-Browser] 策略2: {len(cell_data)} 个 cell 有 onclick/title")
            for item in cell_data[:2]:
                print(f"  text='{item['text']}' onclick='{item['onclick'][:100]}'")
    except Exception as e:
        print(f"[JWC-Browser] 策略2 失败: {e}")

    # ── 策略 3: 点击"详细"/"列表"/"周次"链接 ──────────────────
    clicked_label = await page.evaluate("""() => {
        const keywords = ['列表', '详细', '周次', '打印', '列表模式', '详细信息', '按列表'];
        const els = document.querySelectorAll('a, li, span, button, .tab, .nav-item');
        for (const el of els) {
            const t = (el.textContent || '').trim();
            if (keywords.includes(t)) { el.click(); return t; }
        }
        for (const el of els) {
            const t = (el.textContent || '').trim();
            for (const kw of keywords) {
                if (t.includes(kw)) { el.click(); return t; }
            }
        }
        return '';
    }""")
    if clicked_label:
        print(f"[JWC-Browser] 策略3: 点击了 '{clicked_label}'")
        await page.wait_for_timeout(2500)
        await page.wait_for_load_state("networkidle", timeout=10000)
        html = await page.content()
        try:
            courses = parse_schedule_to_courses(html)
            if any(c.get("teacher") or c.get("location") or c.get("weeks") for c in courses):
                print("[JWC-Browser] 策略3 获取成功!")
                return courses
        except Exception:
            pass

    # ── 策略 4: 逐个点击课程格子收集弹窗详情 ──────────────────
    try:
        cell_infos = await page.evaluate("""() => {
            const results = [];
            const tables = document.querySelectorAll('table');
            for (const table of tables) {
                const rows = table.querySelectorAll('tr');
                for (let r = 1; r < rows.length; r++) {
                    const cells = rows[r].querySelectorAll('td');
                    const timeLabel = cells[0] ? cells[0].textContent.trim() : '';
                    for (let c = 1; c < cells.length; c++) {
                        const text = cells[c].textContent.trim();
                        if (text.length > 2 && text.length < 50) {
                            results.push({
                                col: c, row: r, name: text, time: timeLabel,
                                selector: `table tr:nth-child(${r + 1}) td:nth-child(${c + 1})`
                            });
                        }
                    }
                }
            }
            return results;
        }""")
        if not cell_infos:
            return None

        print(f"[JWC-Browser] 策略4: 共 {len(cell_infos)} 个课程格子，探测弹窗...")
        first = cell_infos[0]
        await page.click(first["selector"])
        await page.wait_for_timeout(1500)
        popup_text = await page.evaluate("""() => {
            const sels = '.modal, .dialog, .popup, .layer, .panel, [role="dialog"], .ui-dialog, .layui-layer, .win, .window';
            const all = document.querySelectorAll(sels);
            for (const el of all) {
                if (el.offsetHeight > 0) return el.textContent.substring(0, 500);
            }
            const divs = document.querySelectorAll('div[style*="display: block"]');
            for (const d of divs) {
                if (d.offsetHeight > 50 && d.textContent.length > 20) return d.textContent.substring(0, 500);
            }
            return '';
        }""")
        print(f"[JWC-Browser] 弹窗内容: {popup_text[:200]}")

        # 关弹窗
        await page.evaluate("""() => {
            const btns = document.querySelectorAll('.close, .layui-layer-close, [onclick*="close"], .ui-dialog-close');
            for (const b of btns) { if (b.offsetHeight > 0) { b.click(); return; } }
            document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true}));
        }""")
        await page.wait_for_timeout(500)

        has_detail = popup_text and any(kw in popup_text for kw in ["教师", "地点", "周次", "教室", "老师", "上课"])
        if not has_detail:
            print("[JWC-Browser] 弹窗无详情，跳过逐个点击")
            return None

        print(f"[JWC-Browser] 开始逐个点击 {len(cell_infos)} 个课程...")
        details = []
        for i, ci in enumerate(cell_infos):
            try:
                await page.click(ci["selector"])
                await page.wait_for_timeout(1000)
                detail_text = await page.evaluate("""() => {
                    const sels = '.modal, .dialog, .popup, .layer, .panel, [role="dialog"], .ui-dialog, .layui-layer, .win';
                    const all = document.querySelectorAll(sels);
                    for (const el of all) {
                        if (el.offsetHeight > 0) return el.textContent;
                    }
                    return '';
                }""")
                details.append({"name": ci["name"], "time": ci["time"], "detail": detail_text})
                await page.evaluate("""() => {
                    const btns = document.querySelectorAll('.close, .layui-layer-close, [onclick*="close"], .ui-dialog-close');
                    for (const b of btns) { if (b.offsetHeight > 0) { b.click(); return; } }
                    document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true}));
                }""")
                await page.wait_for_timeout(300)
                if i % 5 == 0 and i > 0:
                    print(f"  [{i}/{len(cell_infos)}]")
            except Exception:
                continue

        print(f"[JWC-Browser] 收集到 {len(details)} 条详情")
        return _parse_popup_details(details, cell_infos)
    except Exception as e:
        print(f"[JWC-Browser] 策略4 失败: {e}")
        import traceback
        traceback.print_exc()

    return None


def _parse_popup_details(details: list[dict], course_cells: list[dict]) -> list[dict]:
    """从弹窗文本解析教师/地点/周次"""
    courses = []
    for d in details:
        text = d["detail"]
        teacher = ""
        location = ""
        weeks = ""

        for line in text.replace("\n", " ").split():
            line = line.strip()
            if not line:
                continue
            if any(kw in line for kw in ("教师", "老师", "任课", "授课")) and len(line) < 30:
                teacher = line
            elif any(kw in line for kw in ("地点", "教室", "上课地点", "教学楼", "机房", "实验室")):
                location = line
            elif "周" in line and any(c.isdigit() for c in line) and len(line) < 50:
                weeks = line

        match = next((c for c in course_cells if c["name"] == d["name"] and c["time"] == d.get("time", "")), None)
        if not match:
            match = next((c for c in course_cells if c["name"] == d["name"]), None)

        courses.append({
            "name": d["name"],
            "day": 0,
            "time_slot": (match or d).get("time", ""),
            "location": location.replace("地点：", "").replace("上课地点：", "").strip(),
            "teacher": teacher.replace("教师：", "").replace("任课教师：", "").replace("老师：", "").strip(),
            "weeks": weeks.replace("周次：", "").strip(),
        })
    return courses


# ── 公开接口 ──────────────────────────────────────────────────────────────────

async def browser_login_and_parse(timeout_seconds: int = 300) -> list[dict]:
    """启动 Chromium 浏览器，用户手动登录教务，自动抓取课表

    调用后弹出浏览器窗口 → 用户手动完成 CAS 登录（含验证码）→
    进入教务主页后系统自动检测课表表格 → 抓取 HTML → 解析课程 → 关闭浏览器。

    timeout_seconds: 等待用户登录的超时秒数，默认 5 分钟
    返回: [{"name":"", "day":1, "time_slot":"第一大节", "location":"1404", "teacher":"来俊", "weeks":"1-16(周)"}, ...]
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise RuntimeError("请先安装 playwright: pip install playwright && playwright install chromium")

    print("[JWC-Browser] 启动浏览器...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        login_url = f"{_CAS_LOGIN_URL}?service={url_quote(_CAS_SERVICE, safe='')}"
        print(f"[JWC-Browser] 打开登录页: {login_url}")
        await page.goto(login_url, wait_until="domcontentloaded")

        print(f"[JWC-Browser] 请在浏览器中手动登录教务系统...")
        print(f"[JWC-Browser] 登录后课表自动检测 (超时 {timeout_seconds}s)...")

        import time as _time
        start = _time.monotonic()
        logged_in_notified = False
        while _time.monotonic() - start < timeout_seconds:
            url = page.url

            if "jsxsd" in url and not logged_in_notified:
                print(f"[JWC-Browser] 检测到已登录教务系统: {url}")
                logged_in_notified = True

            if "jsxsd" in url:
                try:
                    await page.wait_for_timeout(500)
                    has_table = await page.evaluate("""
                        () => {
                            const tables = document.querySelectorAll('table');
                            for (const t of tables) {
                                const text = t.textContent || '';
                                if (text.includes('节') && (text.includes('一') || text.includes('二') || text.includes('三'))) {
                                    return true;
                                }
                            }
                            const iframes = document.querySelectorAll('iframe');
                            for (const f of iframes) {
                                try {
                                    const doc = f.contentDocument || f.contentWindow.document;
                                    const iframeText = doc.body ? doc.body.textContent : '';
                                    if (iframeText.includes('节') && iframeText.includes('周')) {
                                        return true;
                                    }
                                } catch(e) {}
                            }
                            return false;
                        }
                    """)
                    if has_table:
                        print(f"[JWC-Browser] 检测到课表表格！URL: {url}")
                        await page.wait_for_load_state("networkidle", timeout=10000)

                        enriched = await _try_enrich_from_page(page)
                        if enriched:
                            await browser.close()
                            print(f"[JWC-Browser] 完成（含详情），解析到 {len(enriched)} 门课程")
                            return enriched

                        html = await page.content()
                        iframe_html = await page.evaluate("""
                            () => {
                                const iframes = document.querySelectorAll('iframe');
                                for (const f of iframes) {
                                    try {
                                        const doc = f.contentDocument || f.contentWindow.document;
                                        if (doc.body && doc.body.innerHTML.includes('节')) {
                                            return doc.documentElement.outerHTML;
                                        }
                                    } catch(e) {}
                                }
                                return '';
                            }
                        """)
                        await browser.close()
                        target_html = iframe_html if iframe_html else html
                        courses = parse_schedule_to_courses(target_html)
                        print(f"[JWC-Browser] 完成，解析到 {len(courses)} 门课程")
                        return courses
                except Exception:
                    pass

            await asyncio.sleep(1)

        await browser.close()
        raise RuntimeError(
            f"等待超时（{timeout_seconds}s），未检测到课表表格。"
            "请确认已登录教务并打开能看到课表的页面"
        )
