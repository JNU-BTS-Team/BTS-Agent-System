# 模块一环境配置 - Multi Agent Pipeline
$env:AGENT_PIPELINE = "multi"
$env:MULTI_AGENT_MODEL = "deepseek-chat"
$env:MULTI_AGENT_API_KEY = "sk-7d027c8543f246be85e73317e585bdf9"
$env:deepseek_base_url = "https://api.deepseek.com"
$env:MULTI_AGENT_STRATEGY = "debate"

$env:SINGLE_AGENT_MODEL = "deepseek-chat"
$env:SINGLE_AGENT_API_KEY = "sk-7d027c8543f246be85e73317e585bdf9"

# 远程执行配置（可选）
$env:REMOTE_HOST = "10.125.125.2"
$env:REMOTE_PORT = "22"
$env:REMOTE_USERNAME = "wpw"
$env:REMOTE_PASSWORD = "123456"

# 模块二环境配置 - DLC MySQL 数据库
$env:DLC_MYSQL_HOST = "localhost"
$env:DLC_MYSQL_USER = "root"
$env:DLC_MYSQL_PASSWORD = "wpw242512"
$env:DLC_MYSQL_DB = "SECD2"

# SSO 配置
$env:BTS_SSO_SECRET = "bts_sso_demo"
$env:BTS_LOGIN_TO_DLC = "1"
