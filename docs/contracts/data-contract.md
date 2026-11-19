# 数据契约 v1

## 权威字段与规范化
行为及错误码在五份Spec中定义，本文补充结构，不能另定业务规则。版本均为JSON整数1；day/sequence/资金库存必须是安全整数；不接受NaN、Infinity、字符串数字或未知额外属性。

## 生成居民与设施
生成ID resident-001至resident-030；前10人为farmer，中10人为waterWorker，后10人为resident。所有人住home-01。数字人物固定digital-001。name可重复；关系由ID索引，所有成对关系初始trust/affinity=50。固定设施清单在 [scenario-v1](../fixtures/scenario-v1.json)。设施不可被用户删除；仅广场open/capacity用于边界测试，MVP1不开放其他设施编辑。

## 状态与事件校验
- resources只有food/water/wood/treasury；资金恒等式 `sum(agent.cash)+treasury+externalSpent=1600`。
- 30名生成居民完整存在，数字人物0或1；数字人物含M3白名单profile且授权true。
- proposal字段、cost、effects、version必须匹配场景1；OPEN时ballots为空，关闭后每名在册居民恰好一张票，票数/输入/score10/结果一致。EXECUTED时externalSpent=120，其他状态externalSpent=0。
- events序号从1起连续，nextEventSequence=events.length+1；day非降序且≤state.day；因果标识必须指向合法的命令类别。
- events的actorIds只能引用居民；targetIds允许town、设施ID、议案ID和居民ID。effects字段只允许声明实体的字段；before/after必须符合相应类型。
- 初次创建追加WORLD_CREATED，sequence=1、day=0；下一个事件序号2。快照导出/恢复不产生世界事件。
- bioSummary/displayName作为数据，不解释为HTML。诊断不含原始文本。

## 输入顺序与错误码
人物输入见M3-FR-02；快照输入见M5-FR-03。不得自动纠正快照中的负数、未知版本或悬空引用。

## 快照与演示配置区别
scenario-v1.json是初始化输入，不是可直接导入的世界快照；digital-profile-v1.json是人物导入输入。实际快照由src正式实现产生，见[第30日快照](../test/evidence/day30.json)；配置文件不能作为世界存档导入。
