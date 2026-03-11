#!/bin/bash
BASE="${WORKSPACE:-$HOME/.openclaw/workspace}"
DATE=$(date +%Y-%m-%d)

# 自动检测运行时目录
RUNTIME_DIR=""
for candidate in "$BASE/.sys" "$BASE/.openclaw"; do
  if [ -d "$candidate/logs" ]; then
    RUNTIME_DIR="$candidate"
    break
  fi
done
[ -z "$RUNTIME_DIR" ] && RUNTIME_DIR="$BASE/.sys"

LOG="$RUNTIME_DIR/baseline/baseline-$DATE.log"
mkdir -p "$RUNTIME_DIR/baseline"

{
  echo "=== Baseline $DATE ==="
  echo "--- runtime dir: $RUNTIME_DIR ---"
  echo "--- memory/recent.md lines ---"
  wc -l "$BASE/memory/recent.md" 2>/dev/null
  echo "--- memory/project.md lines ---"
  wc -l "$BASE/memory/project.md" 2>/dev/null
  echo "--- AGENTS.md lines ---"
  wc -l "$BASE/AGENTS.md" 2>/dev/null
  echo "--- skills count ---"
  ls "$BASE/skills" 2>/dev/null | wc -l
  echo "--- events.jsonl lines ---"
  wc -l "$RUNTIME_DIR/logs/events.jsonl" 2>/dev/null
  echo "--- error counts ---"
  grep -c "repeated-error" "$RUNTIME_DIR/logs/events.jsonl" 2>/dev/null || echo 0
  grep -c "new-capability"  "$RUNTIME_DIR/logs/events.jsonl" 2>/dev/null || echo 0
} > "$LOG"

HISTORY=$(ls "$RUNTIME_DIR/baseline/" | grep -v "$DATE" | sort | tail -1)
if [ -n "$HISTORY" ]; then
  echo "--- diff from last baseline ---" >> "$LOG"
  diff "$RUNTIME_DIR/baseline/$HISTORY" "$LOG" >> "$LOG" 2>/dev/null || true
fi

cat "$LOG"
