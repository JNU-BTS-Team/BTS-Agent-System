# 弥影智析：面向缺失模态的脑肿瘤 MRI 智能体分析与管理系统 
**Miying Intelligence: Intelligent Agent Analysis and Management System for Brain Tumor MRI with Missing Modalities**

## 📖 项目简介
本项目是一个基于多智能体（Multi-Agent）架构的脑肿瘤 MRI 智能分析与管理系统，专为解决临床真实场景中常见的“影像模态缺失”问题而设计。系统集成了 3D 医学影像处理、大语言模型（LLM）推理与临床数据管理功能。

## 🚀 快速启动

### 1. 数据库准备
1. **导入数据**：将 `MySQL数据库` 文件夹中的 `secd.sql` 文件导入本地 MySQL 数据库。
2. **启动服务**：按 `Win + R`，输入 `services.msc`，找到并启动 **MySQL** 服务。
3. **验证登录**：在终端执行以下命令，输入密码后显示 `welcome` 即为正常：
   ```bash
   mysql -u root -p
2. 环境配置与系统运行
在项目根目录终端执行以下命令（以 PowerShell 为例）：

PowerShell
# 指定 Python 解释器路径
$env:BTS_PYTHON="C:\Users\26013\python-sdk\python3.13.2\python.exe"

### 运行平台启动脚本
powershell -ExecutionPolicy Bypass -File .\start_both.ps1
3. 访问系统
在浏览器中打开以下地址即可使用系统：
🔗 http://127.0.0.1:5000/login

⚙️ 环境变量配置参考
在部署或调试时，需确保以下环境变量配置正确：

模块一：智能体分析模块 (Multi-Agent System)
PowerShell
### Agent Core
$env:AGENT_PIPELINE="multi"
$env:MULTI_AGENT_MODEL="deepseek-chat"
$env:MULTI_AGENT_API_KEY="sk-7741c51d631a4a388d9d1e29582d0a10"
$env:deepseek_base_url="[https://api.deepseek.com](https://api.deepseek.com)"
$env:MULTI_AGENT_STRATEGY="debate"

### Single Agent Backup
$env:SINGLE_AGENT_MODEL="deepseek-chat"
$env:SINGLE_AGENT_API_KEY="sk-7741c51d631a4a388d9d1e29582d0a10"

### Flask Web Server
$env:FLASK_HOST="0.0.0.0"
$env:FLASK_PORT="5000"
$env:FLASK_DEBUG="0"

### Remote Execution
$env:REMOTE_HOST="10.125.125.2"
$env:REMOTE_PORT="22"
$env:REMOTE_USERNAME="wpw"
$env:REMOTE_PASSWORD="123456"
模块二：数据管理与基础服务 (Data Management)
PowerShell
### Database Config
$env:DLC_MYSQL_HOST="localhost"
$env:DLC_MYSQL_USER="root"
$env:DLC_MYSQL_PASSWORD="Hjk608866"
$env:DLC_MYSQL_DB="SECD2"

### Flask Run Port
$env:FLASK_RUN_PORT="5001"
