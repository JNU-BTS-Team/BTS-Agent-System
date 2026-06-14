# BTS-Agent 配置已完成！

## ✅ 已更新内容

1. **API 密钥已更新**
   - 旧密钥：`sk-7741c51d...`
   - 新密钥：`sk-7d027c8543f246be85e73317e585bdf9` ✓

2. **配置文件已更新**
   - `start_both.local.ps1` - 已更新为你的 API 密钥

3. **新增文件**
   - `QUICKSTART.md` - 详细启动指南
   - `init_env.py` - Python 数据库初始化脚本
   - `start_all.bat` - 一键启动脚本（Windows）

---

## 🚀 快速启动（3 步）

### 第 1 步：启动 MySQL
```powershell
Win + R → services.msc → 找到 MySQL80 → 右键启动
```

### 第 2 步：初始化数据库（仅首次）
```powershell
cd BTS-Agent-System
python init_env.py
```

### 第 3 步：运行应用
```powershell
powershell -ExecutionPolicy Bypass -File .\start_both.ps1
```

**或者直接使用一键启动：**
```
双击 start_all.bat
```

---

## 🌐 访问应用

| 系统 | 地址 | 说明 |
|------|------|------|
| **BTS_UI** | http://127.0.0.1:5000/login | 脑肿瘤诊断系统 |
| **DLC** | http://127.0.0.1:5001 | 数据管理系统 |

**默认账号**
- 用户名：`admin`
- 密码：`admin123`

---

## 🔧 当前配置

### 数据库
- **主机**：localhost
- **用户**：root
- **密码**：Hjk608866
- **数据库**：SECD2

### AI 模型
- **提供商**：DeepSeek
- **模型**：deepseek-chat
- **API 密钥**：sk-7d027c8543f246be85e73317e585bdf9
- **策略**：多代理辩论融合

---

## 📋 环境变量参考

```powershell
# 多代理配置
AGENT_PIPELINE=multi
MULTI_AGENT_MODEL=deepseek-chat
MULTI_AGENT_API_KEY=sk-7d027c8543f246be85e73317e585bdf9
MULTI_AGENT_STRATEGY=debate

# 数据库配置
DLC_MYSQL_HOST=localhost
DLC_MYSQL_USER=root
DLC_MYSQL_PASSWORD=Hjk608866
DLC_MYSQL_DB=SECD2
```

---

## 🆘 常见问题

**Q: 启动时提示"无法连接数据库"**
- A: 检查 MySQL 服务是否启动，运行 `net start MySQL80`

**Q: 密码错误**
- A: 确认使用的是 `Hjk608866` 而不是其他密码

**Q: 端口被占用**
- A: 运行 `netstat -ano | findstr :5000` 查看占用进程

**Q: 需要修改配置**
- A: 编辑 `start_both.local.ps1` 并重新运行启动脚本

---

## 📁 项目结构

```
BTS-Agent-System/
├── BTS_UI/                 # 诊断系统主模块
├── BTS_UI_DLC/             # 数据管理子模块
├── start_both.ps1          # 主启动脚本
├── start_both.local.ps1    # ✓ 已更新的配置
├── start_all.bat           # ✓ 新增一键启动
├── init_env.py             # ✓ 新增初始化脚本
├── QUICKSTART.md           # ✓ 新增详细指南
├── secd2.sql               # 数据库初始数据
└── README.md               # 项目文档
```

---

## ✨ 下一步

- [ ] 启动应用并访问登录页面
- [ ] 修改管理员密码
- [ ] 上传患者数据
- [ ] 配置远程推理（如需）
- [ ] 自定义诊断规则

---

**需要帮助？** 查看 `QUICKSTART.md` 了解详细步骤
