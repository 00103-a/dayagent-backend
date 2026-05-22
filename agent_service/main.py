"""
DayAgent - Agent 服务入口

启动方式：
    uvicorn agent_service.main:app --reload --port 8000
"""
import asyncio
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Windows 必须用 ProactorEventLoop，否则 Playwright 子进程无法启动
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from dotenv import load_dotenv

# 无论从哪个目录启动, 都正确找到 agent_service/.env
# 必须在 import routers 之前加载，否则 tools/news.py 等模块在
# 模块级读取 os.getenv() 时拿不到 .env 中的配置
load_dotenv(Path(__file__).parent / ".env")

from fastapi import FastAPI
from agent_service.routers import plan, courses, weather, news, chaoxing, chat

# ═════════════════════════════════════════════════════════════
# 防御：清除系统级代理环境变量，防止被 httpx/openai 等库自动读取
#
# Windows 上代理软件（Clash/V2RayN 等）常在系统/PowerShell profile 中设
# HTTP_PROXY / HTTPS_PROXY，httpx 默认 trust_env=True 会自动走这些代理。
# 一旦代理没启动，所有外部请求全部超时。
#
# 这里的策略：启动时直接干掉这些变量，DayAgent 只用自己 .env 里的
# CHAOXING_PROXY / LLM_PROXY 控制代理行为。
# ═════════════════════════════════════════════════════════════
_PROXY_ENV_VARS = [
    "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
    "http_proxy", "https_proxy", "all_proxy",
    "NO_PROXY", "no_proxy",
]
for _var in _PROXY_ENV_VARS:
    if _var in os.environ:
        print(f"[启动] 清除系统代理环境变量: {_var}={os.environ.pop(_var)}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭时的生命周期管理"""
    # 启动时自检连通性
    import httpx
    print(f"[启动诊断] Python: {sys.executable}")
    print(f"[启动诊断] Event loop: {type(asyncio.get_running_loop()).__name__}")
    try:
        async with httpx.AsyncClient(timeout=5.0, trust_env=False) as c:
            r = await c.get("https://api.deepseek.com/v1/models")
            print(f"[启动诊断] DeepSeek 连通: HTTP {r.status_code}")
    except Exception as e:
        print(f"[启动诊断] DeepSeek 不通: {type(e).__name__}: {e}")
    try:
        async with httpx.AsyncClient(timeout=5.0, trust_env=False) as c:
            r = await c.get("https://passport2.chaoxing.com")
            print(f"[启动诊断] 学习通 连通: HTTP {r.status_code}")
    except Exception as e:
        print(f"[启动诊断] 学习通 不通: {type(e).__name__}: {e}")
    print("Agent Service 启动成功")
    yield
    # 关闭 MySQL 连接池
    try:
        from agent_service.tools.mysql_client import close_pool
        await close_pool()
    except Exception:
        pass


app = FastAPI(
    title="DayAgent Agent Service",
    description="多源数据采集 + LLM 规划生成",
    version="0.1.0",
    lifespan=lifespan,
)

# 注册路由
app.include_router(plan.router)
app.include_router(courses.router)
app.include_router(weather.router)
app.include_router(news.router)
app.include_router(chaoxing.router)
app.include_router(chat.router)


@app.get("/health")
async def health_check():
    """健康检查接口，Java 端会定时探测"""
    return {"status": "ok"}
