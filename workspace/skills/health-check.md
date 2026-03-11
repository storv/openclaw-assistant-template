# /health-check

检查助手系统运行状态。

## 执行步骤

1. 运行健康检查脚本：
   exec: WORKSPACE=~/.openclaw/workspace \
     bash ~/.openclaw/workspace/scripts/health-check.sh

2. 脚本会自动检测实际运行时目录（.sys/ 或 .openclaw/），
   无需手动指定路径。

3. 报告检查结果：
   - 运行时目录路径
   - workspace 可写性
   - events.jsonl 可写性及 JSON 合法性
   - 磁盘空间（> 1GB）
   - 关键文件存在性
   - evolve.py 语法

4. 若有 ERR 项，给出修复建议
