# 🦞 OpenClaw 自主进化数字助手模板

> **个人 AI 助手 · 持续学习 · 本地自动化**
> 基于 OpenClaw + Python + cron 的自主进化配置方案

[![版本](https://img.shields.io/badge/version-v3.6-1a56db?style=flat-square)](https://github.com/zhihua-yang/openclaw-assistant-template)
[![平台](https://img.shields.io/badge/platform-Linux%20%7C%20macOS-0694a2?style=flat-square)]()
[![Python](https://img.shields.io/badge/python-3.8%2B-057a55?style=flat-square)]()
[![License](https://img.shields.io/badge/license-MIT-6b7280?style=flat-square)]()

---

## ✨ 这是什么

一套让 OpenClaw AI 助手**真正记住你、持续进化**的本地配置模板。

- 📝 **标准化事件记录**：每次重要交互通过 `create_event.py` 写入结构化日志
- 🧠 **每日自动记忆提炼**：`evolve.py` 由 cron 驱动，每天凌晨自动读取事件、更新记忆文件
- 📈 **长期成长追踪**：`memory/growth.md` 记录能力里程碑（v3.6 新增）
- 🔧 **一键部署**：`setup.sh` 自动完成目录创建、文件初始化、cron 注册

---

## 🆕 v3.6 更新说明

> 基于 v3.5 三个已知问题的全面修复

| 问题 | 根本原因 | v3.6 修复方案 |
|------|---------|-------------|
| `memory/growth.md` 不存在 | 从未被纳入规范体系 | 正式定义，setup.sh 自动创建，evolve.py 自动写入 |
| `.sys/logs/events.jsonl` 始终为空 | `session_note_writer.py` 写错路径 | 路径修正为 `.sys/logs/events.jsonl` |
| 三套事件写入逻辑并存 | AGENTS.md 规则分裂 | 统一声明唯一入口为 `create_event.py`，删除 `evolve.py` 中的 `append_event()` |

**核心设计原则（SSOT）**：
- 事件写入唯一入口：`create_event.py`
- 事件唯一路径：`.sys/logs/events.jsonl`
- `.openclaw/logs/events.jsonl` 为 Gateway 平台日志，脚本只读不写
- 规则变更必须先删除旧规则，不允许新旧并存

---

## 📁 目录结构

```
~/.openclaw/workspace/
├── .sys/
│   ├── logs/
│   │   ├── events.jsonl              ← ✅ 唯一业务事件写入路径
│   │   ├── last_evolution_line.txt
│   │   └── cron-memory-evolution.log
│   ├── sessions/                     ← /session-notes 写入
│   ├── baseline/
│   ├── todo/
│   └── compact/
├── memory/
│   ├── core.md                       ← 用户信息（人工维护）
│   ├── recent.md                     ← evolve.py 自动维护
│   ├── errors.md                     ← evolve.py 追加 + 人工晋升
│   ├── growth.md                     ← ✨ v3.6 新增：长期成长轨迹
│   ├── project.md                    ← 项目信息（人工维护）
│   └── archive/                      ← recent.md 超300行自动归档
├── scripts/
│   ├── setup.sh                      ← 一键部署（v3.6）
│   ├── evolve.py                     ← 核心进化脚本（v3.6 重构）
│   ├── create_event.py               ← 事件写入唯一入口
│   ├── session_note_writer.py        ← v3.6 路径修复
│   ├── fix_recent_events_tags.py
│   └── fix_nonstandard_types.py
├── IDENTITY.md
└── AGENTS.md                         ← v3.6 行为规范

# 注意：以下为 Gateway 平台日志，脚本禁止写入
~/.openclaw/logs/
└── events.jsonl                      ← ⚠️ Gateway 专用，与上方同名但用途不同
```

---

## 🚀 快速开始

### 前提条件

| 依赖 | 最低版本 | 检查 |
|------|---------|------|
| OpenClaw | 已安装 | 打开应用 |
| Python 3 | 3.8+ | `python3 --version` |
| Bash | 4.0+（macOS 需升级） | `bash --version` |
| cron | 系统自带 | `crontab -l` |

macOS 用户需升级 bash：`brew install bash`

### Step 1 — 克隆仓库

```bash
git clone https://github.com/zhihua-yang/openclaw-assistant-template.git
cd openclaw-assistant-template
```

### Step 2 — 一键部署

```bash
# 默认安装到 ~/.openclaw/workspace
bash scripts/setup.sh

# 或自定义路径
bash scripts/setup.sh /custom/path/workspace
```

正常输出示例：
```
[setup] 目标 workspace：/Users/you/.openclaw/workspace
[setup] 初始化运行时目录 (.sys)...
[setup] 创建 memory/growth.md
[setup] 设置脚本执行权限...
[setup] crontab 验证成功：memory-evolution 已注册（每天 00:00）
[setup] crontab 验证成功：weekly-self-reflection 已注册（每周一 09:00）
✅ 部署完成！（v3.6）
```

### Step 3 — 配置 OpenClaw

打开 OpenClaw → **Settings** → **Workspace**，填入绝对路径：
```
/Users/yourname/.openclaw/workspace
```
> ⚠️ 使用绝对路径，不要用 `~`

### Step 4 — 激活助手

新建对话，粘贴以下提示词：

```
请读取以下文件完成初始化：
IDENTITY.md、AGENTS.md、memory/core.md、
memory/project.md、memory/recent.md、memory/errors.md、memory/growth.md
以及 scripts/ 下所有文件。

读取完成后，请依次问我：
1. 给我起个名字
2. 我的性格风格
3. 你叫什么？时区？
4. 工作场景和偏好？

收集信息后写入 IDENTITY.md 和 memory/core.md，
执行 /remember 和 /session-notes，
验证：exec: crontab -l | grep -E "memory-evolution|weekly-self-reflection"
```

### Step 5 — 验证部署

```bash
# 写入测试事件
python3 ~/.openclaw/workspace/scripts/create_event.py   --type system-improvement   --content "完成 v3.6 部署验证，路径统一 .sys/logs/events.jsonl"

# 确认写入正确路径（非 .openclaw/logs/）
cat ~/.openclaw/workspace/.sys/logs/events.jsonl

# 运行 evolve.py
python3 ~/.openclaw/workspace/scripts/evolve.py
# 预期：[evolve] using logs: .../.sys/logs/events.jsonl

# 确认 growth.md 已创建
cat ~/.openclaw/workspace/memory/growth.md
```

---

## 📋 脚本说明

| 脚本 | 职责 | 写入路径 |
|------|------|---------|
| `create_event.py` | 标准化事件写入（唯一入口） | `.sys/logs/events.jsonl` |
| `evolve.py` | 读取事件、提炼记忆 | `memory/recent.md`, `errors.md`, `growth.md` |
| `setup.sh` | 一键部署、cron 注册 | 目录初始化 |
| `session_note_writer.py` | 会话摘要写入 | `.sys/logs/events.jsonl`, `.sys/sessions/` |
| `fix_recent_events_tags.py` | 修复历史 Tags 缺失 | `.sys/logs/events.jsonl`（in-place） |
| `fix_nonstandard_types.py` | 修复非标准类型 | `.sys/logs/events.jsonl`（in-place） |

### 事件类型（14 种标准类型）

```bash
python3 scripts/create_event.py --list-types
```

| 类型 | 说明 |
|------|------|
| `task-done` | 完成任务 |
| `error-found` | 发现错误 |
| `system-improvement` | 系统改进 |
| `learning-achievement` | 学习成就 |
| `user-correction` | 用户纠正 |
| `new-capability` | 新能力获得 |
| `pua-inspection` | 深度架构检查 |
| `quality-improvement` | 质量改进 |
| *(更多见 AGENTS.md)* | |

---

## 📅 日常使用

```bash
# 记录事件
python3 scripts/create_event.py --type task-done --content "完成需求文档评审"

# 手动触发记忆进化
python3 scripts/evolve.py

# 搜索历史记忆
python3 scripts/evolve.py search "关键词"

# 查看成长轨迹
cat memory/growth.md

# 查看 cron 日志
cat .sys/logs/cron-memory-evolution.log
```

### OpenClaw 快捷指令

| 指令 | 行为 |
|------|------|
| `/remember` | 写入本次会话重要事件 |
| `/session-notes` | 保存会话摘要到 `.sys/sessions/` |
| `/health-check` | 检查系统状态 |
| `/evolve` | 手动触发记忆进化 |
| `/search [keyword]` | 搜索历史记忆 |

---

## 🔍 故障排查

**events.jsonl 为空 / 没有数据**
```bash
# 检查正确路径（注意是 .sys/logs，不是 .openclaw/logs）
cat ~/.openclaw/workspace/.sys/logs/events.jsonl
```

**growth.md 不存在**
```bash
echo -e "# Growth Log
_由 evolve.py 自动追加_
"   > ~/.openclaw/workspace/memory/growth.md
# 或重跑 setup.sh（不覆盖已有数据）
bash scripts/setup.sh
```

**evolve.py FileNotFoundError**
```bash
mkdir -p ~/.openclaw/workspace/.sys/logs
touch ~/.openclaw/workspace/.sys/logs/events.jsonl
```

**cron 不执行（macOS）**
系统偏好设置 → 隐私与安全性 → 完全磁盘访问 → 允许 cron

**macOS bash 版本过低**
```bash
brew install bash
/opt/homebrew/bin/bash scripts/setup.sh
```

---

## 📦 数据备份优先级

| 优先级 | 文件 | 说明 |
|--------|------|------|
| 🔴 最重要 | `memory/errors.md` | 人工整理的错误经验，无法自动重建 |
| 🟡 次要 | `memory/recent.md`, `memory/growth.md` | 可重跑 evolve.py 部分重建 |
| 🟢 影响最小 | `.sys/logs/events.jsonl` | 丢失后记忆文件不受影响 |

---

## 📜 版本历史

| 版本 | 日期 | 核心变更 |
|------|------|---------|
| v3.6 | 2026-03-19 | 修复路径混乱、新增 growth.md、删除冗余写入逻辑、SSOT 规范 |
| v3.5 | 2026-03-18 | 统一 .sys/logs 路径、修复 Tags、类型标准化工具 |
| v3.4 | — | evolve.py 自动路径探测（已废弃） |

---

## 📄 License

MIT © [zhihua-yang](https://github.com/zhihua-yang)
