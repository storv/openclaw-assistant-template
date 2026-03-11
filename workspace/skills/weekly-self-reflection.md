# /weekly-self-reflection

每周一 09:00 由定时任务自动触发，生成量化周报。

## 执行步骤

1. 列出本周所有会话文件：
   exec: ls ~/.openclaw/workspace/.sys/sessions/ | tail -7

2. 读取 memory/recent.md、memory/project.md、memory/errors.md

3. 从 events.jsonl 统计本周数据：
   exec: grep "$(date -d '7 days ago' +%Y-%m-%d 2>/dev/null || date -v-7d +%Y-%m-%d)" \
     ~/.openclaw/workspace/.sys/logs/events.jsonl | wc -l

4. 对比 AGENTS.md 近期变更（查看 recent.md 中的进化摘要记录）

5. 按以下量化模板生成周报：

   ## 周报 YYYY-WXX（YYYY-MM-DD）

   ### 数据统计
   - 会话次数：N
   - 新增 learnings：N 条（晋升 N 条）
   - 错误记录：N 条（消除 N 条，pending N 条）
   - 用户纠正次数：N
   - Skill 提取候选：N 个 / 新增 Skill 文件：N 个

   ### 能力变化
   - 进步最明显：___
   - 仍反复出错：___

   ### 规则变更
   - 新增 AGENTS.md 规则：___
   - 废弃规则：___

   ### Skill 提取候选（count >= 5 且无同 tag 错误）
   - 候选 1：___ （建议文件名：xxx.md）
   - 候选 2：___ （建议文件名：xxx.md）
   ⚠️ 需人工确认后才写入 skills/，每次最多 2 个

   ### 下周优先改进（最多 2 条）
   1. ___
   2. ___

6. 将周报追加写入 memory/project.md 留档

7. 若有 Skill 提取候选，等待用户输入「确认提取」后才写入 skills/
