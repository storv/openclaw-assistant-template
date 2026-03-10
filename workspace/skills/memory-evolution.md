# skill: memory-evolution
## 执行步骤（每日 00:00 cron 触发）

1. 运行进化脚本：
exec: WORKSPACE=$WORKSPACE python3 ${WORKSPACE}/scripts/evolve.py

2. 根据输出决定后续：
   - 含 "SKIP"   → 事件不足，结束
   - 含 "INFO"   → 无有效聚类，仅更新记忆，结束
   - 含 "LEVEL2" → 进入步骤 3

3. 生成 AGENTS.md 修改建议（Level 2，仅生成，不执行）：
  === 建议修改 AGENTS.md ===
  --- 当前规则
  +++ 建议规则
  原因：[为什么改]
  风险：[可能的副作用]
  建议验证：[如何验证没问题]
  请回复"确认修改"或"拒绝修改"。
  ===

4. 回复"确认修改"后（Level 3）：
   a. cp AGENTS.md AGENTS.md.bak.$(date +%Y%m%d_%H%M%S)
   b. read → write 覆写 AGENTS.md
   c. git add AGENTS.md memory/ skills/ scripts/
   d. git commit -m "evolution: $(date +%Y-%m-%d)"
   e. 在 memory/project.md 追加变更记录

5. 执行健康检查：
exec: bash ${WORKSPACE}/scripts/health-check.sh
