# AGENTS — 行为规范 v3.6
# ============================================================
# 变更协议（SSOT 原则）
# - 新增规则前，必须搜索是否存在相同职责的旧规则
# - 旧规则若被新规则替代，必须同行标注 [deprecated] 或删除
# - 路径、工具名、函数名变更必须全文搜索替换，不允许新旧并存
# ============================================================

## 路径权威定义（唯一可信来源，所有脚本以此为准）

| 用途 | 路径 | 说明 |
|------|------|------|
| 业务事件流 | `.sys/logs/events.jsonl` | **唯一写入路径**，所有脚本写此处 |
| Gateway 平台日志 | `.openclaw/logs/events.jsonl` | 只读，平台自动写入，**脚本禁止读写** |
| 进化摘要 | `memory/recent.md` | 由 evolve.py 自动维护 |
| 错误库 | `memory/errors.md` | 人工维护为主，evolve.py 自动追加待晋升项 |
| 成长记录 | `memory/growth.md` | 长期能力成长轨迹，由 evolve.py 自动追加 |
| 会话记录 | `.sys/sessions/` | /session-notes 指令写入 |
| cron 日志 | `.sys/logs/cron-memory-evolution.log` | cron 自动写入 |

> ⚠️ 排查问题时必须检查 `.sys/logs/events.jsonl`
> 勿误读 `.openclaw/logs/events.jsonl`（两个文件同名但用途不同）

---

## 事件记录规范

**所有事件统一通过 `create_event.py` 写入 `.sys/logs/events.jsonl`。**
不使用 evolve.py 的 append_event()，不使用任何其他写入逻辑。

### 标准事件类型（共 14 种）

| 类型 | 说明 | 最低内容长度 |
|------|------|------------|
| `task-done` | 完成任务 | 8 词 |
| `error-found` | 发现错误 | 8 词 |
| `system-improvement` | 系统改进 | 10 词 |
| `learning-achievement` | 学习成就（需含学习价值） | 15 词 |
| `user-correction` | 用户纠正 | 10 词 |
| `automation-deployment` | 自动化部署 | 5 词 |
| `error-fix` | 错误修复 | 5 词 |
| `system-monitoring` | 系统监控 | 5 词 |
| `quality-verification` | 质量验证 | 5 词 |
| `new-capability` | 新能力获得 | 5 词 |
| `automation-planning` | 自动化规划 | 5 词 |
| `memory-compaction` | 记忆压缩 | 5 词 |
| `pua-inspection` | 深度架构检查 | 5 词 |
| `quality-improvement` | 质量改进 | 5 词 |

### 写入方式（唯一）

```bash
python3 scripts/create_event.py --type <类型> --content "<内容>"
# 可选参数
python3 scripts/create_event.py --type <类型> --content "<内容>" --tags "tag1,tag2" --count 2
```

---

## 记忆文件说明

| 文件 | 维护方式 | 说明 |
|------|---------|------|
| `memory/core.md` | 人工 | 用户基本信息、偏好 |
| `memory/project.md` | 人工 | 当前项目信息 |
| `memory/recent.md` | evolve.py 自动 | 近 7 天事件摘要，超 300 行自动归档 |
| `memory/errors.md` | evolve.py 追加 + 人工晋升 | 高频错误库，pending → promoted 需人工确认 |
| `memory/growth.md` | evolve.py 自动追加 | 长期能力成长轨迹，记录新能力里程碑 |

---

## 快捷指令

| 指令 | 行为 |
|------|------|
| `/remember` | 将本次会话重要内容写入事件日志（调用 create_event.py） |
| `/session-notes` | 生成会话摘要，保存到 `.sys/sessions/` |
| `/health-check` | 检查系统状态（见下方健康检查项） |
| `/evolve` | 手动触发记忆进化（运行 evolve.py） |
| `/search [keyword]` | 搜索历史记忆（调用 evolve.py search） |

### /health-check 检查项

```bash
# 1. 事件日志（正确路径）
cat ~/.openclaw/workspace/.sys/logs/events.jsonl | wc -l

# 2. cron 任务
crontab -l | grep -E "memory-evolution|weekly-self-reflection"

# 3. evolve.py 手动运行
python3 ~/.openclaw/workspace/scripts/evolve.py

# 4. growth.md 存在
ls ~/.openclaw/workspace/memory/growth.md
```

---

## cron 定时任务

| 任务 | 执行时间 | 脚本 |
|------|---------|------|
| 记忆进化 | 每天 00:00 | `evolve.py` |
| 每周自我反思 | 每周一 09:00 | 写入 task-done 事件到 `.sys/logs/events.jsonl` |

---

## 脚本职责一览（禁止职责交叉）

| 脚本 | 唯一职责 | 写入路径 |
|------|---------|---------|
| `create_event.py` | 标准化事件写入 | `.sys/logs/events.jsonl` |
| `evolve.py` | 读取事件、提炼记忆 | `memory/recent.md`, `memory/errors.md`, `memory/growth.md` |
| `setup.sh` | 一键部署、cron 注册 | 目录初始化 |
| `fix_recent_events_tags.py` | 修复历史 Tags 缺失 | `.sys/logs/events.jsonl`（in-place） |
| `fix_nonstandard_types.py` | 修复非标准类型 | `.sys/logs/events.jsonl`（in-place） |
| `session_note_writer.py` | 会话摘要写入 | `.sys/logs/events.jsonl`, `.sys/sessions/` |
