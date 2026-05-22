import os, httpx, asyncio
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path("agent_service/main.py").parent / ".env")

async def t():
    c = httpx.AsyncClient(timeout=15)
    r = await c.get(
        os.getenv("LLM_BASE_URL") + "/v1/models",
        headers={"Authorization": "Bearer " + os.getenv("LLM_API_KEY")},
    )
    print(r.status_code)

asyncio.run(t())
