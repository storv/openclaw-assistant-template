#!/usr/bin/env python3
"""
create_event.py v3.7.1
- v3.6: 路径统一 .sys/logs/events.jsonl
- v3.7: 修复中文概念单元计算（CN_UNIT_DIVISOR = 5）
- v3.7.1: --list-types 不再依赖 --type（required=False，独立执行）
"""

import json, sys, os, argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

STANDARD_TYPES = [
    'task-done', 'error-found', 'system-improvement', 'learning-achievement',
    'user-correction', 'automation-deployment', 'error-fix', 'system-monitoring',
    'quality-verification', 'new-capability', 'automation-planning',
    'memory-compaction', 'pua-inspection', 'quality-improvement',
]

MIN_CONTENT_LENGTH = {
    'learning-achievement': 15,
    'user-correction':      10,
    'task-done':             8,
    'error-found':           8,
    'system-improvement':   10,
    'default':               5,
}

TAG_RULES = {
    'learning-achievement': ['learning'],
    'user-correction':      ['user-interaction', 'feedback'],
    'task-done':            ['task-completion', 'progress'],
    'error-found':          ['error-detection', 'monitoring'],
    'system-improvement':   ['improvement', 'optimization'],
    'automation-deployment':['automation', 'deployment'],
    'error-fix':            ['error-resolution', 'fixing'],
    'quality-verification': ['quality-check', 'verification'],
    'pua-inspection':       ['pua-mode', 'deep-inspection', 'architecture-check'],
}

# 中文概念单元除数（v3.7）
# 英文：1词 = 1单元；中文：5字 = 1单元（75汉字 ≈ 15英文词）
CN_UNIT_DIVISOR = 5


def validate_event_type(t: str) -> bool:
    return t in STANDARD_TYPES


def validate_content(content: str, event_type: str) -> bool:
    if not content or not content.strip():
        return False
    cs = content.strip()
    has_cn = any('\u4e00' <= c <= '\u9fff' for c in cs)
    units = len(cs) / CN_UNIT_DIVISOR if has_cn else len(cs.split())
    return units >= MIN_CONTENT_LENGTH.get(event_type, MIN_CONTENT_LENGTH['default'])


def get_content_units(content: str) -> float:
    cs = content.strip()
    has_cn = any('\u4e00' <= c <= '\u9fff' for c in cs)
    return len(cs) / CN_UNIT_DIVISOR if has_cn else len(cs.split())


def generate_tags(event_type: str, content: str, user_tags: List[str] = None) -> List[str]:
    tags = list(TAG_RULES.get(event_type, []))
    if user_tags:
        tags.extend(user_tags)
    kws = {
        'monitoring': ['monitor', 'check', 'verify', 'inspect'],
        'automation': ['auto', 'script', 'cron', 'schedule'],
        'quality':    ['quality', 'fix', 'improve', 'enhance'],
        'error':      ['error', 'bug', 'issue', 'problem'],
        'learning':   ['learn', 'study', 'understand', 'master'],
        'user':       ['user', 'human', 'feedback', 'request'],
        'system':     ['system', 'architecture', 'design'],
        'data':       ['data', 'log', 'record', 'event'],
    }
    cl = content.lower()
    for tag, words in kws.items():
        if any(w in cl for w in words) and tag not in tags:
            tags.append(tag)
    seen, unique = set(), []
    for t in tags:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return unique or [event_type.replace('-', '_')]


def create_standard_event(event_type, content, tags=None, count=1, extra=None):
    if not validate_event_type(event_type):
        print(f"❌ 非标准类型: {event_type}")
        print(f"   支持的类型：{', '.join(STANDARD_TYPES)}")
        return None
    if not validate_content(content, event_type):
        required = MIN_CONTENT_LENGTH.get(event_type, MIN_CONTENT_LENGTH['default'])
        actual   = get_content_units(content)
        print(f"❌ 内容质量不足：需要 {required} 个概念单元，当前约 {actual:.1f} 个")
        cs = content.strip()
        has_cn = any('\u4e00' <= c <= '\u9fff' for c in cs)
        if has_cn:
            print(f"   提示：中文需约 {required * CN_UNIT_DIVISOR} 个汉字，当前 {len(cs)} 个汉字")
        else:
            print(f"   提示：英文需约 {required} 个单词，当前 {len(cs.split())} 个单词")
        return None
    event = {
        'ts':      datetime.now(timezone.utc).isoformat(),
        'type':    event_type,
        'content': content.strip(),
        'tags':    generate_tags(event_type, content, tags),
        'count':   count,
    }
    if extra:
        event['extra'] = extra
    print(f"✅ 事件创建成功：{event_type}")
    return event


def append_event_to_file(event, output_file=None):
    if output_file:
        filepath = Path(output_file)
    else:
        filepath = Path(__file__).parent.parent / '.sys' / 'logs' / 'events.jsonl'
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    print(f"📁 已保存到：{filepath}")
    return True


def main():
    parser = argparse.ArgumentParser(description='标准化事件创建工具 v3.7.1')
    # v3.7.1：--type 改为非必填，--list-types 时无需提供
    parser.add_argument('--type',       required=False, default=None)
    parser.add_argument('--content',    required=False, nargs='+', default=None)
    parser.add_argument('--tags',       default=None)
    parser.add_argument('--count',      type=int, default=1)
    parser.add_argument('--extra',      default=None)
    parser.add_argument('--file',       default=None)
    parser.add_argument('--list-types', action='store_true')
    args = parser.parse_args()

    # --list-types 独立执行，不依赖 --type
    if args.list_types:
        print("支持的标准事件类型：")
        for t in STANDARD_TYPES:
            req = MIN_CONTENT_LENGTH.get(t, MIN_CONTENT_LENGTH['default'])
            print(f"  {t:<30} 最低 {req:>2} 概念单元（中文约 {req * CN_UNIT_DIVISOR:>3} 字）")
        return 0

    # 非 --list-types 模式：--type 和 --content 必填
    if not args.type:
        parser.error("请提供 --type 参数，或使用 --list-types 查看所有类型")
    if not args.content:
        parser.error("请提供 --content 参数")

    tags  = [t.strip() for t in args.tags.split(',')] if args.tags else None
    extra = None
    if args.extra:
        extra = {}
        for pair in args.extra.split(','):
            if ':' in pair:
                k, v = pair.split(':', 1)
                extra[k.strip()] = v.strip()

    event = create_standard_event(
        args.type, ' '.join(args.content), tags, args.count, extra
    )
    if event:
        append_event_to_file(event, args.file)
        return 0
    return 1


if __name__ == '__main__':
    sys.exit(main())
