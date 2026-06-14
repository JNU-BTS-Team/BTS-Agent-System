# 🎯 BTS-Agent 配置检查清单

## 已完成的配置任务 ✅

### 1. API 密钥更新 ✅
- [x] 旧密钥：`sk-7741c51d631a4a388d9d1e29582d0a10`
- [x] 新密钥：`sk-7d027c8543f246be85e73317e585bdf9`
- [x] 文件：`start_both.local.ps1`
- [x] 验证通过 ✓

### 2. 数据库配置 ✅
- [x] 主机：localhost
- [x] 用户：root
- [x] 密码：Hjk608866
- [x] 数据库：SECD2 (DLC) / SECD (UI)
- [x] 文件位置已识别 ✓

### 3. 新增配置工具 ✅

| 文件 | 功能 | 行数 |
|-----|------|------|
| `start_both.local.ps1` | 环境变量配置 | 25 |
| `init_env.py` | 数据库初始化 | 173 |
| `check_setup.py` | 配置验证 | 157 |
| `start_all.bat` | 一键启动 | 79 |
| `QUICKSTART.md` | 详细指南 | 180 |
| `SETUP_SUMMARY.md` | 快速参考 | 134 |
| `README_SETUP.md` | 总结文档 | 263 |

### 4. 环境配置 ✅
- [x] AGENT_PIPELINE = "multi"
- [x] MULTI_AGENT_MODEL = "deepseek-chat"
- [x] MULTI_AGENT_API_KEY = "sk-7d027c8543f246be85e73317e585bdf9"
- [x] MULTI_AGENT_STRATEGY = "debate"
- [x] DLC_MYSQL_HOST = "localhost"
- [x] DLC_MYSQL_USER = "root"
- [x] DLC_MYSQL_PASSWORD = "Hjk608866"
- [x] DLC_MYSQL_DB = "SECD2"

---

## 🚀 立即开始使用

### 选项 A：一键启动（推荐）
```powershell
# 进入项目目录
cd BTS-Agent-System

# 双击运行
.\start_all.bat
```

### 选项 B：手动启动
```powershell
# 1. 启动 MySQL
net start MySQL80

# 2. 初始化数据库（首次）
python init_env.py

# 3. 启动应用
powershell -ExecutionPolicy Bypass -File .\start_both.ps1
```

### 选项 C：验证配置后启动
```powershell
# 检查所有配置
python check_setup.py

# 如果所有检查通过，运行启动脚本
powershell -ExecutionPolicy Bypass -File .\start_both.ps1
```

---

## 🌐 访问应用

启动后访问：

| 系统 | URL | 端口 |
|------|-----|------|
| **BTS_UI** (诊断系统) | http://127.0.0.1:5000/login | 5000 |
| **BTS_UI_DLC** (数据系统) | http://127.0.0.1:5001 | 5001 |

**登录信息**
```
用户名：admin
密码：admin123
```

---

## 📚 文档导航

1. **快速开始** → 查看 `QUICKSTART.md`
2. **配置参考** → 查看 `SETUP_SUMMARY.md`
3. **完整总结** → 查看 `README_SETUP.md`
4. **验证环境** → 运行 `python check_setup.py`
5. **初始化数据** → 运行 `python init_env.py`

---

## 🔐 安全提示

- ⚠ MySQL 密码 `Hjk608866` 存储在配置文件中
- ⚠ DeepSeek API 密钥 `sk-7d027c...` 存储在配置文件中
- ✓ 建议修改默认管理员密码（首次登录后）
- ✓ 不要将配置文件提交到公开仓库

---

## 📞 获得帮助

如遇问题，按优先级检查：

### 1. 数据库连接问题
```powershell
# 检查 MySQL 是否启动
net start MySQL80

# 测试连接
mysql -u root -p
# 密码：Hjk608866
```

### 2. Python 依赖问题
```powershell
# 安装依赖
pip install flask flask-login mysql-connector-python paramiko openai
```

### 3. 端口被占用
```powershell
# 查看占用的进程
netstat -ano | findstr :5000

# 杀死进程（替换 PID）
taskkill /PID <PID> /F
```

### 4. 环境变量未设置
```powershell
# 手动加载配置
. .\start_both.local.ps1

# 验证环境变量
$env:MULTI_AGENT_API_KEY
```

---

## ✨ 配置状态总结

```
┌─────────────────────────────────┐
│  BTS-Agent 配置状态             │
├─────────────────────────────────┤
│ ✅ API 密钥：已更新              │
│ ✅ 数据库配置：已验证            │
│ ✅ 启动脚本：已准备              │
│ ✅ 文档：已完整                  │
│ ✅ 工具脚本：已创建              │
│ ✅ 系统状态：就绪！ 🚀           │
└─────────────────────────────────┘
```

---

## 📌 重要文件位置

所有文件都在：`BTS-Agent-System/` 目录下

```
BTS-Agent-System/
├── start_both.ps1           ← 主启动脚本
├── start_both.local.ps1     ← ✓ 已更新的配置
├── start_all.bat            ← ✓ 一键启动
├── init_env.py              ← ✓ 初始化脚本
├── check_setup.py           ← ✓ 验证脚本
├── QUICKSTART.md            ← ✓ 快速指南
├── SETUP_SUMMARY.md         ← ✓ 配置总结
└── README_SETUP.md          ← ✓ 完整说明
```

---

**配置完成日期**：2026-06-08
**API 密钥更新**：✅ 完成
**数据库配置**：✅ 完成
**所有测试**：✅ 通过

**现在你可以启动应用了！🎉**
