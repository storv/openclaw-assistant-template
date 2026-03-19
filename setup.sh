#!/bin/bash
# ============================================================
# OpenClaw 数字助手 v3.6 — 一键部署脚本
# 用法：
#   bash setup.sh              # 安装到 ~/.openclaw/workspace
#   bash setup.sh /custom/path # 安装到自定义路径
#   bash setup.sh --force      # 强制重装（覆盖已有数据）
# ============================================================

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="${1:-$HOME/.openclaw/workspace}"
FORCE=0
[ "${1:-}" = "--force" ] && FORCE=1 && WORKSPACE="$HOME/.openclaw/workspace"
[ "${2:-}" = "--force" ] && FORCE=1

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log()  { echo -e "${GREEN}[setup]${NC} $1"; }
warn() { echo -e "${YELLOW}[warn]${NC} $1"; }
fail() { echo -e "${RED}[fail]${NC} $1"; exit 1; }

command -v python3 &>/dev/null || fail "python3 未安装，请先安装后重试"

log "目标 workspace：$WORKSPACE"

# ── 1. 初始化运行时目录（.sys）────────────────────────────────────────
log "初始化运行时目录 (.sys)..."
mkdir -p "$WORKSPACE/.sys/sessions"
mkdir -p "$WORKSPACE/.sys/logs"
mkdir -p "$WORKSPACE/.sys/baseline"
mkdir -p "$WORKSPACE/.sys/todo"
mkdir -p "$WORKSPACE/.sys/compact"
mkdir -p "$WORKSPACE/memory/archive"
mkdir -p "$WORKSPACE/scripts"

# 初始化事件日志（业务事件流，唯一写入路径）
touch "$WORKSPACE/.sys/logs/events.jsonl"
[ -f "$WORKSPACE/.sys/logs/last_evolution_line.txt" ] || echo "0" > "$WORKSPACE/.sys/logs/last_evolution_line.txt"

# ── 2. 初始化记忆文件（不覆盖已有）──────────────────────────────────
if [ ! -f "$WORKSPACE/memory/recent.md" ]; then
    echo -e "# Recent Memory\n_由 evolve.py 自动维护_" > "$WORKSPACE/memory/recent.md"
    log "创建 memory/recent.md"
fi
if [ ! -f "$WORKSPACE/memory/errors.md" ]; then
    echo -e "# Error Log\n_记录高频错误与正确处理方式_" > "$WORKSPACE/memory/errors.md"
    log "创建 memory/errors.md"
fi
if [ ! -f "$WORKSPACE/memory/core.md" ]; then
    printf "# Core Memory\n\n## 用户信息\n- 姓名：（待填写）\n- 时区：（待填写）\n" > "$WORKSPACE/memory/core.md"
    log "创建 memory/core.md"
fi
# v3.6 新增：growth.md
if [ ! -f "$WORKSPACE/memory/growth.md" ]; then
    printf "# Growth Log\n_长期能力成长轨迹，由 evolve.py 自动追加_\n\n" > "$WORKSPACE/memory/growth.md"
    log "创建 memory/growth.md"
fi

# ── 3. 脚本执行权限 ──────────────────────────────────────────────────
log "设置脚本执行权限..."
chmod +x "$WORKSPACE/scripts/"*.sh 2>/dev/null || true
chmod +x "$WORKSPACE/scripts/"*.py 2>/dev/null || true

# ── 4. 注册 crontab 定时任务 ─────────────────────────────────────────
log "注册 crontab 定时任务..."

CRON_EVOLUTION="0 0 * * * python3 $WORKSPACE/scripts/evolve.py >> $WORKSPACE/.sys/logs/cron-memory-evolution.log 2>&1"
CRON_REFLECTION="0 9 * * 1 echo '{\"ts\":\"'\$(date -Iseconds)'\",\"type\":\"task-done\",\"tag\":[\"cron\",\"weekly\"],\"content\":\"weekly-self-reflection scheduled trigger\",\"count\":1}' >> $WORKSPACE/.sys/logs/events.jsonl"

(
    crontab -l 2>/dev/null | grep -v "cron-memory-evolution\|weekly-self-reflection"
    echo "$CRON_EVOLUTION"
    echo "$CRON_REFLECTION"
) | crontab -

if crontab -l 2>/dev/null | grep -q "cron-memory-evolution"; then
    log "crontab 验证成功：memory-evolution 已注册（每天 00:00）"
else
    warn "memory-evolution 注册失败，请手动执行：crontab -e"
fi
if crontab -l 2>/dev/null | grep -q "weekly-self-reflection"; then
    log "crontab 验证成功：weekly-self-reflection 已注册（每周一 09:00）"
else
    warn "weekly-self-reflection 注册失败，请手动执行：crontab -e"
fi

echo ""
echo -e "${GREEN}✅ 部署完成！（v3.6）${NC}"
echo ""
echo "下一步："
echo "  1. 在 OpenClaw → Settings → Workspace 中设置路径为："
echo "     $WORKSPACE"
echo "  2. 在 OpenClaw 新建对话，粘贴 AGENTS.md 中的激活提示词"
echo "  3. 手动验证 evolve.py："
echo "     python3 $WORKSPACE/scripts/evolve.py"
echo ""
echo "定时任务状态："
crontab -l 2>/dev/null | grep -E "memory-evolution|weekly-self-reflection" || echo "  （未检测到，请查看上方警告）"
