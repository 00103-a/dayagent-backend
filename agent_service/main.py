"""
DayAgent Agent service entrypoint.

Run:
    uvicorn agent_service.main:app --port 8000
"""

import asyncio
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI


if sys.platform == "win32":
    # Playwright needs the Proactor event loop on Windows.
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


def _load_env() -> None:
    """Load agent_service/.env before importing routers/tools."""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)


_load_env()

from agent_service.routers import (  # noqa: E402
    chaoxing,
    chat,
    courses,
    environment,
    news,
    plan,
    voice,
    weather,
)


_PROXY_ENV_VARS = [
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "NO_PROXY",
    "no_proxy",
]


def _clear_proxy_env() -> None:
    """Avoid accidental proxy usage from the host environment."""
    for var in _PROXY_ENV_VARS:
        if var in os.environ:
            value = os.environ.pop(var)
            print(f"[startup] cleared proxy env: {var}={value}")


def _startup_diagnostics_enabled() -> bool:
    value = os.getenv("STARTUP_DIAGNOSTICS", "true").lower()
    return value not in {"0", "false", "no"}


async def _diagnose_url(label: str, url: str) -> None:
    import httpx

    try:
        async with httpx.AsyncClient(timeout=5.0, trust_env=False) as client:
            response = await client.get(url)
            print(f"[startup diagnostic] {label} reachable: HTTP {response.status_code}")
    except Exception as exc:
        print(f"[startup diagnostic] {label} unreachable: {type(exc).__name__}: {exc}")


_clear_proxy_env()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup diagnostics and shutdown cleanup."""
    print(f"[startup] Python: {sys.executable}")
    print(f"[startup] Event loop: {type(asyncio.get_running_loop()).__name__}")

    if _startup_diagnostics_enabled():
        await _diagnose_url("DeepSeek", "https://api.deepseek.com/v1/models")
        await _diagnose_url("Chaoxing", "https://passport2.chaoxing.com")

    print("Agent Service started")
    yield

    try:
        from agent_service.tools.mysql_client import close_pool

        await close_pool()
    except Exception:
        pass


app = FastAPI(
    title="DayAgent Agent Service",
    description="Multi-source data collection and LLM planning generation",
    version="0.1.0",
    lifespan=lifespan,
)


for router_module in (
    plan,
    courses,
    weather,
    news,
    chaoxing,
    chat,
    environment,
    voice,
):
    app.include_router(router_module.router)


@app.get("/health")
async def health_check():
    """Health check endpoint used by Java and local diagnostics."""
    return {"status": "ok"}
