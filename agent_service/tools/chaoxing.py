import asyncio
import os
from datetime import datetime, timedelta

import httpx


# ============================================================
# 学习通模拟登录 + 课程列表抓取
# ============================================================
#
# 调用链:
#   fetch_chaoxing_tasks()
#     -> _login(client)                  模拟登录, 拿到 Cookie
#     -> _fetch_course_list(client)      获取课程列表
#     -> _format_result(courses)         拼成自然语言
#
# 作业列表抓取因学习通新增 enc 授权 Token（服务端按会话生成），
# 纯 HTTP 请求方式暂无法自动获取，待后续接入浏览器自动化后恢复。
#
# 代理配置:
#   如果校内网无法直连，在 .env 中设置 CHAOXING_PROXY=http://127.0.0.1:7890
# ============================================================


# ---- 常量 ----

LOGIN_URL = "https://passport2.chaoxing.com/fanyalogin"
COURSE_LIST_URL = "https://mooc1-api.chaoxing.com/mycourse/backclazzdata"

USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 12; Pixel 6) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Mobile Safari/537.36"
)

MAX_LOGIN_RETRIES = 3
RETRY_BACKOFF = 1.5  # 重试等待秒数（指数增长）


# ---- 对外接口 ----


async def fetch_chaoxing_tasks() -> str:
    """抓取学习通课程列表，返回自然语言描述"""
    username = os.getenv("CHAOXING_USERNAME", "")
    password = os.getenv("CHAOXING_PASSWORD", "")

    if not username or not password:
        return "学习通账号未配置（请在 .env 里填 CHAOXING_USERNAME 和 CHAOXING_PASSWORD）"

    # 诊断：检查隐藏的代理环境变量
    for var in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
        val = os.environ.get(var, "")
        if val:
            print(f"[学习通-诊断] 发现代理环境变量 {var}={val}")

    # 构建 transport，支持代理和连接调优
    proxy = os.getenv("CHAOXING_PROXY", "")
    transport_kwargs = _build_transport_kwargs(proxy)

    async with httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
        timeout=httpx.Timeout(15.0, connect=10.0),
        trust_env=False,  # 不读取系统 HTTP_PROXY 环境变量
        **transport_kwargs,
    ) as client:
        # 1. 登录（最多重试 MAX_LOGIN_RETRIES 次）
        ok = await _login_with_retry(client, username, password)
        if not ok:
            return "学习通登录失败，请检查账号密码"

        # 2. 获取课程列表
        courses = await _fetch_course_list(client)
        if courses is None:
            return "学习通课程列表获取失败"

        # 3. 拼成自然语言
        return _format_result(courses)


# ---- 传输层构建 ----


def _build_transport_kwargs(proxy: str) -> dict:
    """根据是否有代理，构建 httpx transport 参数"""
    kwargs: dict = {}

    if proxy:
        # 显式代理（http://127.0.0.1:7890 格式）
        try:
            transport = httpx.AsyncHTTPTransport(
                proxy=proxy,
                verify=False,           # 代理场景下可能涉及自签证书
                retries=1,
            )
            kwargs["transport"] = transport
            print(f"[学习通] 使用代理: {proxy}")
        except Exception as e:
            print(f"[学习通] 代理配置异常，回退直连: {e}")

    return kwargs


# ---- 登录（带重试） ----


async def _login_with_retry(
    client: httpx.AsyncClient, username: str, password: str
) -> bool:
    """登录，连接失败自动重试"""
    last_error = None

    for attempt in range(MAX_LOGIN_RETRIES):
        try:
            result = await _login(client, username, password)
            if result:
                return True
            # 登录返回了响应但 status != true（密码错误等），不重试
            return False
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            last_error = e
            if attempt < MAX_LOGIN_RETRIES - 1:
                wait = RETRY_BACKOFF * (2 ** attempt)
                print(f"[学习通] {type(e).__name__}，{wait:.1f}s 后重试 ({attempt + 2}/{MAX_LOGIN_RETRIES})...")
                await asyncio.sleep(wait)
        except httpx.RequestError as e:
            # 其他请求错误不重试（如 SSL 错误）
            print(f"[学习通] 登录请求异常: {e}")
            _print_diagnostic_hints(e)
            return False

    if last_error:
        print(f"[学习通] 登录请求异常（已重试 {MAX_LOGIN_RETRIES} 次仍失败）: {type(last_error).__name__}: {last_error}")
        _print_diagnostic_hints(last_error)

    return False


async def _login(client: httpx.AsyncClient, username: str, password: str) -> bool:
    """模拟登录学习通, 成功返回 True"""
    resp = await client.post(
        LOGIN_URL,
        data={
            "uname": username,
            "password": password,
            "t": "true",
        },
    )
    data = resp.json()
    if data.get("status") is True:
        return True

    msg = data.get("msg2", data.get("msg", "未知错误"))
    print(f"[学习通] 登录失败: {msg}")
    return False


def _print_diagnostic_hints(error: Exception) -> None:
    """打印连接问题的诊断建议"""
    error_str = str(error).lower()

    print("[学习通] 诊断建议：")
    if "name or service not known" in error_str or "getaddrinfo" in error_str:
        print("  → DNS 解析失败，检查网络连接或 DNS 设置")
    elif "connection refused" in error_str:
        print("  → 目标服务器拒绝连接，可能需要 VPN 或代理")
    elif "timeout" in error_str or "timed out" in error_str:
        print("  → 连接超时，服务器可能不可达，尝试设置 CHAOXING_PROXY 代理")
    elif "certificate" in error_str or "ssl" in error_str:
        print("  → SSL 证书问题，可以尝试关闭 VPN 或更换网络环境")
    elif "all connection attempts failed" in error_str:
        print("  → 所有连接尝试均失败，可能原因：")
        print("    1. 防火墙/杀软拦截了连接")
        print("    2. 需要代理（在 .env 中设置 CHAOXING_PROXY=http://127.0.0.1:7890）")
        print("    3. 学习通服务器暂时不可达（等待几分钟后重试）")
        print("    4. DNS 污染，尝试用 nslookup passport2.chaoxing.com 检查")


# ---- 课程列表 ----


async def _fetch_course_list(client: httpx.AsyncClient) -> list[dict] | None:
    """获取当前学期课程列表（过滤掉 3 个月前的旧课）"""
    try:
        resp = await client.get(COURSE_LIST_URL)
        data = resp.json()

        # 课表按时间倒序排列（最新的在前），遇到第一门旧课就停止
        cutoff = datetime(2026, 3, 1)

        channels = data.get("channelList", [])
        courses = []
        seen = set()

        for ch in channels:
            content = ch.get("content", {})
            begin_str = content.get("beginDate", "")

            # 有日期且早于 3 月的 = 旧课，之后的都跳过
            if begin_str and begin_str != "?":
                try:
                    begin_date = datetime.strptime(begin_str[:10], "%Y-%m-%d")
                    if begin_date < cutoff:
                        break  # 遇到旧课，后面都是更旧的
                except ValueError:
                    pass

            for item in content.get("course", {}).get("data", []):
                name = item.get("name", "未知课程")
                if name in seen:
                    continue
                seen.add(name)
                courses.append({
                    "course_id": item.get("id"),
                    "class_id": ch.get("key"),
                    "name": name,
                })

        return courses

    except httpx.RequestError as e:
        print(f"[学习通] 课程列表请求异常: {e}")
        return None
    except Exception as e:
        print(f"[学习通] 课程列表解析异常: {e}")
        return None


# ---- 结果拼装 ----


def _format_result(courses: list[dict]) -> str:
    """把课程列表拼成 LLM 能理解的自然语言"""
    lines = []

    if courses:
        course_names = "、".join(c["name"] for c in courses)
        lines.append(f"本学期课程（共 {len(courses)} 门）：{course_names}")
    else:
        lines.append("本学期暂无课程数据")

    lines.append("（作业列表暂不可用——学习通新增 enc 授权校验，待后续适配）")
    return "\n".join(lines)
