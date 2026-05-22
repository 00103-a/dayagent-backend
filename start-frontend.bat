@echo off
REM ============================================
REM DayAgent - 前端开发服务器启动脚本
REM ============================================
cd /d "%~dp0frontend"
echo Starting Vite Dev Server on port 3000...
call npm run dev
pause
