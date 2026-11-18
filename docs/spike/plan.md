# 技术探针计划

## 探针SP-01：原子提交和随机状态恢复
- 目标：验证ADR-002所选机制是否能丢弃半成品、拒绝过期请求、恢复PRNG续跑。
- 输入：独立的最小计数器与xorshift32状态，不实现居民/投票等业务。
- 步骤：副本修改后故障注入；相同revision重复提交；连续30步对比15步保存+15步；恢复再导出语义比较。
- 成功标准：原对象及日志不变；只有一次提交；续跑完全相同；失败不增加revision。
- 命令：`node --test docs/spike/atomic-replay-probe.mjs`（Node 22+）。
- 产出：[atomic-replay-result.md](atomic-replay-result.md)、[原始输出](atomic-replay-output.txt)。
- 约束：仅机制证据，不合并src/，不证明正式实现或投票正确。

## 探针SP-02：浏览器模块和契约Mock
- 目标：验证ES modules加载、文本安全、主界面成功/错误分支，以及31人30日事件量是否达到性能目标。
- 输入：固定模拟响应，尤其INSUFFICIENT_TREASURY、DIGITAL_PROFILE_INVALID、SNAPSHOT_INVALID。
- 步骤：由本地HTTP加载隔离Mock，验证标签文本不执行、错误不清空现有界面；记录设备、预热10次、100样本。
- 成功标准：无外部网络请求；错误码原样显示；规则P95≤100ms、UI≤500ms、快照恢复≤1秒、文件≤5MiB。
- 产出位置：未来docs/spike/browser-contract-result.md。
- 当前状态：计划，未执行；不伪造页面截图或性能数值。正式UI由T03开发、T12验收。

## 探针SP-03：旧HTML交互参考
保留town-simulation-spike.html和原说明，不改其业务逻辑。本次只审阅已知限制，不把旧投票/人物导入/快照当成新Spec验收。
