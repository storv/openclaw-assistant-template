#!/usr/bin/env python3
"""
修复近期事件Tags缺失问题
专门解决PUA第2轮检查发现的问题：修复后新增事件Tags覆盖率严重倒退

问题发现：在修复过程中创建的新事件（从第24个事件开始）大部分无Tags
解决方案：使用标准化工具重新处理这些事件，智能生成Tags

此工具采用保守修复策略：
1. 不删除原事件，创建副本修复
2. 备份原数据
3. 使用create_event.py相同的Tags生成逻辑
4. 仅修复Tags缺失的事件，保留已有Tags的事件
"""

import json
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(__file__))
try:
    from create_event import generate_tags
except ImportError:
    def generate_tags(event_type: str, content: str, user_tags: List[str] = None) -> List[str]:
        tags = []
        type_tags = {
            'learning-achievement': ['learning'],
            'user-correction':      ['user-interaction', 'feedback'],
            'task-done':            ['task-completion', 'progress'],
            'error-found':          ['error-detection', 'monitoring'],
            'system-improvement':   ['improvement', 'optimization'],
            'system-monitoring':    ['monitoring', 'check'],
            'quality-verification': ['quality-check', 'verification'],
        }
        if event_type in type_tags:
            tags.extend(type_tags[event_type])
        if user_tags:
            if isinstance(user_tags, list):
                tags.extend(user_tags)
        content_lower = content.lower()
        if 'learning' in content_lower or 'learn' in content_lower:
            tags.append('learning')
        if 'user' in content_lower or 'human' in content_lower:
            tags.append('user')
        if 'quality' in content_lower or 'fix' in content_lower:
            tags.append('quality')
        if 'tool' in content_lower or 'script' in content_lower:
            tags.append('tool')
        if 'event' in content_lower or 'log' in content_lower:
            tags.append('data')
        if 'pua' in content_lower or 'inspect' in content_lower:
            tags.append('inspection')
        unique_tags = []
        for tag in tags:
            if tag not in unique_tags:
                unique_tags.append(tag)
        if not unique_tags:
            unique_tags.append(event_type.replace('-', '_'))
        return unique_tags


def load_events(filepath: Path) -> List[Dict[str, Any]]:
    events = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
        print(f"📊 已加载 {len(events)} 个事件")
    except FileNotFoundError:
        print(f"❌ 文件不存在: {filepath}")
    return events


def identify_events_to_fix(events: List[Dict[str, Any]]) -> List[int]:
    to_fix = []
    for i, event in enumerate(events):
        if i >= 23:
            has_tags = ('tags' in event and event['tags'] and len(event['tags']) > 0)
            if not has_tags:
                to_fix.append(i)
                print(f"  事件{i+1}: ❌ 无Tags ({event.get('type', 'unknown')}): {event.get('content', '')[:30]}...")
    return to_fix


def fix_event_tags(event: Dict[str, Any]) -> Dict[str, Any]:
    fixed_event = event.copy()
    event_type = event.get('type', 'unknown')
    content = event.get('content', '')
    existing_tags = event.get('tags', [])
    if isinstance(existing_tags, list) and len(existing_tags) == 0:
        existing_tags = []
    new_tags = generate_tags(event_type, content, existing_tags)
    fixed_event['tags'] = new_tags
    if 'extra' not in fixed_event:
        fixed_event['extra'] = {}
    fixed_event['extra']['tags_fixed_at'] = datetime.now().isoformat()
    return fixed_event


def backup_original_file(filepath: Path) -> bool:
    if not filepath.exists():
        return False
    backup_path = filepath.parent / f"{filepath.name}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy2(filepath, backup_path)
        print(f"📁 已备份原文件到: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        return False


def main():
    print("🔧 修复近期事件Tags缺失工具")
    print("="*60)
    print("目标：修复PUA检查发现的Tags覆盖率严重倒退问题")
    print("  修复后新增事件（第24个开始）大部分无Tags")
    print("="*60)

    # 统一使用 .sys/logs/events.jsonl
    workspace_root = Path(__file__).parent.parent
    events_file = workspace_root / '.sys' / 'logs' / 'events.jsonl'

    if not events_file.exists():
        print(f"❌ 文件不存在: {events_file}")
        return 1

    backup_original_file(events_file)

    events = load_events(events_file)
    if len(events) == 0:
        print("❌ 没有事件可处理")
        return 1

    print(f"🔍 识别需要修复Tags的事件（从第24个事件开始）...")
    events_to_fix = identify_events_to_fix(events)

    if not events_to_fix:
        print("✅ 所有事件都有Tags，无需修复")
        return 0

    print(f"📊 需要修复的事件: {len(events_to_fix)}个")
    total_events = len(events)
    events_from_24 = total_events - 23
    print(f"  📈 事件总数: {total_events}")
    print(f"  📊 修复后新增事件(24+): {events_from_24}个")
    print(f"  ❌ 无Tags事件: {len(events_to_fix)}个 ({len(events_to_fix)/events_from_24*100:.1f}%)")

    fixed_count = 0
    for idx in events_to_fix:
        if idx < len(events):
            original_event = events[idx]
            print(f"🔄 修复事件{idx+1}: {original_event.get('type', 'unknown')}")
            fixed_event = fix_event_tags(original_event)
            events[idx] = fixed_event
            original_tag_count = len(original_event.get('tags', [])) if original_event.get('tags') else 0
            new_tag_count = len(fixed_event['tags'])
            print(f"  📊 Tags: {original_tag_count} → {new_tag_count}: {fixed_event['tags'][:3]}")
            fixed_count += 1

    try:
        with open(events_file, 'w', encoding='utf-8') as f:
            for event in events:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')

        print(f"\n✅ 修复完成！")
        print(f"  📊 修复文件: {events_file}")
        print(f"  🔄 修复数量: {fixed_count}/{len(events_to_fix)}个事件")

        print(f"\n🔍 验证修复效果:")
        verified_events = load_events(events_file)
        if verified_events:
            recent_events = verified_events[23:] if len(verified_events) > 23 else []
            if recent_events:
                has_tags = sum(1 for e in recent_events if 'tags' in e and e['tags'] and len(e['tags']) > 0)
                coverage = has_tags / len(recent_events) * 100 if recent_events else 0
                print(f"  📊 修复后新增事件Tags覆盖率: {coverage:.1f}%")
                print(f"  📈 修复前覆盖率: 11.8% (仅2/17有Tags)")
                print(f"  📈 修复后覆盖率: {coverage:.1f}% ({has_tags}/{len(recent_events)}有Tags)")
                if coverage >= 95:
                    print(f"  ✅ Tags修复成功！")
                else:
                    print(f"  ⚠️ Tags覆盖率仍需改进")
        return 0
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
