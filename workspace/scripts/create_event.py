#!/usr/bin/env python3
"""
标准化事件创建工具
解决PUA第2轮检查发现的：手动创建事件导致质量倒退问题

功能：
1. 确保所有事件都通过标准化工具创建
2. 自动Tags智能生成（无法缺失Tags）
3. 类型合法性验证（防止非标类型）
4. 时区自动标准化（确保UTC）
5. 内容质量检查（防止内容空洞）
6. Schema一致性保证（标准字段格式）

使用方式：
python3 create_event.py [--type TYPE] [--content CONTENT] [--tags TAG1,TAG2]
                        [--count COUNT] [--extra KEY:VALUE] [--file OUTPUT_FILE]
"""

import json
import sys
import os
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

# 标准事件类型列表（参考AGENTS.md和已有实践）
STANDARD_TYPES = [
    'task-done',             # 完成任务
    'error-found',           # 发现错误
    'system-improvement',    # 系统改进
    'learning-achievement',  # 学习成就（**必须高质量内容**）
    'user-correction',       # 用户纠正
    'automation-deployment', # 自动化部署
    'error-fix',             # 错误修复
    'system-monitoring',     # 系统监控
    'quality-verification',  # 质量验证
    'new-capability',        # 新能力获得
    'automation-planning',   # 自动化规划
    'memory-compaction',     # 内存压缩
    'pua-inspection',        # PUA检查
    'quality-improvement',   # 质量改进
]

# 内容质量要求
MIN_CONTENT_LENGTH = {
    'learning-achievement': 15,
    'user-correction': 10,
    'task-done': 8,
    'error-found': 8,
    'system-improvement': 10,
    'default': 5,
}

# Tags智能生成规则
TAG_RULES = {
    'learning-achievement':  ['learning'],
    'user-correction':       ['user-interaction', 'feedback'],
    'task-done':             ['task-completion', 'progress'],
    'error-found':           ['error-detection', 'monitoring'],
    'system-improvement':    ['improvement', 'optimization'],
    'automation-deployment': ['automation', 'deployment'],
    'error-fix':             ['error-resolution', 'fixing'],
    'quality-verification':  ['quality-check', 'verification'],
    'pua-inspection':        ['pua-mode', 'deep-inspection', 'architecture-check'],
}


def validate_event_type(event_type: str) -> bool:
    return event_type in STANDARD_TYPES


def suggest_event_types(keyword: str = '') -> List[str]:
    if not keyword:
        return STANDARD_TYPES
    keyword = keyword.lower()
    suggestions = [t for t in STANDARD_TYPES if keyword in t]
    return suggestions if suggestions else STANDARD_TYPES


def validate_content(content: str, event_type: str) -> bool:
    if not content or not content.strip():
        return False
    content_stripped = content.strip()
    char_count = len(content_stripped)
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in content_stripped)
    if has_chinese:
        conceptual_units = char_count / 15
    else:
        conceptual_units = len(content_stripped.split())
    min_length = MIN_CONTENT_LENGTH.get(event_type, MIN_CONTENT_LENGTH['default'])
    if event_type == 'learning-achievement':
        learning_keywords = [
            'learn', '掌握', '理解', 'understand', 'master', 'discover',
            '发现', 'realize', '认识', 'achieve', '实现', 'improve', '改进',
            'progress', '进展', 'develop', '开发', 'update', '更新',
            'upgrade', '升级', 'enhance', '增强',
        ]
        has_learning_value = any(kw in content_stripped.lower() for kw in learning_keywords)
        if not has_learning_value:
            print(f"⚠️ 警告：学习成就内容可能缺乏学习价值，建议包含学习过程描述")
    is_valid = conceptual_units >= min_length
    if not is_valid:
        print(f"  📊 当前概念单元数：{conceptual_units:.1f}，要求至少：{min_length}")
    return is_valid


def generate_tags(event_type: str, content: str, user_tags: List[str] = None) -> List[str]:
    tags = []
    if event_type in TAG_RULES:
        tags.extend(TAG_RULES[event_type])
    if user_tags:
        tags.extend(user_tags)
    content_lower = content.lower()
    common_keywords = {
        'monitoring':  ['monitor', 'check', 'verify', 'inspect'],
        'automation':  ['auto', 'script', 'cron', 'schedule'],
        'quality':     ['quality', 'fix', 'improve', 'enhance'],
        'error':       ['error', 'bug', 'issue', 'problem'],
        'learning':    ['learn', 'study', 'understand', 'master'],
        'user':        ['user', 'human', 'feedback', 'request'],
        'system':      ['system', 'architecture', 'design', 'structure'],
        'data':        ['data', 'log', 'record', 'event'],
    }
    for tag, keywords in common_keywords.items():
        if any(kw in content_lower for kw in keywords):
            if tag not in tags:
                tags.append(tag)
    unique_tags = []
    for tag in tags:
        if tag not in unique_tags:
            unique_tags.append(tag)
    if not unique_tags:
        unique_tags.append(event_type.replace('-', '_'))
    return unique_tags


def validate_schema(event_data: Dict[str, Any]) -> bool:
    required_fields = ['ts', 'type', 'content']
    for field in required_fields:
        if field not in event_data:
            return False
    if not event_data.get('content') or not isinstance(event_data['content'], str):
        return False
    if 'tags' in event_data and not isinstance(event_data['tags'], list):
        return False
    if 'extra' in event_data and not isinstance(event_data['extra'], dict):
        return False
    return True


def create_standard_event(
    event_type: str,
    content: str,
    tags: Optional[List[str]] = None,
    count: int = 1,
    extra: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    if not validate_event_type(event_type):
        print(f"❌ 错误：事件类型 '{event_type}' 不是标准类型")
        print(f"  标准类型列表：{', '.join(STANDARD_TYPES[:5])}...")
        print(f"  建议更换为：{', '.join(suggest_event_types(event_type.split('-')[0]))}")
        return None
    if not validate_content(content, event_type):
        min_length = MIN_CONTENT_LENGTH.get(event_type, MIN_CONTENT_LENGTH['default'])
        word_count = len(content.strip().split())
        print(f"❌ 错误：内容质量不足")
        print(f"  当前单词数：{word_count}，要求至少：{min_length}")
        if event_type == 'learning-achievement':
            print(f"  💡 学习成就要详细描述：学习内容+方法+收获+应用")
        elif event_type == 'user-correction':
            print(f"  💡 用户纠正要清晰：用户指令+背景+纠正内容+影响")
        return None
    generated_tags = generate_tags(event_type, content, tags)
    event = {
        'ts':      datetime.now(timezone.utc).isoformat(),
        'type':    event_type,
        'content': content.strip(),
        'tags':    generated_tags,
        'count':   count,
    }
    if extra:
        event['extra'] = extra
    if not validate_schema(event):
        print(f"❌ 错误：事件Schema验证失败")
        return None
    content_stripped = content.strip()
    char_count = len(content_stripped)
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in content_stripped)
    if has_chinese:
        conceptual_units = char_count / 15
        unit_name = "概念单元"
    else:
        conceptual_units = len(content_stripped.split())
        unit_name = "单词"
    print(f"✅ 事件创建成功！")
    print(f"  📋 类型：{event_type}")
    print(f"  📝 内容：{content[:50]}..." if len(content) > 50 else f"  📝 内容：{content}")
    print(f"  📊 {unit_name}数：{conceptual_units:.1f} (标准：{MIN_CONTENT_LENGTH.get(event_type, MIN_CONTENT_LENGTH['default'])}+)")
    print(f"  🏷️ Tags：{', '.join(generated_tags[:3])}" + ("..." if len(generated_tags) > 3 else ""))
    print(f"  ⏰ 时间戳：{event['ts'][:19]} UTC")
    return event


def append_event_to_file(event: Dict[str, Any], output_file: str = None) -> bool:
    if output_file:
        filepath = Path(output_file)
    else:
        # 统一使用 .sys/logs/events.jsonl
        workspace_root = Path(__file__).parent.parent
        filepath = workspace_root / '.sys' / 'logs' / 'events.jsonl'

    filepath.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
        print(f"📁 事件已保存到：{filepath}")
        return True
    except Exception as e:
        print(f"❌ 保存失败：{e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='标准化事件创建工具')
    parser.add_argument('--type',       required=True, help='事件类型（必须为标准类型）')
    parser.add_argument('--content',    required=True, help='事件内容（详细描述）', nargs='+')
    parser.add_argument('--tags',       help='Tags列表，逗号分隔')
    parser.add_argument('--count',      type=int, default=1, help='事件计数（通常为1）')
    parser.add_argument('--extra',      help='额外信息，格式：key1:value1,key2:value2')
    parser.add_argument('--file',       help='输出文件路径（默认：.sys/logs/events.jsonl）')
    parser.add_argument('--list-types', action='store_true', help='列出所有标准类型')
    parser.add_argument('--check-type', help='检查类型是否为标准类型')

    args = parser.parse_args()

    if args.list_types:
        print("📋 所有标准事件类型：")
        for i, t in enumerate(STANDARD_TYPES, 1):
            min_len = MIN_CONTENT_LENGTH.get(t, MIN_CONTENT_LENGTH['default'])
            print(f"  {i:2}. {t} (最小内容长度：{min_len}单词)")
        return

    if args.check_type:
        is_valid = validate_event_type(args.check_type)
        print(f"✅ '{args.check_type}' 是标准类型" if is_valid else f"❌ '{args.check_type}' 不是标准类型")
        if not is_valid:
            print(f"  类似建议：{suggest_event_types(args.check_type.split('-')[0])}")
        return

    content = ' '.join(args.content)
    tags = [tag.strip() for tag in args.tags.split(',')] if args.tags else None
    extra = None
    if args.extra:
        extra = {}
        for pair in args.extra.split(','):
            if ':' in pair:
                key, value = pair.split(':', 1)
                extra[key.strip()] = value.strip()

    event = create_standard_event(
        event_type=args.type,
        content=content,
        tags=tags,
        count=args.count,
        extra=extra,
    )

    if event:
        append_event_to_file(event, args.file)
        print("\n🎯 标准化事件创建成功！建议后续使用此工具创建所有事件")
        print("💡 使用示例：")
        print("  python3 create_event.py --type learning-achievement --content \"详细学习描述...\"")
        print("  python3 create_event.py --type task-done --content \"完成任务描述...\" --tags task,automation,monitoring")
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
