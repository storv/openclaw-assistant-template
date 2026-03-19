#!/usr/bin/env python3
"""
evolve.py v3.7
- v3.5: 路径统一 .sys/logs/events.jsonl
- v3.6: 新增 update_growth_md()，error-found 纳入高频统计
- v3.7: BASE 改用 Path(__file__).parent.parent 动态推导（支持自定义 workspace 路径）
"""

import json
import re
import sys
from pathlib import Path
from collections import Counter
from datetime import datetime, timedelta, timezone

# 动态推导 workspace 根目录（v3.7：支持任意安装路径）
# __file__ = workspace/scripts/evolve.py
# parent   = workspace/scripts/
# parent.parent = workspace/
BASE = Path(__file__).parent.parent

MEM  = BASE / 'memory' / 'recent.md'
ERRS = BASE / 'memory' / 'errors.md'
GROW = BASE / 'memory' / 'growth.md'
LOGS = BASE / '.sys' / 'logs' / 'events.jsonl'

# 初始化必要目录
LOGS.parent.mkdir(parents=True, exist_ok=True)
for d in ['sessions', 'baseline', 'todo', 'compact']:
    (BASE / '.sys' / d).mkdir(parents=True, exist_ok=True)
(BASE / 'memory' / 'archive').mkdir(parents=True, exist_ok=True)


def load_recent_events(days=7):
    events = []
    now_naive_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff = now_naive_utc - timedelta(days=days)
    if not LOGS.exists():
        return events
    for line in LOGS.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
            if 'ts' not in e:
                continue
            event_dt = datetime.fromisoformat(e['ts'])
            naive_utc = event_dt.astimezone(timezone.utc).replace(tzinfo=None) if event_dt.tzinfo else event_dt
            if naive_utc >= cutoff:
                events.append(e)
        except (json.JSONDecodeError, ValueError, KeyError):
            pass
    return events


def search_memory(keyword: str, topn: int = 5):
    results = []
    if not LOGS.exists():
        return results
    kw = keyword.lower()
    for line in LOGS.read_text().splitlines():
        line = line.strip()
        if not line or kw not in line.lower():
            continue
        try:
            results.append(json.loads(line))
        except Exception:
            pass
    results.sort(key=lambda x: (x.get('count', 1), x.get('ts', '')), reverse=True)
    return results[:topn]


def extract_insights(events: list) -> dict:
    corrections  = [e for e in events if e.get('type') == 'user-correction']
    errors       = [e for e in events if e.get('type') in ('repeated-error', 'user-correction', 'bug-analysis', 'error-found')]
    capabilities = [e for e in events if e.get('type') in ('new-capability', 'learning-achievement')]
    preferences  = [e for e in events if e.get('type') == 'preference']

    error_counts = Counter()
    for e in errors:
        key = e.get('content', '')[:80]
        error_counts[key] += e.get('count', 1)
    frequent_errors = [e for e, c in error_counts.items() if c >= 2]

    all_tags = []
    for e in events:
        all_tags.extend(e.get('tags', e.get('tag', [])))
    tag_summary = Counter(all_tags).most_common(5)

    return {
        'corrections':      corrections,
        'frequent_errors':  frequent_errors,
        'new_capabilities': [e.get('content', '') for e in capabilities],
        'preferences':      [e.get('content', '') for e in preferences],
        'total_events':     len(events),
        'tag_summary':      tag_summary,
        'raw_capabilities': capabilities,
    }


def get_already_promoted_errors() -> list:
    if not ERRS.exists():
        return []
    content = ERRS.read_text()
    promoted_errors = []
    lines = content.split('\n')
    current_error = None
    for line in lines:
        if line.startswith('##') and '|' in line:
            current_error = line.split('|')[1][:80]
        elif current_error and '|' in line and 'promoted' in line:
            promoted_errors.append(current_error)
            current_error = None
    return promoted_errors


def update_memory(insights: dict):
    if not MEM.exists():
        MEM.parent.mkdir(parents=True, exist_ok=True)
        MEM.write_text('# Recent Memory\n')
    content = MEM.read_text()
    ts    = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
    total = insights['total_events']
    tag_line       = ', '.join(f'{t}×{c}' for t, c in insights['tag_summary']) or '-'
    corrections_text = '\n'.join(
        f'- {c.get("content", c.get("old","?"))[:80]} → {c.get("new","?")}' for c in insights['corrections']
    ) or '-'
    promoted_errors = get_already_promoted_errors()
    filtered_errors = [
        err for err in insights['frequent_errors']
        if not any(pe in err[:80] or err[:80] in pe for pe in promoted_errors)
    ]
    errors_text = '\n'.join(f'- {e}' for e in filtered_errors) or '-'
    caps_text   = '\n'.join(f'- {c[:100]}' for c in insights['new_capabilities']) or '-'
    prefs_text  = '\n'.join(f'- {p}' for p in insights['preferences']) or '-'

    section = (
        f'\n## {ts} | 近7天 {total} 条事件\n'
        f'**Tag摘要** - {tag_line}\n'
        f'**用户纠正**\n{corrections_text}\n'
        f'**高频错误**\n{errors_text}\n'  # 2次以上
        f'**新能力**\n{caps_text}\n'
        f'**偏好**\n{prefs_text}\n'
    )
    new_content = re.sub(r'\n## \d{4}-\d{2}-\d{2}.+?(?=\n## |\Z)', section, content, flags=re.DOTALL)
    if new_content == content:
        new_content = content + section
    MEM.write_text(new_content)
    print(f'[evolve] recent.md updated ({total} events), logs: {LOGS}')


def update_errors_md(insights: dict):
    if not insights['frequent_errors']:
        return
    if not ERRS.exists():
        ERRS.write_text('# Error Log\n')
    content = ERRS.read_text()
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    promoted_errors = get_already_promoted_errors()
    errors_to_process = [
        ec for ec in insights['frequent_errors']
        if not any(pe in ec[:80] or ec[:80] in pe for pe in promoted_errors)
    ]
    if not errors_to_process:
        return
    for err_content in errors_to_process:
        if err_content in content:
            content = re.sub(
                r'(- 出现次数：)(\d+)',
                lambda m: f'{m.group(1)}{int(m.group(2)) + 1}',
                content, count=1
            )
        else:
            content += (
                f'\n## {ts} | {err_content[:60]}\n'
                f'- 来源：events.jsonl 自动检测\n'
                f'- 原始内容：{err_content}\n'
                f'- 正确处理：（待补充）\n'
                f'- tag：auto-detected\n'
                f'- 出现次数：2\n'
                f'- 状态：pending\n'
            )
    ERRS.write_text(content)
    print(f'[evolve] errors.md updated ({len(errors_to_process)} items)')


def update_growth_md(insights: dict):
    """
    v3.6 新增：将 new-capability / learning-achievement 事件追加到 growth.md
    v3.7.2 修复两个 bug：
      1. 去重用事件原始 ts 日期（而非今天日期），避免历史事件每次重复追加
      2. 内容取首行不截断（split('\\n')[0]），避免换行破坏格式
    """
    if not insights.get('raw_capabilities'):
        return
    if not GROW.exists():
        GROW.parent.mkdir(parents=True, exist_ok=True)
        GROW.write_text(
            '# Growth Log\n\n'
            '_长期能力成长轨迹，由 evolve.py 自动追加_\n'
            '_格式：`- [YYYY-MM-DD] [event-type] content`_\n\n'
            '---\n\n'
        )
    content   = GROW.read_text()
    new_lines = []
    for e in insights['raw_capabilities']:
        # ✅ Bug1 修复：用事件原始 ts 日期，不用今天日期
        event_ts = e.get('ts', '')
        try:
            event_date = datetime.fromisoformat(event_ts).strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            event_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')

        # ✅ Bug2 修复：取内容首行，不截断，不破坏格式
        raw_content = e.get('content', '')
        first_line  = raw_content.split('\n')[0].strip()

        entry = f'- [{event_date}] [{e.get("type","")}] {first_line}'
        # 去重：检查事件原始日期+首行内容是否已存在
        if entry not in content:
            new_lines.append(entry)
    if new_lines:
        GROW.write_text(content + '\n'.join(new_lines) + '\n')
        print(f'[evolve] growth.md updated ({len(new_lines)} entries)')


def archive_if_needed():
    if not MEM.exists():
        return
    lines = MEM.read_text().splitlines()
    if len(lines) > 300:
        archive_path = BASE / f'memory/archive/{datetime.now(timezone.utc).strftime("%Y-%m")}.md'
        archive_path.write_text('\n'.join(lines))
        MEM.write_text('\n'.join(lines[-50:]))
        print(f'[evolve] archived to {archive_path}')


if __name__ == '__main__':
    print(f'[evolve] using logs: {LOGS}')
    if len(sys.argv) >= 2 and sys.argv[1] == 'search':
        if len(sys.argv) < 3:
            print('Usage: python3 evolve.py search <keyword> [topn]')
            sys.exit(1)
        keyword = sys.argv[2]
        topn    = int(sys.argv[3]) if len(sys.argv) >= 4 else 5
        results = search_memory(keyword, topn)
        if not results:
            print(f'No results for "{keyword}"')
        else:
            print(f'Top {len(results)} results for "{keyword}":')
            for r in results:
                tags = ', '.join(r.get('tag', []))
                print(f'  {r.get("ts","")} [{r.get("type","")}] count={r.get("count",1)}')
                print(f'    tags: {tags}')
                print(f'    {r.get("content","")[:100]}')
    else:
        events   = load_recent_events(7)
        insights = extract_insights(events)
        update_memory(insights)
        update_errors_md(insights)
        update_growth_md(insights)
        archive_if_needed()
        promoted_errors = get_already_promoted_errors()
        filtered = [
            err for err in insights['frequent_errors']
            if not any(pe in err[:80] or err[:80] in pe for pe in promoted_errors)
        ]
        if filtered:
            print(f'[evolve] Pending promotion: {filtered}')
        if insights['new_capabilities']:
            print(f'[evolve] New capabilities: {insights["new_capabilities"]}')
