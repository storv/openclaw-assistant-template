# /session-notes

每次会话结束时自动静默执行（由 AGENTS.md 自动规则触发）。

## 执行步骤

1. 将本次会话摘要写入：
   ~/.openclaw/workspace/.sys/sessions/YYYY-MM-DD.md

2. 将结构化事件追加到 events.jsonl：
   ~/.openclaw/workspace/.sys/logs/events.jsonl

   标准 schema：
   {"ts":"ISO时间","type":"类型","tag":["分类","子分类"],"content":"描述","count":1}

   type 枚举：
   - user-correction：用户纠正了我的输出
   - repeated-error：重复出现的错误
   - new-capability：掌握了新能力或信息
   - task-done：完成了重要任务
   - preference：发现用户新的偏好

   写入示例：
   exec: echo '{"ts":"2026-03-12T00:00:00","type":"new-capability","tag":["tool","shell"],"content":"描述","count":1}' \
     >> ~/.openclaw/workspace/.sys/logs/events.jsonl

3. 若本次会话有明显失误：
   - 检查 memory/errors.md 是否有同类条目
   - 有 -> 更新该条目的出现次数 +1，若 >= 2 次改状态为 pending
   - 无 -> 新增条目，状态为 monitoring
   - 不重复新增同类错误，只累计次数

4. 执行 /remember，更新 memory/recent.md 和 memory/project.md
