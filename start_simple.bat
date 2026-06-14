@echo off
REM BTS-Agent 快速启动脚本（简化版）
chcp 65001 >nul
setlocal enabledelayedexpansion

REM 进入脚本所在目录
cd /d "%~dp0"

echo.
echo ╔════════════════════════════════════════════╗
echo ║     BTS-Agent 系统快速启动                 ║
echo ╚════════════════════════════════════════════╝
echo.

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ Python 未找到，请检查 Python 是否已安装
    pause
    exit /b 1
)

REM 设置环境变量
set "AGENT_PIPELINE=multi"
set "MULTI_AGENT_MODEL=deepseek-chat"
set "MULTI_AGENT_API_KEY=sk-7d027c8543f246be85e73317e585bdf9"
set "deepseek_base_url=https://api.deepseek.com"
set "MULTI_AGENT_STRATEGY=debate"
set "SINGLE_AGENT_MODEL=deepseek-chat"
set "SINGLE_AGENT_API_KEY=sk-7d027c8543f246be85e73317e585bdf9"
set "DLC_MYSQL_HOST=localhost"
set "DLC_MYSQL_USER=root"
set "DLC_MYSQL_PASSWORD=wpw242512"
set "DLC_MYSQL_DB=SECD2"
set "BTS_SSO_SECRET=bts_sso_demo"
set "BTS_LOGIN_TO_DLC=1"

echo ✓ 环境变量已设置
echo.

REM 提示用户
echo 准备启动应用...
echo.
echo 应用启动后访问：
echo   ★ 诊断系统：http://127.0.0.1:5000/login
echo   ★ 数据系统：http://127.0.0.1:5001
echo.
echo 默认账号：admin / admin123
echo.
echo 按任意键继续...
pause >nul

REM 启动应用
powershell -NoExit -ExecutionPolicy Bypass -Command "cd '%cd%'; . '.\start_both.ps1'"
