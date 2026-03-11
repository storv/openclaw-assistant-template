# /compact

当 context 接近上限时，压缩当前对话上下文。

## 执行步骤

1. 将当前对话压缩为结构化摘要，保存到：
   ~/.openclaw/workspace/.sys/compact/YYYY-MM-DD-HH.md

2. 摘要包含：
   - 本次对话核心目标
   - 已完成事项
   - 未完成事项
   - 重要决策和结论
   - 下一步行动

3. 压缩后继续当前任务，不中断工作流
