@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM 进入脚本所在目录
cd /d "%~dp0"

echo ================================================
echo BTS-Agent 系统初始化
echo ================================================
echo.
echo 工作目录: %cd%
echo.

REM 检查是否以管理员身份运行
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 此脚本需要以管理员身份运行
    echo 请右键点击此文件，选择"以管理员身份运行"
    echo.
    pause
    exit /b 1
)

REM 启动 MySQL 服务
echo [INFO] 正在启动 MySQL 服务...
net start MySQL80 >nul 2>&1
if %errorlevel% equ 0 (
    echo [成功] MySQL 服务已启动
) else (
    echo [警告] MySQL 服务已在运行或启动失败
)
echo.

REM 检查 Python
echo [INFO] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Python 未找到或不在 PATH 中
    pause
    exit /b 1
)
echo [成功] Python 已安装
echo.

REM 设置环境变量
echo [INFO] 设置环境变量...
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
echo [成功] 环境变量已设置
echo.

REM 初始化数据库
echo [INFO] 初始化数据库...
python init_env.py
if %errorlevel% neq 0 (
    echo [警告] 数据库初始化异常，继续启动...
)
echo.

REM 启动应用
echo [INFO] 启动 BTS-Agent 应用...
echo.
echo 启动中：
echo   - UI 系统: http://127.0.0.1:5000/login
echo   - DLC 系统: http://127.0.0.1:5001
echo.
echo 按 Ctrl+C 停止应用
echo.

powershell -NoExit -ExecutionPolicy Bypass -File "%cd%\start_both.ps1"

pause
