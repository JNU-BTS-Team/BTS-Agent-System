# BTS-Agent 快速启动指南

## 前置准备

### 1. 启动 MySQL 数据库服务

#### Windows 系统启动 MySQL：
```powershell
# 方法一：通过服务管理器
Win + R → services.msc → 找到 MySQL 服务 → 右键启动

# 方法二：通过 PowerShell（需要管理员权限）
net start MySQL80  # 根据实际版本调整
```

#### 验证 MySQL 连接：
```bash
mysql -u root -p
# 输入密码后，如果显示 mysql> 提示符表示成功
```

---

## 第一次初始化（仅需一次）

### 2. 初始化数据库

进入项目根目录（`BTS-Agent-System` 文件夹），运行：

```powershell
python BTS_UI_DLC\setup_database.py
```

这会：
- 导入 `secd2.sql` 和 `current_data.sql`
- 创建必要的表和数据
- 验证数据库连接

**如果提示权限不足**，请检查：
- MySQL 用户名：`root`
- MySQL 密码：`Hjk608866`
- 数据库名：`SECD2`（DLC模块）或 `SECD`（UI模块）

---

## 启动应用

### 3. 运行启动脚本

在项目根目录（`BTS-Agent-System`）执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\start_both.ps1
```

这会启动两个应用：
- **BTS_UI**：`http://127.0.0.1:5000/login` - 脑肿瘤诊断系统
- **BTS_UI_DLC**：`http://127.0.0.1:5001` - 数据管理系统

---

## 访问应用

### 4. 打开浏览器

#### BTS_UI（主系统）
```
http://127.0.0.1:5000/login
```

**默认账号**：
- 用户名：`admin`
- 密码：`admin123`

#### BTS_UI_DLC（数据管理）
```
http://127.0.0.1:5001
```

---

## 环境配置详情

配置文件位置：`start_both.local.ps1`

### 模块一：Multi-Agent Pipeline
```powershell
$env:AGENT_PIPELINE = "multi"                    # 多代理管道
$env:MULTI_AGENT_MODEL = "deepseek-chat"        # 模型
$env:MULTI_AGENT_API_KEY = "sk-7d0..."          # API密钥
$env:deepseek_base_url = "https://api.deepseek.com"  # API地址
$env:MULTI_AGENT_STRATEGY = "debate"            # 融合策略
```

### 模块二：DLC 数据库配置
```powershell
$env:DLC_MYSQL_HOST = "localhost"        # 数据库主机
$env:DLC_MYSQL_USER = "root"             # 用户名
$env:DLC_MYSQL_PASSWORD = "Hjk608866"    # 密码
$env:DLC_MYSQL_DB = "SECD2"              # 数据库名
```

---

## 故障排查

### 问题：无法连接数据库
```
解决方案：
1. 检查 MySQL 服务是否启动
2. 验证数据库密码是否正确
3. 运行：mysql -u root -p Hjk608866
```

### 问题：Python 找不到模块
```powershell
解决方案：
# 安装依赖
pip install flask flask-login mysql-connector-python paramiko
```

### 问题：端口被占用
```powershell
解决方案：
# 查看占用 5000 端口的进程
netstat -ano | findstr :5000
# 杀死进程（替换 PID）
taskkill /PID <PID> /F
```

### 问题：权限不足错误
```powershell
解决方案：
# 使用管理员身份运行 PowerShell
# 然后重新执行脚本
```

---

## 项目结构

```
BTS-Agent-System/
├── BTS_UI/              # 脑肿瘤诊断系统前端
├── BTS_UI_DLC/          # 数据管理系统
├── start_both.ps1       # 启动脚本
├── start_both.local.ps1 # 本地配置（已更新）
├── secd.sql             # 数据库初始化
├── secd2.sql            # 备用数据
└── QUICKSTART.md        # 本文件
```

---

## 快速命令参考

```powershell
# 启动应用
.\start_both.ps1

# 测试数据库连接
python -c "import mysql.connector; mysql.connector.connect(host='localhost', user='root', password='Hjk608866', database='SECD2')"

# 查看日志（如有异常）
Get-Content BTS_UI\app.log  # 需要应用配置日志输出

# 停止应用
# 在 PowerShell 窗口中按 Ctrl+C
```

---

## 下一步

- 修改账户密码
- 上传患者数据
- 配置远程推理服务（如需要）
- 自定义诊断规则

详见各模块的 README 文档。
