# /memory-evolution

每日 00:00 由定时任务自动触发，整理记忆并触发进化建议。

## 执行步骤

1. 读取 events.jsonl 当前行数：
   exec: wc -l ~/.openclaw/workspace/.sys/logs/events.jsonl

2. 若行数与上次相比新增 < 5，跳过本次进化，退出。

3. 若新增 >= 5 行，执行进化引擎：
   exec: python3 ~/.openclaw/workspace/scripts/evolve.py

4. 根据 evolve.py 输出，应用晋升规则：

   晋升规则（三条）：
   - 同一 learning 被引用或触发 >= 3 次 -> 晋升写入 AGENTS.md
   - 同一错误模式出现 >= 2 次 -> 写入 memory/errors.md 并标注 pending
   - 单次出现内容 -> 仅保留在 recent.md，不晋升

5. 若有规则变更，更新 AGENTS.md，并在 memory/recent.md 记录变更摘要

6. 检查 recent.md 行数，超 300 行则归档：
   exec: wc -l ~/.openclaw/workspace/memory/recent.md
   若超出 -> 归档到 memory/archive/YYYY-MM.md，保留最近 50 行

## 注意
evolve.py 会自动检测实际运行时目录（.sys/ 或 .openclaw/），
无需手动指定路径。
