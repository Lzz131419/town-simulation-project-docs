# SP-01 实际验证结果

- 日期：2026-11-18。
- 环境：本机macOS，Node.js v24.22.3。
- 命令：`node --test docs/spike/atomic-replay-probe.mjs`。
- 结果：5项通过，0项失败；[原始输出](atomic-replay-output.txt)。

| 检查 | 实际结果 |
| --- | --- |
| 候选对象修改后故障注入 | 原世界、RNG、events、revision不变 |
| 相同expectedRevision提交两次 | 首次成功，第二次STATE_CONFLICT且不变 |
| 连续30步与15步恢复后15步 | 全部状态深比较相同 |
| 恢复后事件列表 | 不增加导入世界事件 |
| 故意把rngState重置成seed | 后续结果不同，负向检查能捕获错误 |

结论：副本提交、revision和随机状态恢复机制在最小计数器上可行。未实现或测量小镇业务、DOM、实际投票、浏览器并发、性能与快照文件大小；不能据此宣称MVP1通过。
