# OpenClaw 内网数字助手模板 v3.1

> 零额外依赖（只需 python3 和 git），让 OpenClaw 具备“持续学习 + 自我进化”的能力。  
> 模板目录：`workspace/`  
> 默认安装路径：`~/.openclaw/workspace`

---

## 核心能力

- **持久记忆**：自动记住你的偏好、项目上下文、纠错记录  
- **错误追踪**：失误自动记录到 `memory/errors.md`，重复出现会被标记为待晋升规则  
- **自我进化**：
  - 每日 `/memory-evolution` 聚合最近事件，生成“进化摘要”
  - 每周 `/weekly-self-reflection` 输出量化周报，推荐 Skill 提取候选
- **自动收尾**：检测到告别语时自动执行 `/session-notes`，静默写日志和事件  
- **纯文件驱动**：所有行为都由 `*.md / *.py / *.sh` 定义，极易用 git 管理和审计

---

## 仓库结构

```bash
openclaw-assistant-template/
├── setup.sh                 # 一键部署脚本（复制 workspace/ 到目标目录）
├── README.md                # 本文件
└── workspace/               # 完整 workspace 模板（和最终运行目录结构一致）
    ├── IDENTITY.md          # 助手人格设定（名称、风格、边界）
    ├── AGENTS.md            # Agent 行为规则与自动触发逻辑
    ├── memory/
    │   ├── core.md          # 用户画像（称呼、时区、偏好）
    │   ├── project.md       # 项目上下文 + 周报存档
    │   ├── recent.md        # 最近学习记录 + 进化摘要
    │   └── errors.md        # 错误日志（重复错误会被标记 pending）
    ├── skills/
    │   ├── remember.md              # /remember：沉淀当前对话要点
    │   ├── session-notes.md         # /session-notes：会话结束日志 + events.jsonl
    │   ├── memory-evolution.md      # /memory-evolution：每日进化
    │   ├── weekly-self-reflection.md# /weekly-self-reflection：每周量化周报
    │   ├── compact.md               # /compact：压缩上下文
    │   ├── todo.md                  # /todo：待办管理
    │   └── health-check.md          # /health-check：系统自检
    └── scripts/
        ├── evolve.py        # 进化引擎：分析 events.jsonl，更新 recent/errors
        ├── health-check.sh  # 健康检查：路径、权限、JSON 合法性
        └── baseline.sh      # 快照：每天输出一份 baseline，支持 diff 对比
提示：workspace/ 目录内容即为“标准方案 v3.1”的完整落地版本。
setup.sh 所做的事情只是：把 workspace/ 原样复制到目标路径，并初始化运行时目录。

安装与更新
1. clone 仓库

bash
git clone https://github.com/you/openclaw-assistant-template.git
cd openclaw-assistant-template
2. 安装到默认 workspace（推荐）

bash
bash setup.sh
默认安装到：

text
~/.openclaw/workspace
3. 安装到自定义路径（可选）

bash
bash setup.sh /path/to/your/workspace
重复执行 setup.sh 相当于更新框架文件（覆盖现有 AGENTS.md、skills/、scripts/ 等）。
如果你在运行中的 workspace 里做了个性化修改，建议只改这些文件，并在 git 里 ignore 它们：

workspace/IDENTITY.md

workspace/memory/core.md

workspace/memory/project.md

workspace/memory/recent.md

workspace/memory/errors.md

配置 OpenClaw
在 OpenClaw 中，将 workspace 路径设置为安装目标路径，例如：

text
~/.openclaw/workspace
位置：
OpenClaw → Settings → Workspace → Custom Path

首次激活：对话提示词
安装完成后，新建一个 OpenClaw 对话，粘贴下面这段提示词：

text
请读取以下文件完成初始化：
IDENTITY.md、AGENTS.md、memory/core.md、
memory/project.md、memory/recent.md、memory/errors.md
以及 skills/ 下所有文件。

读取完成后，请依次问我以下问题：

[关于你]
1. 给你起个名字 — 你想叫什么？
2. 你的性格风格 — 直接/温和/幽默/严谨，或自由描述
3. 有什么口头禅或特别习惯吗？（没有可跳过）

[关于我]
4. 叫我什么，你在哪个时区？
5. 你的工作场景和日常使用偏好是什么？
6. 希望我重点协助哪些方面？

收集完以上信息后，请：
- 将助手设定写入 IDENTITY.md
- 将用户信息写入 memory/core.md
- 执行 /remember 和 /session-notes

完成后请立即创建 2 个定时任务（使用 OpenClaw 自己的定时能力）：
1. 每天 00:00 执行 /memory-evolution
2. 每周一 09:00 执行 /weekly-self-reflection

定时任务创建完成后：
- 告诉我你创建了哪些任务，下一次触发时间
- 做一个简短的自我介绍，确认全部初始化完成
你也可以直接把 setup.sh 文件拖给 OpenClaw，让它先理解脚本，再按里面的步骤执行和自检。

日常使用：常用指令
指令	作用	触发时机
/remember	将当前对话要点写入记忆	重要对话后手动执行
/session-notes	会话日志 + events.jsonl + 错误记录	检测到告别语时自动执行
/memory-evolution	整理最近 7 天事件，更新进化摘要和错误晋升	每日 00:00（定时）
/weekly-self-reflection	生成量化周报，列出 Skill 候选	每周一 09:00（定时）
/compact	压缩上下文，避免 context 爆掉	对话太长时手动触发
/todo	管理待办列表	任意时刻
/health-check	检查路径、权限、JSON 合法性等	怀疑系统异常时
命令行工具示例
bash
# 健康检查
WORKSPACE=~/.openclaw/workspace \
  bash ~/.openclaw/workspace/scripts/health-check.sh

# 搜索历史事件（跨会话记忆检索）
python3 ~/.openclaw/workspace/scripts/evolve.py search "关键词"

# 手动触发进化（等价于每日 00:00 的定时任务）
python3 ~/.openclaw/workspace/scripts/evolve.py

# 生成 baseline 快照并查看
WORKSPACE=~/.openclaw/workspace \
  bash ~/.openclaw/workspace/scripts/baseline.sh

# 查看最近 20 条事件（格式化）
tail -20 ~/.openclaw/workspace/.sys/logs/events.jsonl \
  | python3 -m json.tool

# 简单备份当前 workspace
cp -r ~/.openclaw/workspace ~/openclaw-backup-$(date +%Y%m%d)
系统工作原理（简版）
text
每次对话
  └─ 用户说“再见 / 结束 / bye”……
       └─ /session-notes 自动静默执行
            ├─ 写 .sys/sessions/YYYY-MM-DD.md
            ├─ 追加 .sys/logs/events.jsonl（结构化事件）
            └─ 有失误时更新 memory/errors.md

每天 00:00
  └─ /memory-evolution
       └─ scripts/evolve.py
            ├─ 自动检测 .sys/ 或 .openclaw/ 作为运行时目录
            ├─ 统计错误和能力变化
            ├─ 高频错误 → errors.md 标记 pending
            └─ 更新 memory/recent.md 中的“进化摘要”

每周一 09:00
  └─ /weekly-self-reflection
       ├─ 统计最近 7 天 sessions + events.jsonl
       ├─ 输出量化数据（纠错次数、新能力、错误情况）
       └─ 将周报追加写入 memory/project.md
版本记录
版本	说明
v3.0	初版自进化框架：结构化 events.jsonl、错误晋升、周报模板
v3.1	统一使用 .sys/ 运行时目录（兼容旧版本 .openclaw/）、清理路径问题、简化为 workspace/ + setup.sh 的 git 友好结构
