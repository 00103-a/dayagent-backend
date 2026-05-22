@echo off
REM ============================================
REM DayAgent - Python Agent 服务启动脚本
REM 注意：Windows 下不能用 --reload，否则 Playwright 子进程会失败
REM ============================================
cd /d "%~dp0agent_service"
echo Starting Python Agent Service on port 8000...
uvicorn agent_service.main:app --host 0.0.0.0 --port 8000 --loop asyncio
pause
