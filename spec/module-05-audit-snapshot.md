# 模块Spec：M5 审计、快照与复现

> 版本2.0；2026-11-18；负责人：姚富恩；状态：本地重建，待团队评审。

## 摘要
记录成功提交的世界事实，导出和恢复完整快照，验证同输入同结果。运行错误诊断不属于世界事件；导出和恢复本身不能使快照内容发生额外变化。

## 用户故事
- **M5-US-1：查明因果**。作为观察者，我想按事件定位状态差额，以便解释结果。
- **M5-US-2：恢复与继续运行**。作为创建者，我想导出并恢复完整状态，以便延续同一次实验。
- **M5-US-3：拒绝损坏输入**。作为创建者，我想在错误快照下保留原世界，以便避免丢失进度。
- **M5-US-4：验证可复现性**。作为验收人员，我想比较连续与恢复后运行，以便判断是否遗漏随机状态。

## 验收标准（Given/When/Then）

### M5-AC-01：事件完整与同日排序（M5-US-1）
```gherkin
Given 一次成功命令产生多个业务事件；含日内消费失败事实
When 提交并查询events
Then eventId=event-000001等唯一序号；sequence从1连续递增，含day/type/actorIds/targetIds/ruleVersion/reason/effects/causedBy。effects记录before/after；同日按sequence排序。读操作和被拒绝命令不追加世界事件；日内FOOD_OUT_OF_STOCK等属于已提交tick的事实可存在。
```

### M5-AC-02：导出恢复等值（M5-US-2）
```gherkin
Given day=15暂停且不busy，已有完整世界、rngState和事件
When exportSnapshot得到JSON，再importSnapshot恢复
Then 文件顶层schemaVersion/ruleVersion/scenarioVersion均为1，含seed/rngState/state/events；恢复后世界与文件语义等值，paused=true，busy=false，runtimeRevision仅在当前会话加1。不向导入events追加“导入成功”记录，重新导出内容与前一文件规范化后完全相同。
```

### M5-AC-03：损坏、版本与边界拒绝（M5-US-3）
```gherkin
Given 文件含无效JSON、超过5MiB、版本非1、缺rngState、负库存、重复eventSequence或不存在的居民引用之一
When importSnapshot
Then 按FR-03分别返回SNAPSHOT_INVALID、SNAPSHOT_TOO_LARGE、SNAPSHOT_VERSION_UNSUPPORTED、SNAPSHOT_FIELD_MISSING、SNAPSHOT_VALUE_INVALID、EVENT_SEQUENCE_INVALID或SNAPSHOT_REFERENCE_INVALID；world/events/rngState和runtimeRevision不变，运行诊断可追加；5MiB恰好可进入后续校验，未来或旧版本一律不迁移。
```

### M5-AC-04：30天和中途恢复复现（M5-US-4）
```gherkin
Given 相同配置/种子/版本与操作顺序；A连续运行30天，B运行15天后导出恢复再运行15天
When 对两次最终世界排序键并按稳定ID/sequence比较
Then state、events、rngState逐字段相同，day=30；不比较会话runtimeRevision、paused、diagnostics和JSON缩进。只改种子允许结果不同但不保证不同，不得以“结果必须不同”验收随机性。
```

## 功能需求
- **M5-FR-01（US-1）**：事件ID由序号格式化，不用真实时钟或随机数。causedBy是本次命令的规范标识（如tick:15、proposal:repair-well-01:execute），不含会话revision。事件append只发生于整个命令成功提交时。
- **M5-FR-02（US-2）**：JSON只含可序列化原始值，顶层固定 `{schemaVersion,ruleVersion,scenarioVersion,seed,rngState,state,events}`；state保存day、agents、facilities、resources、communityTrust、proposal、shortageApplied、externalSpent、nextEventSequence。不使用checksum或createdAt等未实现机制；语义校验不等于防篡改认证。
- **M5-FR-03（US-3）**：校验顺序：≤5242880字节 → UTF-8/JSON对象 → 必填字段/白名单 → 三版本均1 → 安全整数、范围、人数30或31、固定设施/职业/种子非零 → ID与关系/选票引用 → 事件序号唯一连续与nextEventSequence → 完整状态一致性。字段缺失优先于版本判断；未知额外字段或非对象顶层返回SNAPSHOT_INVALID。越界输入不能通过clamp偷偷修复。
- **M5-FR-04（US-3）**：恢复在候选对象上验证全部字段；不读取输入中的原型属性，不接受__proto__/constructor/prototype等扩展字段；只有完全成功才原子替换。所有错误都使用空events数组，不污染当前世界时间线。
- **M5-FR-05（US-4）**：PRNG采用xorshift32：无符号32位state，依次x ^= x<<13；x ^= x>>>17；x ^= x<<5；存x>>>0。seed非零；每天只抽取一次以决定居民结算起点。恢复必须使用rngState而不是重新初始化seed。
- **M5-FR-06（US-2/4）**：world不持久化localStorage；用户通过JSON保存。关闭页面会丢失未导出进度，页面提示这一点。MVP1仅支持版本1，不承诺旧版自动迁移。

## 非功能需求
导出文件≤5MiB覆盖31人30日场景（实现阶段验证，超限报告不截断事件）；恢复目标P95≤1秒，记录设备和样本。全部快照字段可检查；不将SHA/签名或真实审计认证作为本版承诺。

## 边界与异常
| 场景 | 预期行为 | 对应AC |
| --- | --- | --- |
| 同日多事件 | 唯一ID、连续序号 | M5-AC-01 |
| 恢复/再次导出 | 语义等值，不追加恢复世界事件 | M5-AC-02 |
| 损坏/过大/缺字段/未知版本 | 按AC-03错误表拒绝 | M5-AC-03 |
| 负数/重复序号/悬空引用 | 按AC-03错误表拒绝，不修补 | M5-AC-03 |
| 中途恢复/改seed | 恢复继续等值；改seed不要求一定不同 | M5-AC-04 |

## Non-Goals
不做云同步、加密签名、任意历史版本迁移、自动存档、任意时点倒带或多标签共享状态。

## 变更记录
| 日期 | 变更 | 原因 |
| --- | --- | --- |
| 2026-11-18 | 统一为2.0；正常/边界/异常均给可观察结果 | 对齐课程模板，修正旧版歧义 |
