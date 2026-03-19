#!/usr/bin/env python3
"""
evolve.py v3.6
职责：读取 .sys/logs/events.jsonl，提炼写入 recent.md / errors.md / growth.md
- 不写入事件（事件写入统一由 create_event.py 负责）
- 路径唯一：.sys/logs/events.jsonl，不读写 .openclaw/logs/
"""

import json
import re
import sys
from pathlib import Path
from collections import Counter
from datetime import datetime, timedelta, timezone

BASE   = Path.home() / ".openclaw/workspace"
MEM    = BASE / "memory/recent.md"
ERRS   = BASE / "memory/errors.md"
GROWTH = BASE / "memory/growth.md"

# ── 唯一权威路径，不做任何自动探测 ──────────────────────────────────
LOGS = BASE / ".sys/logs/events.jsonl"
LOGS.parent.mkdir(parents=True, exist_ok=True)

for _d in ["sessions", "baseline", "todo", "compact"]:
    (BASE / ".sys" / _d).mkdir(parents=True, exist_ok=True)
(BASE / "memory/archive").mkdir(parents=True, exist_ok=True)


# ── 事件加载 ─────────────────────────────────────────────────────────

def load_recent_events(days: int = 7) -> list:
    events = []
    if not LOGS.exists():
        print(f"[evolve] ⚠️  日志文件不存在: {LOGS}")
        return events

    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    failed = 0

    for line in LOGS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
            if "ts" not in e:
                failed += 1
                continue
            dt = datetime.fromisoformat(e["ts"])
            naive = dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt
            if naive >= cutoff:
                events.append(e)
        except (json.JSONDecodeError, ValueError, KeyError):
            failed += 1

    if failed:
        print(f"[evolve] ⚠️  跳过 {failed} 条格式异常记录")
    return events


# ── 洞察提炼 ─────────────────────────────────────────────────────────

def extract_insights(events: list) -> dict:
    corrections  = [e for e in events if e.get("type") == "user-correction"]
    errors       = [e for e in events if e.get("type") in (
                    "repeated-error", "user-correction", "bug-analysis", "error-found")]
    capabilities = [e for e in events if e.get("type") in ("new-capability", "learning-achievement")]
    preferences  = [e for e in events if e.get("type") == "preference"]

    error_counts = Counter()
    for e in errors:
        key = e.get("content", "")[:80]
        error_counts[key] += e.get("count", 1)
    frequent_errors = [e for e, c in error_counts.items() if c >= 2]

    all_tags = []
    for e in events:
        all_tags.extend(e.get("tags", e.get("tag", [])))
    tag_summary = Counter(all_tags).most_common(5)

    return {
        "corrections":      corrections,
        "frequent_errors":  frequent_errors,
        "new_capabilities": [(e.get("content", ""), e.get("ts", "")) for e in capabilities],
        "preferences":      [e.get("content", "") for e in preferences],
        "total_events":     len(events),
        "tag_summary":      tag_summary,
    }


# ── errors.md 辅助 ───────────────────────────────────────────────────

def get_already_promoted_errors() -> list:
    if not ERRS.exists():
        return []
    promoted = []
    current = None
    for line in ERRS.read_text(encoding="utf-8").splitlines():
        if line.startswith("## [") and "] " in line:
            current = line.split("] ", 1)[1][:80]
        elif current and "状态" in line and "promoted" in line:
            promoted.append(current)
            current = None
    return promoted


# ── recent.md ────────────────────────────────────────────────────────

def update_memory(insights: dict):
    if not MEM.exists():
        MEM.parent.mkdir(parents=True, exist_ok=True)
        MEM.write_text("# Recent Memory\n\n", encoding="utf-8")
    content = MEM.read_text(encoding="utf-8")

    ts    = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    total = insights["total_events"]
    tag_line = ", ".join(f"{t}×{c}" for t, c in insights["tag_summary"]) or "-"

    corrections_text = "\n".join(
        f"- {c.get('content', c.get('old','?') + ' → ' + c.get('new','?'))[:80]}"
        for c in insights["corrections"]
    ) or "- 无"

    promoted = get_already_promoted_errors()
    filtered = [e for e in insights["frequent_errors"]
                if not any(pe in e[:80] or e[:80] in pe for pe in promoted)]
    errors_text = "\n".join(f"- {e}" for e in filtered) or "- 无"
    caps_text   = "\n".join(f"- {c[:100]}" for c, _ in insights["new_capabilities"]) or "- 无"
    prefs_text  = "\n".join(f"- {p}" for p in insights["preferences"]) or "- 无"

    section = (
        f"\n## [{ts}] 进化摘要（近7天 {total} 事件）\n\n"
        f"### 高频 Tag\n- {tag_line}\n\n"
        f"### 用户纠正\n{corrections_text}\n\n"
        f"### 高频错误（≥2次，待晋升）\n{errors_text}\n\n"
        f"### 新能力\n{caps_text}\n\n"
        f"### 用户偏好\n{prefs_text}\n"
    )

    new_content = re.sub(
        r"## \[\d{4}-\d{2}-\d{2}.*?(?=## \[|\Z)",
        section, content, flags=re.DOTALL,
    )
    if new_content == content:
        new_content = content + section
    MEM.write_text(new_content, encoding="utf-8")
    print(f"[evolve] recent.md updated ({total} events)")


# ── errors.md ────────────────────────────────────────────────────────

def update_errors_md(insights: dict):
    if not insights["frequent_errors"]:
        return
    if not ERRS.exists():
        ERRS.write_text("# Error Log\n\n", encoding="utf-8")

    content  = ERRS.read_text(encoding="utf-8")
    ts       = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    promoted = get_already_promoted_errors()
    to_process = [
        ec for ec in insights["frequent_errors"]
        if not any(pe in ec[:80] or ec[:80] in pe for pe in promoted)
    ]
    if not to_process:
        return

    for err in to_process:
        if err[:60] in content:
            content = re.sub(
                r"(- \*\*出现次数\*\*：)(\d+)",
                lambda m: f"{m.group(1)}{int(m.group(2)) + 1}",
                content, count=1,
            )
            content = content.replace("monitoring", "pending")
        else:
            content += (
                f"\n## [{ts}] {err[:60]}\n"
                f"- **触发场景**：自动检测（events.jsonl）\n"
                f"- **错误行为**：{err}\n"
                f"- **正确处理**：待人工补充\n"
                f"- **tag**：[auto-detected]\n"
                f"- **出现次数**：2\n"
                f"- **状态**：pending\n"
            )

    ERRS.write_text(content, encoding="utf-8")
    print(f"[evolve] errors.md updated: {len(to_process)} items")


# ── growth.md ────────────────────────────────────────────────────────

def update_growth_md(insights: dict):
    """将本次进化中出现的新能力追加写入 growth.md（去重）"""
    if not insights["new_capabilities"]:
        return
    if not GROWTH.exists():
        GROWTH.parent.mkdir(parents=True, exist_ok=True)
        GROWTH.write_text(
            "# Growth Log\n_长期能力成长轨迹，由 evolve.py 自动追加_\n\n",
            encoding="utf-8"
        )
    content = GROWTH.read_text(encoding="utf-8")
    added = 0
    for cap_content, cap_ts in insights["new_capabilities"]:
        if cap_content[:60] not in content:
            entry = f"- [{cap_ts[:10]}] {cap_content[:120]}\n"
            content += entry
            added += 1
    if added:
        GROWTH.write_text(content, encoding="utf-8")
        print(f"[evolve] growth.md updated: +{added} capabilities")


# ── 归档 ─────────────────────────────────────────────────────────────

def archive_if_needed():
    if not MEM.exists():
        return
    lines = MEM.read_text(encoding="utf-8").splitlines()
    if len(lines) > 300:
        archive_path = BASE / f"memory/archive/{datetime.now(timezone.utc).strftime('%Y-%m')}.md"
        archive_path.write_text("\n".join(lines), encoding="utf-8")
        MEM.write_text("\n".join(lines[-50:]), encoding="utf-8")
        print(f"[evolve] archived to {archive_path}")


# ── 搜索 ─────────────────────────────────────────────────────────────

def search_memory(keyword: str, top_n: int = 5) -> list:
    results = []
    if not LOGS.exists():
        return results
    kw = keyword.lower()
    for line in LOGS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or kw not in line.lower():
            continue
        try:
            results.append(json.loads(line))
        except Exception:
            pass
    results.sort(key=lambda x: (x.get("count", 1), x.get("ts", "")), reverse=True)
    return results[:top_n]


# ── 入口 ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"[evolve] using logs: {LOGS}")

    if len(sys.argv) >= 2 and sys.argv[1] == "search":
        if len(sys.argv) < 3:
            print("用法: python3 evolve.py search <keyword> [top_n]")
            sys.exit(1)
        keyword = sys.argv[2]
        top_n   = int(sys.argv[3]) if len(sys.argv) >= 4 else 5
        results = search_memory(keyword, top_n)
        if not results:
            print(f"无结果：{keyword}")
        else:
            print(f"Top {len(results)} 结果（关键词：{keyword}）:\n")
            for r in results:
                tags = ", ".join(r.get("tag", r.get("tags", [])))
                print(f"[{r.get('ts','')}] [{r.get('type','')}] count={r.get('count',1)}")
                print(f"  tags: {tags}")
                print(f"  {r.get('content','')}\n")
    else:
        events   = load_recent_events(7)
        insights = extract_insights(events)
        update_memory(insights)
        update_errors_md(insights)
        update_growth_md(insights)
        archive_if_needed()

        promoted = get_already_promoted_errors()
        pending  = [e for e in insights["frequent_errors"]
                    if not any(pe in e[:80] or e[:80] in pe for pe in promoted)]
        if pending:
            print(f"[evolve] 待晋升错误: {pending}")
        if insights["new_capabilities"]:
            print(f"[evolve] 新能力: {[c for c, _ in insights['new_capabilities']]}")
