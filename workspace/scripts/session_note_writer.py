#!/usr/bin/env python3
"""
session_note_writer.py v3.6
修复：写入路径统一为 .sys/logs/events.jsonl（v3.5 错误写入 .openclaw/logs/）
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── 唯一权威路径（与 create_event.py、evolve.py 保持一致）──────────
BASE       = Path.home() / ".openclaw/workspace"
EVENTS_LOG = BASE / ".sys/logs/events.jsonl"   # ✅ 正确路径
SESSIONS   = BASE / ".sys/sessions"

EVENTS_LOG.parent.mkdir(parents=True, exist_ok=True)
SESSIONS.mkdir(parents=True, exist_ok=True)


def append_event(event_type: str, content: str, tags: list = None, count: int = 1):
    """写入一条事件到 .sys/logs/events.jsonl（唯一路径）"""
    record = {
        "ts":      datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "type":    event_type,
        "tag":     tags or [],
        "content": content,
        "count":   count,
    }
    with EVENTS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"[session_note_writer] event written → {EVENTS_LOG}")


def save_session_notes(session_id: str, content: str):
    """保存会话摘要到 .sys/sessions/"""
    ts   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = SESSIONS / f"{ts}_{session_id}.md"
    path.write_text(content, encoding="utf-8")
    print(f"[session_note_writer] session saved → {path}")
    return path


if __name__ == "__main__":
    # 快速测试
    append_event("system-monitoring", "session_note_writer v3.6 路径修复验证", ["test"])
    print("✅ 路径验证完成，事件写入 .sys/logs/events.jsonl")
