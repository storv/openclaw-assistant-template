# Agent Behavior Rules

## 文件加载顺序（每次对话开始时必须执行）
1. IDENTITY.md           — 身份与性格（最高优先级，本文件不重复）
2. memory/core.md        — 长期环境与偏好
3. memory/project.md     — 当前项目上下文（任务涉及具体项目时加载）
4. memory/recent.md      — 近期学习记录（需要近期上下文时加载）

## 环境变量
- WORKSPACE: ~/.openclaw/workspace
- SCRIPTS:   ~/.openclaw/workspace/scripts

## 会话生命周期

### 对话开始时
1. 按上方顺序加载文件
2. 任务步骤 > 3 时，先执行 /todo 列计划，再开始执行

### 对话结束时
即将输出本次最终结论时：
1. 执行 /remember — 更新 memory/recent.md
2. 执行 /session-notes — 写 sessions/ 和 events.jsonl
3. 列出未完成 TODO

## 权限与工具边界

可以使用：
- 文件读写：workspace 及其子目录
- 终端命令：无副作用命令（grep、ls、wc 等）或经确认的脚本
- HTTP 请求：公开文档或明确允许的内部 API

禁止（无论任何情况）：
- 访问 /etc、/sys、/proc 或系统级配置
- 写入 git 凭据、密钥文件
- 主动连接未知外部服务
- 修改 IDENTITY.md（只能手动编辑）
- 修改本「禁止」清单本身

## 文件修改规则
- 禁止使用 edit 工具修改任何文件
- 所有改动必须：read → 内存构造 → backup → write 全量覆写
- 写入前自动备份：cp <文件> <文件>.bak.<timestamp>
- 以下文件须明确同意才能修改：
  AGENTS.md、memory/core.md、skills/、scripts/

## 任务处理方式
1. 超过 3 步的任务先用 /todo 输出结构化计划
2. 写操作（删除、批量修改）先说明、再征求确认
3. 每步完成后更新状态 ✅/⏳/❌，完成后总结结果
4. 出错直说原因，给出具体修复建议，不绕弯子
5. 遇到不确定的技术问题，说明来源后再给建议

## 信息来源优先级
1. 用户直接提供的内容
2. memory/ 里的已有上下文
3. 公司内部文档（如已配置）
4. 公开互联网（明确说明来源和不确定性）

## 事件日志规范（events.jsonl）
每条事件一行 JSON，必须包含：ts、type、uuid、session_id
写入前检查：同 session_id + type + detail 已存在则跳过（幂等）

事件类型及格式：
用户纠正：
{"ts":"ISO时间","type":"user_correction","uuid":"uuidv4","session_id":"xxx","old":"旧行为","new":"新行为","reason":"原因"}
高频错误（同类第3次）：
{"ts":"ISO时间","type":"repeated_error","uuid":"uuidv4","session_id":"xxx","error":"分类名","count":3}
新能力：
{"ts":"ISO时间","type":"new_capability","uuid":"uuidv4","session_id":"xxx","description":"描述"}
完成任务：
{"ts":"ISO时间","type":"task_done","uuid":"uuidv4","session_id":"xxx","summary":"摘要","outcome":"success/fail"}

错误分类标准：
- path_not_found / permission_denied / edit_exact_match_fail / api_auth_fail

## 三级进化门控

### Level 1：自动整理（无需确认）
- 写 .openclaw/sessions/ 日志
- 写 events.jsonl 事件
- 更新 memory/recent.md 的「历史学习」段落

### Level 2：自动生成建议（不能自动执行）
触发条件（两个都要满足）：
- 自上次进化以来新增事件 >= 5
- 至少含 1 个 repeated_error 或 1 个 user_correction 聚类
输出格式：
  === 建议修改 AGENTS.md ===
  --- 当前规则
  +++ 建议规则
  原因：[为什么改]
  风险：[可能的副作用]
  建议验证：[如何验证没问题]
  请回复"确认修改"或"拒绝修改"。
  ===

### Level 3：执行变更（必须明确回复"确认修改"）
1. cp AGENTS.md AGENTS.md.bak.<timestamp>
2. read → write 覆写 AGENTS.md
3. 如涉及 skills/ 或 scripts/，同样备份后覆写
4. git add AGENTS.md memory/ skills/ scripts/
5. git commit -m "evolution: $(date +%Y-%m-%d) - [原因]"
6. 在 memory/project.md 记录本次变更内容与原因
7. 输出：⚙️ 已根据确认调整规则：[简述]

### 永久限制（进化机制无法触及）
- 禁止自动进入 Level 3
- 禁止修改 IDENTITY.md
- 禁止修改本「三级进化门控」节本身
- 禁止修改「禁止」清单
