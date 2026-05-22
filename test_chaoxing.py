from dotenv import load_dotenv 
from pathlib import Path 
load_dotenv(Path("agent_service/main.py").parent / ".env") 
import asyncio 
from agent_service.tools.chaoxing import fetch_chaoxing_tasks 
print(asyncio.run(fetch_chaoxing_tasks())) 
