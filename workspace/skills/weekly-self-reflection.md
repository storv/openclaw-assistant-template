# skill: weekly-self-reflection
## 执行步骤（每周一 09:00 cron 触发）

1. 读取最近 7 天 session notes：
exec: ls ${WORKSPACE}/.openclaw/sessions/
逐一读取最近 7 个文件

2. 读取 memory/recent.md 和 memory/project.md

3. 综合评估：
   - 哪些规则有效？哪些需要调整或删除？
   - 能力边界有哪些新突破？
   - 有没有连续出现的问题尚未处理？

4. 生成 AGENTS.md 修改建议（Level 2，格式同 memory-evolution）

5. 回复"确认修改"后执行 Level 3，git commit

6. 将本周复盘概要追加写入 memory/project.md

7. 执行健康检查：
exec: bash ${WORKSPACE}/scripts/health-check.sh
