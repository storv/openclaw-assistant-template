# skill: session-notes
## 执行步骤
1. 追加写入 .openclaw/sessions/YYYY-MM-DD.md：
   - 做了什么 / 遇到的问题与解法 / 留到下次的 TODO
2. 向 .openclaw/logs/events.jsonl 写结构化事件：
   - 每条一行 JSON，含 ts/type/uuid/session_id
   - 写入前检查幂等性（同 session_id+type+detail 已存在则跳过）
   - 按 AGENTS.md 事件类型规范记录
