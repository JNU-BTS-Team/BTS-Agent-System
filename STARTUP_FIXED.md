# 🚀 BTS-Agent 启动问题已解决

## 问题分析

你之前运行 `start_all.bat` 时出现的错误：
```
python: can't open file 'C:\\Windows\\System32\\init_env.py'
The argument 'start_both.ps1' to the -File parameter does not exist
```

**原因**：脚本在 `System32` 目录运行，而不是项目目录，导致找不到文件。

---

## ✅ 解决方案

我为你创建了 **3 个可靠的启动脚本**，选择其中任意一个即可：

### 方式 1️⃣：PowerShell 脚本（推荐）✓ 最可靠

**文件**：`start_app.ps1`

**运行方式**：
```powershell
# 在 PowerShell 中运行
powershell -ExecutionPolicy Bypass -File .\start_app.ps1

# 或者右键点击文件 → "使用 PowerShell 运行"
```

**优点**：
- ✓ 自动检查 MySQL 服务
- ✓ 清晰的进度提示
- ✓ 在独立窗口启动两个应用
- ✓ 最稳定可靠

---

### 方式 2️⃣：简化批处理脚本

**文件**：`start_simple.bat`

**运行方式**：
```
双击 start_simple.bat
```

**优点**：
- ✓ 最简单快速
- ✓ 自动设置工作目录
- ✓ 修复了之前的路径问题

---

### 方式 3️⃣：手动启动（完全控制）

如果上面两个方法有问题，可以手动启动：

```powershell
# 1. 打开 PowerShell 并进入项目目录
cd "f:\Undergraduate_Competitions\Computer_Design_Competition\BTS-Agent\BTS-Agent-System"

# 2. 加载环境变量
. .\start_both.local.ps1

# 3. 启动应用
powershell -ExecutionPolicy Bypass -File .\start_both.ps1
```

---

## 🎯 推荐使用（最简单）

**现在就试试这个**：
```powershell
powershell -ExecutionPolicy Bypass -File .\start_app.ps1
```

或者在 PowerShell 中复制粘贴这一行：
```powershell
cd 'f:\Undergraduate_Competitions\Computer_Design_Competition\BTS-Agent\BTS-Agent-System'; powershell -ExecutionPolicy Bypass -File .\start_app.ps1
```

---

## 📋 应用启动后

**应该看到的现象**：
1. ✓ 两个新的 PowerShell 窗口打开
2. ✓ 窗口显示 Flask 应用启动信息
3. ✓ 可以访问应用

**访问地址**：
- 诊断系统：http://127.0.0.1:5000/login
- 数据系统：http://127.0.0.1:5001

**默认账户**：
- 用户名：admin
- 密码：admin123

---

## 🔧 故障排查

### 如果仍然出现错误

**错误 1**：PowerShell 执行策略问题
```powershell
# 解决：在 PowerShell 中运行
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser
```

**错误 2**：MySQL 连接失败
```powershell
# 启动 MySQL 服务
net start MySQL80

# 或者在任务管理器中手动启动 MySQL80 服务
```

**错误 3**：Python 找不到
```powershell
# 检查 Python 是否在 PATH 中
python --version

# 如果没有，需要将 Python 添加到 PATH
```

**错误 4**：端口被占用
```powershell
# 查看占用 5000 端口的进程
netstat -ano | findstr :5000

# 杀死该进程（替换 <PID>）
taskkill /PID <PID> /F
```

---

## 📁 所有启动脚本

```
BTS-Agent-System/
├── start_app.ps1          ✓ 推荐 - PowerShell 版
├── start_simple.bat       ✓ 简单 - 批处理版
├── start_all.bat          ✓ 已修复
├── start_both.ps1         - 原始启动脚本
└── start_both.local.ps1   - 环境变量配置
```

---

## ✨ 现在就开始

**最快的方式**（复制粘贴到 PowerShell）：

```powershell
cd 'f:\Undergraduate_Competitions\Computer_Design_Competition\BTS-Agent\BTS-Agent-System'; powershell -ExecutionPolicy Bypass -File .\start_app.ps1
```

**或者更简单**（如果你已经在项目目录）：

```powershell
powershell -ExecutionPolicy Bypass -File .\start_app.ps1
```

---

**问题已解决！请尝试上述任一方法启动应用。** 🎉
