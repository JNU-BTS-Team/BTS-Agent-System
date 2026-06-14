# BTS-Agent启动脚本
param()

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "BTS-Agent 启动中..." -ForegroundColor Cyan
Write-Host ""

# 加载环境变量
$env:AGENT_PIPELINE = "multi"
$env:MULTI_AGENT_MODEL = "deepseek-chat"
$env:MULTI_AGENT_API_KEY = "sk-7d027c8543f246be85e73317e585bdf9"
$env:deepseek_base_url = "https://api.deepseek.com"
$env:MULTI_AGENT_STRATEGY = "debate"
$env:SINGLE_AGENT_MODEL = "deepseek-chat"
$env:SINGLE_AGENT_API_KEY = "sk-7d027c8543f246be85e73317e585bdf9"
$env:DLC_MYSQL_HOST = "localhost"
$env:DLC_MYSQL_USER = "root"
$env:DLC_MYSQL_PASSWORD = "wpw242512"
$env:DLC_MYSQL_DB = "SECD2"
$env:BTS_SSO_SECRET = "bts_sso_demo"
$env:BTS_LOGIN_TO_DLC = "1"

Write-Host "环境变量已设置" -ForegroundColor Green
Write-Host ""

Write-Host "访问地址:" -ForegroundColor Yellow
Write-Host "  http://127.0.0.1:5000/login" -ForegroundColor Cyan
Write-Host "  账号: admin" -ForegroundColor White
Write-Host "  密码: admin123" -ForegroundColor White
Write-Host ""
Write-Host "按任意键继续..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
Write-Host ""

# 启动应用
Write-Host "启动应用..." -ForegroundColor Cyan
powershell -NoExit -ExecutionPolicy Bypass -File ".\start_both.ps1"
