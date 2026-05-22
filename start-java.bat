@echo off
REM ============================================
REM DayAgent - Java 业务层启动脚本
REM 需要：MySQL 8 已启动 + Maven 已安装
REM ============================================
cd /d "%~dp0business-service"
echo Starting Java Spring Boot on port 8080...
mvn spring-boot:run
pause
