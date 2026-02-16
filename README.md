## BTS Agent System

Author: Peiwei Wu

This is a repository used to store BTS Agent System for Computer-Design-Competition-2026.

## Git 常用命令速查（本地 ↔ GitHub）

> 进入项目目录后再执行下面命令：
```bash
cd "F:\Undergraduate_Competitions\Computer_Design_Competition\code\BTS_Agent_System" # 本地的项目代码文件夹

1) 查看当前状态（最常用）
git status
看哪些文件被修改/新增、是否已暂存、当前在哪个分支。

2) 查看当前分支 & 远程仓库地址
git branch
git remote -v 

3) 从 GitHub 拉取最新代码（更新到本地）
git pull
建议：每次开始写代码前先 git pull，避免冲突。

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
开发修改代码…

查看状态：
git status
暂存 + 提交 + 推送：

推送代码：
git add .
git commit -m "feat: xxxx"
git push
