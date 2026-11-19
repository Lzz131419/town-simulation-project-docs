# 模块Spec：M1 世界控制与观察

> 版本2.1；2026-11-18；负责人：张果、王崛；状态：本地重建，待团队评审。

## 摘要
创建并控制唯一小镇，编排每日规则，展示居民与事件。M1 不自行计算工资、立场和快照校验。命令失败时完整世界（含事件和随机数状态）不变；诊断写入独立会话列表。

## 用户故事
- **M1-US-1：从固定起点开始**。作为创建者，我想载入固定场景，以便重复课堂实验。
- **M1-US-2：控制并解释进程**。作为观察者，我想暂停、推进并查看结果，以便核对状态变化。
- **M1-US-3：观察受控冲击**。作为创建者，我想触发一次轻度粮食短缺，以便看到库存压力来源。

## 验收标准（Given/When/Then）

### M1-AC-01：初始化与配置边界（M1-US-1）
```gherkin
Given 尚无世界，或已有可替换世界；配置为 scenarioVersion=1、ruleVersion=1、schemaVersion=1，30名生成居民、种子非零uint32
When 调用 createWorld(config)
Then 合法配置返回 ok=true，day=0、30名唯一ID居民、paused=true；重复创建是显式重置，不叠加人口。种子0、居民数不为30或字段缺失返回 SCENARIO_CONFIG_INVALID；版本不为1返回 SCENARIO_VERSION_UNSUPPORTED；失败不覆盖旧世界。
```

### M1-AC-02：暂停、单步与原子结算（M1-US-2）
```gherkin
Given 世界day=d，paused=true，runtimeRevision=r，无进行中的命令
When 手动 step(expectedRevision=r)，随后试验暂停/恢复、旧版本与注入结算异常
Then 手动单步成功后day=d+1且仍暂停；暂停只停止自动调度。resume每1000ms最多发起一次相同结算，pause后不补算。忙时返回 STEP_IN_PROGRESS，旧revision返回 STATE_CONFLICT，结算异常返回 STEP_FAILED；三者均不改变world、rngState和events；未初始化返回WORLD_NOT_INITIALIZED，运行中手工写操作返回SIMULATION_RUNNING，也不改变世界；成功提交仅增加一次runtimeRevision。
```

### M1-AC-03：总览、详情与错误反馈（M1-US-2）
```gherkin
Given 已发生一次工作/消费或失败操作，存在稳定agentId和eventSequence
When 查看总览、该居民详情、筛选时间线，并查询不存在的居民
Then 总览显示day/人口/粮食/清水/公库/信任/议案；详情显示职业、精力、需求、余额、关系和最近10条相关事件（不足10条全列）；时间线按sequence倒序，筛选不删数据；未知居民返回 AGENT_NOT_FOUND，页面给出错误码。读操作不修改world与事件；无历史显示“暂无行为记录”。
```

### M1-AC-04：短缺边界与重复保护（M1-US-3）
```gherkin
Given 尚未触发短缺，粮食库存F为非负整数
When 调用 triggerShortage，并尝试再次触发
Then 第一次库存变为 floor(F*0.8)，记录 FOOD_SHORTAGE 的before/after及损失量，shortageApplied=true；F=0时仍记录损失0且不为负；第二次返回 SHORTAGE_ALREADY_APPLIED，库存、rngState和events不变。
```

## 功能需求
- **M1-FR-01（US-1）**：场景固定五类设施、30个初始居民；默认种子20261118。day表示已结算日数，从0开始。
- **M1-FR-02（US-2）**：运行控制 `{paused,busy,runtimeRevision}` 不属于世界快照。成功创建/推进/冲击/人物导入/表决/执行/恢复均使 runtimeRevision 加1；读操作、pause/resume不增加。命令启动先查busy，再查expectedRevision，再执行业务校验。
- **M1-FR-03（US-2）**：一次推进在临时副本上按“day+1 → 需求增长 → 工作/休息 → 购买食物与取水 → 广场社交 → 日摘要 → 不变量验证 → 原子提交”执行。任何意外失败丢弃整个副本；已定义的居民行动失败只是本日事实，不使整个日结算失败。
- **M1-FR-04（US-2）**：成功返回 `{ok:true,data,events}`；拒绝返回 `{ok:false,error:{code,message},events:[]}`。独立diagnostics只存错误码、操作类型，不存导入原文。无世界时除createWorld/importSnapshot外均返回 WORLD_NOT_INITIALIZED。
- **M1-FR-05（US-2）**：暂停可手动单步、导入人物、触发短缺和投票；自动运行中允许读取和pause，其他手工写操作返回 SIMULATION_RUNNING。导出/恢复快照要求暂停且不busy。
- **M1-FR-06（US-3）**：短缺是立即发生的一次性库存损失，不引入多日灾害日历。控制按钮在busy时禁用，业务层仍需防重入。

- **M1-FR-07（US-2，呈现补充）**：中文原创像素地图为桌面观察入口，初次进入自动创建暂停世界；保留总览、详情、事件和公共事务。地图位置仅为视图布局，不新增空间规则；同日快照恢复也必须刷新人物与活动。详见[界面设计](../docs/frontend-design.md)。

## 非功能需求
31人30天无未捕获异常；目标桌面Chrome/Edge最新版，规则单步P95≤100ms、UI更新≤500ms（10次预热后100次样本，记录设备；实测见docs/test/implementation-results.md）。主要操作可键盘访问；所有文本安全输出；无外部请求。

## 边界与异常
| 场景 | 预期行为 | 对应AC |
| --- | --- | --- |
| 缺配置/种子0/人口错误 | SCENARIO_CONFIG_INVALID；旧世界不变 | M1-AC-01 |
| 未知版本 | SCENARIO_VERSION_UNSUPPORTED | M1-AC-01 |
| 暂停手动单步 | 允许，不自动恢复 | M1-AC-02 |
| 忙/过期revision/异常 | STEP_IN_PROGRESS / STATE_CONFLICT / STEP_FAILED；无部分提交 | M1-AC-02 |
| 运行中手工写/无世界 | SIMULATION_RUNNING / WORLD_NOT_INITIALIZED；无副作用（AC-02的前置条件校验） | M1-AC-02 |
| 居民不存在 | AGENT_NOT_FOUND | M1-AC-03 |
| 零库存/重复短缺 | 首次损失0；重复SHORTAGE_ALREADY_APPLIED | M1-AC-04 |

## Non-Goals
不做地图编辑、小时级模拟、多世界、多线程或跨标签同步。观察UI不实现独立业务规则。

## 变更记录
| 日期 | 变更 | 原因 |
| --- | --- | --- |
| 2026-11-18 | 2.1：中文原创桌面像素观察界面；仅澄清呈现，不改变AC或模拟规则 | 用户明确要求参考Smallville但不照搬 |
| 2026-11-18 | 统一为2.0；正常/边界/异常均给可观察结果 | 对齐课程模板，修正旧版歧义 |
