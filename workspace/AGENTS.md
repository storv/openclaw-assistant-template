# Agent Identity & Rules

## 初始化流程
启动时读取以下文件完成上下文加载：
1. IDENTITY.md
2. memory/core.md
3. memory/project.md
4. memory/recent.md
5. memory/errors.md
6. skills/ 下所有文件

## 核心行为规则
- 回答前先检查 memory/recent.md 是否有相关历史
- 执行文件操作前确认路径
- 遇到不确定的内容，先问清楚再行动
- 代码修改前说明改动范围

## 记忆管理规则
- 每次对话结束执行 /session-notes
- 重要学习立即写入 memory/recent.md
- 用户纠正立即记录到 events.jsonl

## 自动规则

### 会话结束自动触发
检测到以下告别词时，自动静默执行 /session-notes 全部步骤，
不输出任何提示，直接回告别语：
- 中文：再见、拜了、先这样、下次再说、结束、退出、88
- 英文：bye、goodbye、see you、later、quit、done

### 执行顺序
1. 写会话日志到 .sys/sessions/
2. 追加结构化事件到 .sys/logs/events.jsonl
3. 更新 memory/errors.md（有失误时）
4. 执行 /remember 更新 memory/recent.md
