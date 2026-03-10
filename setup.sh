#!/bin/bash
set -e

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
err()  { echo -e "${RED}❌ $1${NC}"; exit 1; }
info() { echo -e "${CYAN}$1${NC}"; }

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  内网数字助手 — 初始化脚本 v2.3"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 确保在仓库根目录运行 ──────────────────────
REPO_DIR="$(pwd)"
if [ ! -d "$REPO_DIR/workspace" ]; then
  err "请在仓库根目录运行此脚本（当前目录找不到 workspace/）\n请先执行：cd openclaw-assistant-template"
fi
ok "仓库根目录：$REPO_DIR"

# ── 部署路径 ──────────────────────────────────
WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
echo ""
echo "部署路径：$WORKSPACE"

# 终端环境询问确认，非交互式环境自动跳过
if [ -t 0 ]; then
  read -p "确认部署到此路径？(y/N) " confirm
  [[ "$confirm" =~ ^[Yy]$ ]] || { warn "已取消"; exit 0; }
else
  ok "非交互式环境，自动确认"
fi

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
  local src="$1" dst="$2"
  if [ ! -f "$src" ]; then
    warn "源文件不存在，跳过：$(basename "$src")"; return
  fi
  if [ -f "$dst" ]; then
    warn "已存在，跳过：$(basename "$dst")"
  else
    cp "$src" "$dst" && ok "已复制：$(basename "$dst")"
  fi
}

copy_if_new "$REPO_DIR/workspace/IDENTITY.md"       "$WORKSPACE/IDENTITY.md"
copy_if_new "$REPO_DIR/workspace/AGENTS.md"         "$WORKSPACE/AGENTS.md"
copy_if_new "$REPO_DIR/workspace/memory/core.md"    "$WORKSPACE/memory/core.md"
copy_if_new "$REPO_DIR/workspace/memory/project.md" "$WORKSPACE/memory/project.md"
copy_if_new "$REPO_DIR/workspace/memory/recent.md"  "$WORKSPACE/memory/recent.md"

for f in "$REPO_DIR/workspace/skills/"*.md; do
  [ -f "$f" ] && copy_if_new "$f" "$WORKSPACE/skills/$(basename "$f")"
done

# ── 第二类：脚本文件，已存在则备份后更新 ──────
copy_with_backup() {
  local src="$1" dst="$2"
  if [ ! -f "$src" ]; then
    warn "源文件不存在，跳过：$(basename "$src")"; return
  fi
  if [ -f "$dst" ]; then
    cp "$dst" "${dst}.bak.$(date +%Y%m%d_%H%M%S)"
    warn "已备份旧版本：$(basename "$dst")"
  fi
  cp "$src" "$dst" && ok "已更新：$(basename "$dst")"
}

copy_with_backup "$REPO_DIR/workspace/scripts/evolve.py"       "$WORKSPACE/scripts/evolve.py"
copy_with_backup "$REPO_DIR/workspace/scripts/baseline.sh"     "$WORKSPACE/scripts/baseline.sh"
copy_with_backup "$REPO_DIR/workspace/scripts/health-check.sh" "$WORKSPACE/scripts/health-check.sh"
chmod +x "$WORKSPACE/scripts/"*.sh "$WORKSPACE/scripts/evolve.py"
ok "脚本文件已部署并赋权"

# ── 初始化日志文件 ─────────────────────────────
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
  echo "export WORKSPACE=\"$WORKSPACE\"" >> "$RC_FILE"
  ok "已写入 WORKSPACE 到 $RC_FILE"
else
  warn "WORKSPACE 已存在于 $RC_FILE，跳过"
fi
export WORKSPACE="$WORKSPACE"

# ── 验证关键文件 ───────────────────────────────
echo ""
echo "── 部署验证 ──────────────────────────"
DEPLOY_ERR=""
check_file() {
  if [ -f "$1" ]; then echo "OK  $1"
  else echo "ERR 缺失：$1"; DEPLOY_ERR=1; fi
}
check_file "$WORKSPACE/IDENTITY.md"
check_file "$WORKSPACE/AGENTS.md"
check_file "$WORKSPACE/memory/core.md"
check_file "$WORKSPACE/memory/project.md"
check_file "$WORKSPACE/memory/recent.md"
check_file "$WORKSPACE/scripts/evolve.py"
check_file "$WORKSPACE/scripts/health-check.sh"
[ -n "$DEPLOY_ERR" ] && err "部分文件缺失，请检查仓库结构是否完整"
ok "所有关键文件就位"

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
echo "── 健康检查 ──────────────────────────"
WORKSPACE="$WORKSPACE" bash "$WORKSPACE/scripts/health-check.sh"

# ── 输出激活提示词 ─────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ok "部署完成！"
info "\n把下面这段话复制到 OpenClaw 对话框，开始激活 👇\n"
cat << 'PROMPT'
┌─────────────────────────────────────────────────────────┐

请读取以下文件完成初始化：
IDENTITY.md、AGENTS.md、memory/core.md、
memory/project.md、memory/recent.md
以及 skills/ 下所有文件。

读取完成后，请依次问我以下问题来完善你的设定：

🤖 关于你自己：
1. 给你起个名字 — 你想叫什么？
2. 你的性格风格 — 直接/温和/幽默/严谨，或者自由描述
3. 有什么口头禅或特别的表达习惯吗？（没有可跳过）

👤 关于我：
4. 叫我什么，你在哪个时区？
5. 你的工作场景和日常使用偏好是什么？
6. 希望我重点协助哪些方面？

收集完以上信息后，请：
- 将助手设定写入 IDENTITY.md
- 将用户信息写入 memory/core.md
- 执行 /remember 和 /session-notes

完成以上步骤后，请立即创建以下 2 个定时任务：
1. 每天 00:00 执行 /memory-evolution
   （每日自动整理学习记录，触发进化建议）
2. 每周一 09:00 执行 /weekly-self-reflection
   （每周复盘，生成规则优化建议）

定时任务创建完成后，请：
- 确认两个任务已成功注册并报告状态
- 做一个简短的自我介绍，确认全部初始化完成

└─────────────────────────────────────────────────────────┘
PROMPT

info "\n初始化完成后助手会自动设置定时任务，无需额外操作。"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
