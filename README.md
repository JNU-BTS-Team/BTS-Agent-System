# 🧠 BTS-Agent：脑肿瘤诊断病例管理系统

**BTS-Agent: Brain Tumor Diagnosis Case Management System**

> 一个集医学影像诊断、多代理智能分析、患者病例管理于一体的脑肿瘤诊疗支持系统

---

## 📖 项目简介

本项目是一个集医学影像诊断、多代理智能分析、患者病例管理于一体的脑肿瘤诊疗支持系统。系统采用前后端分离架构，包含 **BTS_UI 主诊疗界面**和 **BTS_UI_DLC 数据管理模块**，支持医生团队协作、患者信息管理、诊断记录追踪等功能，并集成了多智能体辩论融合（Multi-Agent Debate Fusion）的诊断决策支持。

### ✨ 核心功能

- 🏥 **患者诊疗管理** - 患者信息注册、诊断记录管理、医学影像处理
- 🤖 **AI 辅助诊断** - 多智能体辩论融合、DeepSeek LLM 推理
- 👨‍⚕️ **医生团队协作** - 医生权限管理、诊断分工、团队统计
- 🔐 **权限安全控制** - 细粒度访问控制、敏感信息脱敏、视图保护
- 📊 **数据可视化** - 诊断统计、工作量分析、趋势展示

---

## 🚀 快速启动

### 1️⃣ 环境要求

```
✓ Windows 10/11 或 Linux
✓ Python 3.8+
✓ MySQL 5.7+
✓ 现代浏览器 (Chrome/Firefox/Edge)
```

### 2️⃣ 数据库准备

#### 启动 MySQL 服务
```bash
# Windows - 按 Win + R，输入以下命令
services.msc

# 或在 PowerShell 中运行
net start MySQL80
```

#### 导入数据库
```bash
# 进入数据库文件目录
cd BTS-Agent-System/only_sql_bench

# 依次执行初始化脚本
mysql -u root -p < 01_CREATE_DATABASE_AND_TABLES.sql
mysql -u root -p < 02_INSERT_INITIAL_DATA.sql
mysql -u root -p < 07_GRANT_PERMISSIONS.sql
```

#### 验证连接
```bash
mysql -u root -p
# 输入密码后，如果出现 mysql> 提示符即连接成功
```

### 3️⃣ 系统运行

在项目根目录打开 **PowerShell** 或 **CMD**，执行以下命令：

#### 方式一：使用启动脚本（推荐）✨
```powershell
powershell -ExecutionPolicy Bypass -File .\start_app.ps1
```

#### 方式二：手动启动
```powershell
# 启动模块一：主诊疗系统（端口 5000）
python BTS-Agent-System/BTS_UI/app.py

# 新开一个终端，启动模块二：数据管理系统（端口 5001）
python BTS-Agent-System/BTS_UI_DLC/app.py
```

### 4️⃣ 访问系统

在浏览器中打开以下地址：

| 系统模块 | 访问地址 | 描述 |
|---------|---------|------|
| 🔗 **主诊疗系统** | [http://127.0.0.1:5000/login](http://127.0.0.1:5000/login) | 患者诊断、AI 分析 |
| 🔗 **数据管理系统** | [http://127.0.0.1:5001/login](http://127.0.0.1:5001/login) | 医生团队、权限管理 |

### 5️⃣ 默认账户

```
👤 管理员账户
  用户名: admin
  密码: admin123

👨‍⚕️ 医生账户
  用户名: doctor1
  密码: doctor123

👁️ 审计员账户
  用户名: viewer
  密码: viewer123
```

---

## ⚙️ 环境变量配置

### 模块一：BTS_UI 主诊疗系统

```powershell
# MySQL 数据库配置
$env:MYSQL_HOST="localhost"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="修改为你的密码"
$env:MYSQL_DB="SECD"

# Flask Web 服务器配置
$env:FLASK_HOST="127.0.0.1"
$env:FLASK_PORT="5000"
$env:FLASK_DEBUG="0"

# 多智能体诊断系统配置
$env:MULTI_AGENT_STRATEGY="debate"     # debate / voting / confidence_fusion
$env:DEEPSEEK_API_KEY="你的API"
$env:DEEPSEEK_BASE_URL="你使用的URL"
$env:BTS_SSO_SECRET="bts_sso_demo"     # SSO 单点登录密钥
```

### 模块二：BTS_UI_DLC 数据管理系统

```powershell
# MySQL 数据库配置
$env:DLC_MYSQL_HOST="localhost"
$env:DLC_MYSQL_USER="root"
$env:DLC_MYSQL_PASSWORD="修改为你的密码"
$env:DLC_MYSQL_DB="SECD2"

# Flask 运行端口
$env:FLASK_RUN_PORT="5001"

# 远程执行配置（可选）
$env:REMOTE_HOST="10.125.125.2"
$env:REMOTE_PORT="22"
$env:REMOTE_USERNAME="your_username"
$env:REMOTE_PASSWORD="your_password"
```

---

## 📂 项目结构

```
BTS-Agent/
├── BTS-Agent-System/
│   ├── BTS_UI/                          # 主诊疗系统
│   │   ├── app.py                       # Flask 主应用
│   │   ├── init_db.sql                  # 数据库初始化
│   │   ├── templates/                   # HTML 模板
│   │   ├── static/                      # CSS/JS 静态资源
│   │   └── Multi-Agent/                 # 多智能体诊断模块
│   │
│   ├── BTS_UI_DLC/                      # 数据管理系统
│   │   ├── app.py                       # Flask 数据管理应用
│   │   ├── templates/                   # 管理界面模板
│   │   └── static/                      # 管理界面资源
│   │
│   └── only_sql_bench/                  # 数据库脚本
│       ├── 01_CREATE_DATABASE_AND_TABLES.sql
│       ├── 02_INSERT_INITIAL_DATA.sql
│       ├── 04_VIEW_PROTECTION.sql       # 视图脱敏
│       └── 07_GRANT_PERMISSIONS.sql     # 权限管理
│
├── start_app.ps1                        # Windows 启动脚本
├── start_both.ps1                       # 批量启动脚本
├── README.md                            # 本文件
└── QUICKSTART.md                        # 快速入门指南
```

---

## 🏗️ 系统架构

### 模块划分

| 模块 | 功能 | 端口 | 数据库 |
|------|------|------|--------|
| **BTS_UI** | 患者诊疗、AI 辅助分析、影像展示 | 5000 | SECD |
| **BTS_UI_DLC** | 医生团队管理、诊断记录、权限控制 | 5001 | SECD2 |

### 技术栈

```
🎨 前端：HTML5 + CSS3 + Vanilla JavaScript
🔧 后端：Python Flask
💾 数据库：MySQL 5.7+
🤖 AI：DeepSeek LLM + Multi-Agent Debate
🔐 认证：Flask-Login + Session
📡 通信：JSON + Fetch API
```

---

## 🔐 权限管理体系

### 用户角色与权限

| 角色 | 权限范围 | 可操作功能 |
|------|---------|---------|
| **管理员** (admin) | ✅ 全部 | 创建/编辑/删除医生、患者、诊断记录 |
| **医生** (doctor) | ✅ 受限 | 查看患者、创建诊断、无删除权限 |
| **审计员** (viewer) | ✅ 只读 | 仅查看患者和诊断信息 |

### 数据脱敏策略

- 📛 **姓名脱敏**：王** （只显示首字）
- 📞 **电话脱敏**：139****7919 （首尾可见）
- 🎂 **出生日期脱敏**：1990-** （只显示年份）
- 🏠 **住址脱敏**：北京市朝** （只显示前5个字符）

---

## 📖 常见问题

### ❓ 启动时出现数据库连接错误

**原因**：MySQL 服务未启动或密码错误

**解决**：
```powershell
# 1. 启动 MySQL 服务
net start MySQL80

# 2. 验证连接
mysql -u root -p
# 输入密码："你的密码"

# 3. 检查环境变量是否正确设置
echo $env:MYSQL_PASSWORD
```

### ❓ 端口 5000 已被占用

**原因**：之前的 Flask 实例未正常关闭

**解决**：
```powershell
# 查找占用端口的进程
netstat -ano | findstr :5000

# 关闭进程（PID 为上面查询到的进程ID）
taskkill /PID <PID> /F

# 重新启动
python BTS-Agent-System/BTS_UI/app.py
```

### ❓ 页面无法加载或样式混乱

**原因**：浏览器缓存或静态资源未加载

**解决**：
```
1. 按 Ctrl + Shift + Delete 清除浏览器缓存
2. 或按 Ctrl + Shift + R 强制刷新
3. 检查浏览器控制台（F12）是否有错误信息
```

---

## 📚 文档参考

- 📖 [快速入门指南](./QUICKSTART.md) - 5 分钟上手
- 🔐 [权限管理文档](./BTS-Agent-System/4.1_USER_PERMISSION_COMPLETE.md) - 用户权限系统说明
- 👁️ [视图保护文档](./BTS-Agent-System/4.2_VIEW_PROTECTION_GUIDE.md) - 数据脱敏与隐私保护
- ⚡ [API 接口文档](./BTS-Agent-System/API_REFERENCE.md) - 系统 API 调用

---

## 🛠️ 故障排查

### 日志查看

```powershell
# 查看 Flask 日志
python BTS-Agent-System/BTS_UI/app.py 2>&1 | Tee-Object -FilePath "debug.log"

# 查看数据库错误
mysql -u root -p
> SHOW ERRORS;
```

### 数据库检查

```sql
-- 检查用户权限
SHOW GRANTS FOR 'root'@'localhost';

-- 查看所有数据库
SHOW DATABASES;

-- 查看表结构
DESC SECD.users;
DESC SECD.patients;
```

---

## 👥 项目成员

- 🧑‍💼 项目负责人：吴佩威
---

## 📄 许可证

本项目仅供教学使用，禁止商业用途。

---

## 📞 技术支持

如有问题或建议，请联系项目负责人或提交 Issue。

```
最后更新：2026-06-14
版本：v1.1.2
```

---

**🚀 祝你使用愉快！**
