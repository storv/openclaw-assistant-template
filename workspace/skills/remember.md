# /remember

将本次对话的重要内容沉淀到记忆系统。

## 执行步骤

1. 读取 memory/recent.md 当前内容

2. 判断本次对话有哪些值得记录：
   - 用户纠正了我的输出
   - 发现了用户新的偏好或习惯
   - 完成了重要任务，有可复用的经验
   - 掌握了新的项目信息

3. 将新内容追加到 memory/recent.md：
   - 若涉及项目信息 -> 同步更新 memory/project.md
   - 若涉及用户偏好 -> 同步更新 memory/core.md

4. 若 recent.md 超过 300 行：
   - 将旧内容归档到 memory/archive/YYYY-MM.md
   - recent.md 只保留最近 50 行
