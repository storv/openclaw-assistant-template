#!/bin/bash
set -e

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  内网数字助手 — 初始化脚本 v2.1"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "部署路径：$WORKSPACE"
read -p "确认？(y/N) " confirm
[[ "$confirm" =~ ^[Yy]$ ]] || { warn "已取消"; exit 0; }

# ── 创建目录 ──────────────────────────────────
mkdir -p \
  "$WORKSPACE/skills" \
  "$WORKSPACE/memory/archive" \
  "$WORKSPACE/scripts" \
  "$WORKSPACE/.openclaw/sessions" \
  "$WORKSPACE/.openclaw/logs" \
  "$WORKSPACE/.openclaw/baseline" \
  "$WORKSPACE/.openclaw/todo" \
  "$WORKSPACE/.openclaw/compact"
ok "目录结构创建完成"

# ── 第一类：用户配置文件，已存在则跳过 ────────
copy_if_new() {
  [ -f "$2" ] && { warn "已存在，跳过：$(basename "$2")"; return; }
  cp "$1" "$2" && ok "已复制：$(basename "$2")"
}

copy_if_new "$REPO_DIR/workspace/IDENTITY.md"       "$WORKSPACE/IDENTITY.md"
copy_if_new "$REPO_DIR/workspace/AGENTS.md"         "$WORKSPACE/AGENTS.md"
copy_if_new "$REPO_DIR/workspace/memory/core.md"    "$WORKSPACE/memory/core.md"
copy_if_new "$REPO_DIR/workspace/memory/project.md" "$WORKSPACE/memory/project.md"
copy_if_new "$REPO_DIR/workspace/memory/recent.md"  "$WORKSPACE/memory/recent.md"

for f in "$REPO_DIR/workspace/skills/"*.md; do
  copy_if_new "$f" "$WORKSPACE/skills/$(basename "$f")"
done

# ── 第二类：脚本文件，已存在则备份后更新 ──────
copy_with_backup() {
  if [ -f "$2" ]; then
    cp "$2" "${2}.bak.$(date +%Y%m%d_%H%M%S)"
    warn "已备份旧版本：$(basename "$2")"
  fi
  cp "$1" "$2" && ok "已更新：$(basename "$2")"
}

# 注意：源文件在 REPO_DIR/workspace/scripts/
copy_with_backup "$REPO_DIR/workspace/scripts/evolve.py"       "$WORKSPACE/scripts/evolve.py"
copy_with_backup "$REPO_DIR/workspace/scripts/baseline.sh"     "$WORKSPACE/scripts/baseline.sh"
copy_with_backup "$REPO_DIR/workspace/scripts/health-check.sh" "$WORKSPACE/scripts/health-check.sh"
chmod +x "$WORKSPACE/scripts/"*.sh "$WORKSPACE/scripts/evolve.py"
ok "脚本文件已部署并赋权"

# ── 初始化日志 ─────────────────────────────────
touch "$WORKSPACE/.openclaw/logs/events.jsonl"
[ -f "$WORKSPACE/.openclaw/logs/last_evolution_line.txt" ] || \
  echo "0" > "$WORKSPACE/.openclaw/logs/last_evolution_line.txt"
ok "日志文件初始化完成"

# ── 写入环境变量（自动判断 shell）─────────────
if [ -n "$ZSH_VERSION" ] || [ "$SHELL" = "/bin/zsh" ]; then
  RC_FILE="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ] || [ "$SHELL" = "/bin/bash" ]; then
  RC_FILE="$HOME/.bashrc"
else
  RC_FILE="$HOME/.profile"
fi

if ! grep -q 'openclaw/workspace' "$RC_FILE" 2>/dev/null; then
  echo 'export WORKSPACE="$HOME/.openclaw/workspace"' >> "$RC_FILE"
  ok "已写入 WORKSPACE 到 $RC_FILE"
fi
source "$RC_FILE" 2>/dev/null || true

# ── Git 初始化 ─────────────────────────────────
cd "$WORKSPACE"
if [ ! -d ".git" ]; then
  git init && ok "Git 仓库初始化完成"
fi
git add IDENTITY.md AGENTS.md memory/ skills/ scripts/ 2>/dev/null || true
git commit -m "baseline: 内网数字助手初始化 $(date +%Y-%m-%d)" 2>/dev/null || \
  warn "Git commit 跳过（无变更或 git 未配置用户名）"

# ── 健康检查 ───────────────────────────────────
echo ""
WORKSPACE=$WORKSPACE bash "$WORKSPACE/scripts/health-check.sh"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ok "初始化完成！"
echo ""
echo "下一步："
echo "  1. 编辑 $WORKSPACE/IDENTITY.md"
echo "     → 填写助手的身份和性格"
echo "  2. 编辑 $WORKSPACE/memory/core.md"
echo "     → 填写你的环境信息和偏好"
echo "  3. 在 OpenClaw 对话框输入："
echo '     请执行初始化：读取所有配置文件，然后介绍你自己。'
echo "  4. 在 OpenClaw 设置 2 个 cron 任务："
echo "     每天 00:00 执行 /memory-evolution"
echo "     每周一 09:00 执行 /weekly-self-reflection"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
