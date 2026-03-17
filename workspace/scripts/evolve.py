#!/usr/bin/env python3
"""
evolve.py v3.5
- v3.4基础上修复：统一使用 .sys/logs/events.jsonl，删除自动路径探测逻辑
"""

import json
import re
import sys
from pathlib import Path
from collections import Counter
from datetime import datetime, timedelta, timezone

BASE = Path.home() / ".openclaw/workspace"
MEM = BASE / "memory/recent.md"
ERRS = BASE / "memory/errors.md"

LOGS = BASE / ".sys/logs/events.jsonl"
LOGS.parent.mkdir(parents=True, exist_ok=True)

for _d in ["sessions", "baseline", "todo", "compact"]:
    (BASE / ".sys" / _d).mkdir(parents=True, exist_ok=True)
(BASE / "memory/archive").mkdir(parents=True, exist_ok=True)


def _to_naive_utc(dt: datetime) -> datetime:
    """统一转为 UTC naive datetime，避免 aware/naive 混合比较报错。

    规则：
    1. 如果输入datetime有时区，转换为UTC再移除时区信息
    2. 如果输入datetime无时区，直接返回（假设已经是UTC时间）

    注意：此函数假设所有naive时间都是UTC时间，这适用于OpenClaw系统。
    对于带其他时区的时间，此转换确保正确处理。
    """
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def load_recent_events(days=7):

    events = []
    # 统一使用UTC naive时间，避免aware/naive混合比较
    now_naive_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff = now_naive_utc - timedelta(days=days)

    # 注意：使用UTC时间计算7天前边界，适合分布式系统
    # 所有事件时间应转换为UTC naive进行比较
    # 边界情况：事件时间与cutoff接近时（相差<1秒）默认保留

    if not LOGS.exists():
        return events

    loaded_count = 0
    failed_count = 0

    for line in LOGS.read_text().splitlines():
        line = line.strip()
        if not line:
            continue

        try:
            e = json.loads(line)
            # 检查必需字段
            if "ts" not in e:
                failed_count += 1
                continue

            event_dt = datetime.fromisoformat(e["ts"])

            # 处理时区：转换为naive UTC
            if event_dt.tzinfo is not None:
                # 带时区：转换为UTC再移除时区
                naive_utc = event_dt.astimezone(timezone.utc).replace(tzinfo=None)
            else:
                # 无时区：假设为系统使用的UTC时间
                naive_utc = event_dt

            if naive_utc >= cutoff:
                events.append(e)
                loaded_count += 1
            # else: 事件过期，不记录

        except json.JSONDecodeError:
            failed_count += 1
            # 跳过无效JSON行
        except ValueError as e:
            failed_count += 1
            # 时间戳解析失败
        except KeyError as e:
            failed_count += 1
            # 缺少必需字段

    # 可选：显示调试信息
    # if failed_count > 0:
    #     print(f"[evolve] 加载统计: {loaded_count}成功, {failed_count}失败")

    return events


def append_event(type_: str, content: str, tags: list, count: int = 1, extra: dict = None):
    """写入一条标准化事件到 events.jsonl，时间戳带 UTC 时区。"""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "type": type_,
        "tag": tags,
        "content": content,
        "count": count,
    }
    if extra:
        record.update(extra)
    with LOGS.open("a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def search_memory(keyword: str, top_n: int = 5) -> list:
    """逐行扫描 events.jsonl，按 count 降序返回匹配结果。"""
    results = []
    if not LOGS.exists():
        return results
    kw = keyword.lower()
    for line in LOGS.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        if kw in line.lower():
            try:
                results.append(json.loads(line))
            except Exception:
                pass
    results.sort(key=lambda x: (x.get("count", 1), x.get("ts", "")), reverse=True)
    return results[:top_n]


def extract_insights(events: list) -> dict:
    corrections = [e for e in events if e.get("type") == "user-correction"]
    errors = [e for e in events if e.get("type") in ("repeated-error", "user-correction", "bug-analysis")]
    # 修复: new-capability已映射为learning-achievement (PUA第4轮修复 2026-03-15)
    capabilities = [e for e in events if e.get("type") in ("new-capability", "learning-achievement")]
    preferences = [e for e in events if e.get("type") == "preference"]

    error_counts = Counter()
    for e in errors:
        key = e.get("content", "")[:80]
        error_counts[key] += e.get("count", 1)

    frequent_errors = [e for e, c in error_counts.items() if c >= 2]

    all_tags = []
    for e in events:
        # 修复: 字段名应为tags而非tag (PUA第4轮修复 2026-03-15)
        all_tags.extend(e.get("tags", e.get("tag", [])))
    tag_summary = Counter(all_tags).most_common(5)

    return {
        "corrections": corrections,
        "frequent_errors": frequent_errors,
        "new_capabilities": [e.get("content", "") for e in capabilities],
        "preferences": [e.get("content", "") for e in preferences],
        "total_events": len(events),
        "tag_summary": tag_summary,
    }


def get_already_promoted_errors() -> list:
    """从errors.md获取已标记为promoted的错误列表"""
    if not ERRS.exists():
        return []

    content = ERRS.read_text()
    promoted_errors = []

    # 查找所有状态为promoted的错误
    lines = content.split('\n')
    current_error = None

    for i, line in enumerate(lines):
        if line.startswith('## ['):
            # 错误标题行
            if '] ' in line:
                current_error = line.split('] ')[1][:80]

        elif current_error and '状态' in line and 'promoted' in line:
            # 发现promoted状态
            promoted_errors.append(current_error)
            current_error = None

    return promoted_errors


def update_memory(insights: dict):
    if not MEM.exists():
        print("[evolve] recent.md not found, skipped")
        return
    content = MEM.read_text()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    total = insights["total_events"]
    tag_line = ", ".join(f"{t}x{c}" for t, c in insights["tag_summary"]) or "-"

    corrections_text = "\n".join(
        # 修复: user-correction事件用content字段，无old/new字段 (PUA第4轮修复 2026-03-15)
        f"- {c.get('content', c.get('old','?') + ' -> ' + c.get('new','?'))[:80]}"
        for c in insights["corrections"]
    ) or "- 无"

    # 过滤掉已promoted的错误
    promoted_errors = get_already_promoted_errors()
    filtered_errors = []
    for err in insights["frequent_errors"]:
        is_promoted = False
        for promoted_err in promoted_errors:
            if promoted_err in err[:80] or err[:80] in promoted_err:
                is_promoted = True
                break
        if not is_promoted:
            filtered_errors.append(err)

    errors_text = "\n".join(f"- {e}" for e in filtered_errors) or "- 无"
    caps_text = "\n".join(f"- {c[:100]}" for c in insights["new_capabilities"]) or "- 无"
    prefs_text = "\n".join(f"- {p}" for p in insights["preferences"]) or "- 无"

    section = (
        f"\n## [{ts}] 进化摘要（近7天 {total} 事件）\n\n"
        f"### 高频 Tag\n- {tag_line}\n\n"
        f"### 用户纠正\n{corrections_text}\n\n"
        f"### 高频错误（>=2次，待晋升）\n{errors_text}\n\n"
        f"### 新能力\n{caps_text}\n\n"
        f"### 用户偏好\n{prefs_text}\n"
    )

    new_content = re.sub(
        r"## \[\d{4}-\d{2}-\d{2}.*?(?=## \[|\Z)",
        section,
        content,
        flags=re.DOTALL,
    )

    if new_content == content:
        new_content = content + section
    MEM.write_text(new_content)
    print(f"[evolve] recent.md updated ({total} events, logs: {LOGS})")


def update_errors_md(insights: dict):
    if not insights["frequent_errors"]:
        return
    if not ERRS.exists():
        ERRS.write_text("# Error Log\n\n")

    content = ERRS.read_text()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 过滤掉已promoted的错误
    promoted_errors = get_already_promoted_errors()
    errors_to_process = []

    for err_content in insights["frequent_errors"]:
        is_promoted = False
        for promoted_err in promoted_errors:
            if promoted_err in err_content[:80] or err_content[:80] in promoted_err:
                is_promoted = True
                break
        if not is_promoted:
            errors_to_process.append(err_content)

    if not errors_to_process:
        # 所有错误都已promoted
        return

    for err_content in errors_to_process:
        if err_content in content:
            content = re.sub(
                r"(- \*\*出现次数\*\*：)(\d+)",
                lambda m: f"{m.group(1)}{int(m.group(2)) + 1}",
                content,
                count=1,
            )
            content = content.replace("monitoring", "pending")
        else:
            content += (
                f"\n## [{ts}] {err_content[:60]}\n"
                f"- **触发场景**：自动检测（events.jsonl）\n"
                f"- **错误行为**：{err_content}\n"
                f"- **正确处理**：待人工补充\n"
                f"- **tag**：[auto-detected]\n"
                f"- **出现次数**：2\n"
                f"- **状态**：pending\n"
            )

    ERRS.write_text(content)
    print(f"[evolve] errors.md updated: {len(errors_to_process)} items")


def archive_if_needed():
    if not MEM.exists():
        return
    lines = MEM.read_text().splitlines()
    if len(lines) > 300:
        archive_path = BASE / f"memory/archive/{datetime.now(timezone.utc).strftime('%Y-%m')}.md"
        archive_path.write_text("\n".join(lines))
        MEM.write_text("\n".join(lines[-50:]))
        print(f"[evolve] archived to {archive_path}")


if __name__ == "__main__":
    print(f"[evolve] using logs: {LOGS}")

    if len(sys.argv) >= 2 and sys.argv[1] == "search":
        if len(sys.argv) < 3:
            print("Usage: python3 evolve.py search <keyword> [top_n]")
            sys.exit(1)
        keyword = sys.argv[2]
        top_n = int(sys.argv[3]) if len(sys.argv) >= 4 else 5
        results = search_memory(keyword, top_n)
        if not results:
            print(f"No results for: {keyword}")
        else:
            print(f"Top {len(results)} results for '{keyword}':\n")
            for r in results:
                tags = ", ".join(r.get("tag", []))
                print(f"[{r.get('ts','')}] [{r.get('type','')}] count={r.get('count',1)}")
                print(f"  tags: {tags}")
                print(f"  {r.get('content','')}\n")
    else:
        # 主执行逻辑
        events = load_recent_events(7)
        insights = extract_insights(events)
        update_memory(insights)
        update_errors_md(insights)
        archive_if_needed()

        # 显示提示信息（过滤掉已promoted的错误）
        promoted_errors = get_already_promoted_errors()
        filtered_frequent_errors = []
        for err in insights["frequent_errors"]:
            is_promoted = False
            for promoted_err in promoted_errors:
                if promoted_err in err[:80] or err[:80] in promoted_err:
                    is_promoted = True
                    break
            if not is_promoted:
                filtered_frequent_errors.append(err)

        if filtered_frequent_errors:
            print(f"[evolve] Pending promotion: {filtered_frequent_errors}")
        else:
            # 检查是否有已promoted但仍在列表中的错误
            if insights["frequent_errors"]:
                promoted_count = len(insights["frequent_errors"]) - len(filtered_frequent_errors)
                if promoted_count > 0:
                    print(f"[evolve] Note: {promoted_count} error(s) already promoted, skipped")

        if insights["new_capabilities"]:
            print(f"[evolve] New capabilities: {insights['new_capabilities']}")
