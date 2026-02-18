# BTS Agent System

### Author: Peiwei Wu

This is a repository used to store BTS Agent System for Computer-Design-Competition-2026.

### Git 常用命令速查（本地 ↔ GitHub）

> 进入项目目录后再执行下面命令：
```bash
cd "F:\Undergraduate_Competitions\Computer_Design_Competition\code\BTS_Agent_System" # 本地的项目代码文件夹

1) 查看当前状态（最常用）
git status
看哪些文件被修改/新增、是否已暂存、当前在哪个分支。
git remote -v
看目前已经连接成功的远程仓库

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
6.1 临时保存改动（stash）
git stash
git pull
git stash pop
6.2 丢弃某个文件的本地修改（危险：不可恢复）
git restore README.md
6.3 丢弃全部未提交修改（危险：不可恢复）
git restore .

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


### PS:
origin   → "自己的GitHub账号名"/BTS-Agent-System
upstream → BTS-JNU/BTS-Agent-System
工作流程：
先在自己的仓库里面更改，推送到origin，改完稳定后再推送/pull_request到upstream，每次更新同步要从upstream中提取
pull_request：拉取请求，将自己的代码上传到总的仓库中请求合并

这是更新的一句话
