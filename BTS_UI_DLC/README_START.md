# 肿瘤病例管理系统启动说明

这个包包含当前项目文件和当前 `SECD` 数据库快照 `current_data.sql`。在另一台电脑上初始化后，数据库内容会恢复为打包时的状态，页面数据会尽量和当前电脑保持一致。

## 环境要求

- Windows 10/11
- Python 3.10 或更高版本
- MySQL 8.0

## 第一次启动

1. 解压本项目压缩包。
2. 进入解压后的项目文件夹。
3. 双击 `init_database.bat` 初始化数据库。
   - 默认会用 MySQL `root` 用户连接。
   - 如果 root 密码不是空，脚本会提示输入。
   - 初始化后会创建数据库 `SECD`、应用账号 `appuser / 123456`，并导入 `current_data.sql`。
4. 双击 `start_windows.bat` 启动网站。
5. 浏览器打开：

```text
http://127.0.0.1:5000/login
```

## 当前数据快照

`current_data.sql` 包含当前数据库中的：

- 用户和医生账号
- 病人数据
- 诊断记录
- 待办任务
- 通知数据

注意：上传图片文件在 `static/uploaded_images/` 中，已随包一起复制。

## 默认账号

```text
用户名：admin
密码：admin123
```

医生账号通常为：

```text
用户名：doctor1、doctor2、...
密码：123456
```

## 手动命令

如果不使用 bat 文件，也可以在 PowerShell 中执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe setup_database.py
.\.venv\Scripts\python.exe app.py
```

## 注意

- 数据库连接配置在 `app.py` 开头：`localhost / appuser / 123456 / SECD`。
- `/` 根路径没有页面，请访问 `/login`。
- 远程推理功能依赖目标 SSH 服务器，普通本地演示不需要配置。
