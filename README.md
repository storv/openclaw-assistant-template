# OpenClaw 内网数字助手配置模板 v2.1

让 OpenClaw AI 助手「越用越好用」的自主进化配置框架。

## 解决的问题

| 问题 | 解法 |
|------|------|
| 对话越来越慢，token 消耗迅猛 | 三层记忆按需加载 |
| 压缩后助手「变傻」 | 对话结束主动固化记忆 |
| 死板，不会举一反三 | 事件驱动错误聚类，自动触发规则建议 |
| 越用越老旧 | 双频率进化回路 + git 版本追踪 |

## 快速开始

```bash
git clone git@github.com:zhihua-yang/openclaw-assistant-template.git
cd openclaw-assistant-template
bash setup.sh
自定义部署路径（可选）
bash
OPENCLAW_WORKSPACE=/your/custom/path bash setup.sh
目录结构
text
workspace/
├── IDENTITY.md          # 助手身份（初始化后必填）
├── AGENTS.md            # 行为规则与进化门控
├── memory/
│   ├── core.md          # 长期环境信息（必填）
│   ├── project.md       # 项目上下文
│   └── recent.md        # 近期学习记录（自动维护）
├── skills/              # 可调用技能（8个）
└── scripts/             # 进化脚本（与配置统一 git 追踪）
    ├── evolve.py
    ├── baseline.sh
    └── health-check.sh
重要说明
IDENTITY.md：只能手动编辑，进化机制不可触及

memory/recent.md：系统自动维护，setup.sh 不会覆盖已有内容

scripts/：有 bug 修复时 setup.sh 会备份旧版本后更新
