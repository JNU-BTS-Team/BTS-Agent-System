# BTS Agent System

**A Flask‑based tumor case management and remote testing platform**

本项目面向 `Computer Design Competition 2026`，构建了一套
集成化的后台平台，用于肿瘤病例的管理、远程算法评估与运行结果的
可视化分析。系统不仅支持患者与医生信息、诊断记录的CRUD操作，
还通过 Web 界面接收 `.nii` 格式的影像数据，借助 SSH 与服务器
交互完成模型推理。远程生成的分割/预测图像会回传并嵌入页面，
后续还可接入经过微调的深度模型对输出进行自动化后处理与智能
建议，助力临床决策与科研验证。

---


### Chapter1 Git 常用命令速查（本地 ↔ GitHub）

> 进入项目目录后再执行下面命令：
>
> ```bash
> cd "F:\Undergraduate_Competitions\Computer_Design_Competition\code\BTS_Agent_System" # 本地的项目代码文件夹
> ```
>
> 1) 查看当前状态（最常用）
> ```bash
> git status              # 看哪些文件被修改/新增、是否已暂存、当前在哪个分支。
> git remote -v           # 查看已连接的远程仓库
> ```

2) 查看当前分支 & 远程仓库地址
git branch
git branch -a

3) 从 GitHub 拉取最新代码（更新到本地）
git pull
建议：每次开始写代码前先 git pull，避免冲突。0

4) 提交并推送（把本地改动上传到 GitHub）
4.1 暂存（选择一种）
只提交某个文件：0
git add README.md
提交所有改动（常用）：
git add .

4.2 提交
git commit -m "你的提交说明"

4.3 推送到 GitHub
git push
如果是第一次推送、提示没有 upstream：
main 分支：
git push -u origin main


5) 查看提交记录
git log --oneline --decorate --graph -n 20

6) 本地改乱了但还没提交：临时保存 / 恢复

```bash
# 6.1 临时保存改动（stash）
git stash
git pull
git stash pop

# 6.2 丢弃某个文件的本地修改（危险：不可恢复）
git restore README.md

# 6.3 丢弃全部未提交修改（危险：不可恢复）
git restore .
```

7) 典型日常流程（推荐）
从GitHub更新拉取代码：
git pull
或者
git fetch upstream # 从主仓库同步更新
git merge upstream/main

查看git状态：
git status
暂存(add) + 提交(commit) + 推送(push)

标准工作推送代码流程：
🟢 日常开发
git add .
git commit -m "你的更新说明"
git push origin main

🔵 同步主仓库更新（非常重要）
git fetch upstream
git merge upstream/main
# 这两和合并＝git pull
或者更干净：
git fetch upstream
git rebase upstream/main
git push origin main



### Chapter2 三种仓库 & 各自分支结构 重要！！！！！！！

# ===============================
# 1️⃣ 组织远程仓库（upstream）
# ===============================
# 位置：BTS-JNU/BTS-Agent-System
# 作用：团队最终代码

upstream/main    # 稳定版本（发布）
upstream/dev     # 团队开发分支


# ===============================
# 2️⃣ 个人远程仓库（origin）
# ===============================
# 位置：自己的GitHub账号/BTS-Agent-System
# 作用：个人开发中转站

origin/main          # 与 upstream/main 同步
origin/dev           # 与 upstream/dev 同步
origin/feature-xxx   # 个人功能分支


# ===============================
# 3️⃣ 个人本地仓库（Local）
# ===============================
# 位置：自己电脑
# 作用：实际写代码的地方

main                 # 本地主分支
dev                  # 本地开发分支
feature-xxx          # 本地功能分支



### Chapter3 团队协作标准流程（Fork + dev 分支） 非常重要！！！！！！！

## 结构说明
- upstream = 组织远程仓库
- origin = 个人远程仓库
- dev = 团队开发分支
- feature = 个人功能分支

# ===============================
# 0、首先点一下fork到自己的个人仓库中
# ===============================


# ===============================
# 一、开始开发前（同步 dev）
# ===============================

```bash
# 1. 切换到本地 dev 分支
git checkout dev

# 2. 从组织仓库下载最新代码（不修改当前代码）
git fetch upstream

# 3. 合并组织仓库的 dev 到本地 dev
git merge upstream/dev

# 4. 将更新后的 dev 推送到个人仓库
git push origin dev

# 5. 创建个人功能分支（不要在 dev 上直接开发）
git checkout -b feature-xxx
```


# ===============================
# 二、开发完成后
# ===============================

# 6. 添加修改
git add . # 作用在当前所在分支/个人本地仓库 （git branch可知）

# 7. 提交到本地功能分支
git commit -m "中文说明" # 作用在当前所在分支/个人本地仓库 （git branch可知）

# 8. 推送到个人仓库
git push origin feature-xxx # 作用在当前分支/个人本地仓库 → 远程对应分支/个人远程仓库

# 9. 在 GitHub 发起 PR：
#    feature-xxx  →  upstream/dev


# ===============================
# 三、PR 合并成功后
# ===============================

# 10. 切回本地 dev
git checkout dev

# 11. 同步组织仓库最新 dev
git fetch upstream
git merge upstream/dev

# 12. 更新个人仓库 dev
git push origin dev

# 13. 删除本地功能分支
git branch -d feature-xxx

# 14. 删除远程功能分支

---

## 远程测试与数据上传 ⚙️

1. 在系统导航栏点击“测试功能”进入远程服务器测试页面。
2. 在页面顶部先选择要上传的序列类型（FLAIR、T1、T1ce、T2），至少选一种。
3. 拖放或点击上传对应数量的 `.nii` 文件（文件数必须等于选中的类型数）。
   - 如果文件数缺少会提示“请继续输入文件”，多余则提示“当前上传文件数目过多”。
4. 上传按钮成功后右侧显示绿色“上传成功”，同时“开始测试”按钮被激活。
5. 必须先上传数据才能点击“开始测试”，否则页面会显示“远程Uploads目录没有nii文件，请先上传”。
6. 后端会通过 SSH 将上传的 `.nii` 文件发送到远程服务器的
   `/data/WPW/BTS-Agent-Sys/BTS/Uploads/Brats18_TCIA01_1_1/`，测试脚本运行时会使用这些数据。
7. 上传和测试均需登录用户权限。

上传测试也已包含在自动页面访问脚本中，脚本会验证接口是否能返回错误提示。

```bash
# 清理分支示例
git push origin --delete feature-xxx
```



