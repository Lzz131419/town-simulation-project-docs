# 模块Spec：M3 授权数字人物接入

> 版本2.0；2026-11-18；负责人：孙祥；状态：本地重建，待团队评审。

## 摘要
只导入一份本地UTF-8 JSON人物资料，加入统一居民规则。只处理用户提供字段，不抓取主页；演示使用虚构档案。导入必须暂停且无结算，失败world/events/rngState完全不变。

## 用户故事
- **M3-US-1：让人物参与模拟**。作为创建者，我想导入一位授权人物，以便观察其共同生活。
- **M3-US-2：限制和保护输入**。作为人物提供者，我想拒绝无授权或越界资料，以便只让必要信息进入模拟。

## 验收标准（Given/When/Then）

### M3-AC-01：合法导入与默认值（M3-US-1）
```gherkin
Given 世界有30名生成居民，暂停，档案profileVersion=1、displayName="林溪"、authorizationConfirmed=true，未填jobCode
When 调用importProfile并推进一天
Then 导入一次成功、agentId=digital-001、sourceType=digitalPerson、jobCode=resident、homeFacilityId=home-01、cash=0、energy=70、hunger=30、waterNeed=30；人口31、资金总额不变，追加DIGITAL_PROFILE_IMPORTED。推进后该ID有日行动记录并可参加表决。
```

### M3-AC-02：授权、大小与格式校验（M3-US-2）
```gherkin
Given 档案有false/缺失/字符串true的授权，或无效JSON、未知字段、非法职业、超过16384字节
When 分别调用importProfile
Then 按FR-02顺序返回对应错误码；未授权为DIGITAL_PROFILE_NOT_AUTHORIZED，未知字段为DIGITAL_PROFILE_FIELD_NOT_ALLOWED，超大小为DIGITAL_PROFILE_TOO_LARGE，其余类型/格式为DIGITAL_PROFILE_INVALID；world/events/rngState和人口不变，不保留导入原文。
```

### M3-AC-03：一人上限与导入时点（M3-US-1）
```gherkin
Given 已有digital-001，或议案已关闭（APPROVED/REJECTED/EXECUTED），另设一个显示名相同但尚未导入人物的场景
When 导入合法档案
Then 已有数字人物返回DIGITAL_PROFILE_LIMIT_REACHED；无数字人物但表决已关闭返回DIGITAL_PROFILE_VOTING_CLOSED，防止投票名单漂移；尚未导入且议案OPEN时同名可成功，由固定ID区别，不能把显示名当唯一键。
```

### M3-AC-04：文本显示和数据最小化（M3-US-2）
```gherkin
Given 合法档案displayName="<b>林溪</b>"，bioSummary含普通文本；另测名称20/21个Unicode码点、空白名称和不存在home
When 导入并展示、导出快照
Then 标签按原样文本显示而不生成HTML元素，不发出网络请求；20个码点接受、21或空白拒绝DIGITAL_PROFILE_INVALID，不存在home返回DIGITAL_PROFILE_HOME_NOT_FOUND。快照只保留白名单/系统字段；diagnostics不含原始档案、联系方式或背景全文。
```

## 功能需求
- **M3-FR-01（US-1）**：白名单：profileVersion（必填整数1）、displayName（trim后1–20个Unicode码点）、authorizationConfirmed（必填boolean true）、jobCode（可选farmer/waterWorker/resident，缺省resident）、homeFacilityId（可选，仅home-01）、bioSummary（可选字符串≤200码点）。禁止外部ID、URL头像和其他字段；不持久化现实时间戳。
- **M3-FR-02（US-2）**：校验顺序固定：文件字节数≤16384 → UTF-8/JSON对象 → 白名单 → 授权值 → 字段类型/版本/长度/职业 → 住宅引用 → 当前人数上限 → 议案仍OPEN。相同多重错误只返回最先命中的错误码。版本不是1也属于DIGITAL_PROFILE_INVALID。
- **M3-FR-03（US-1）**：导入只在M1事务副本里分配digital-001；与每名现存居民建立双向trust=50/affinity=50关系。居民总数变31，现金0，固定住宅总容量31，不增发金钱。模型不参与。
- **M3-FR-04（US-2）**：页面显示“已授权数字人物”和字段用途，授权勾选不等于法律身份认证；生产演示不放真实资料。所有字符串用textContent渲染。
- **M3-FR-05（US-2）**：MVP1撤回方式是显式重置小镇，清除当前内存人物与事件，并提醒已下载JSON由用户自行删除；不提供单人删除/跨设备擦除承诺。

## 非功能需求
不上传资料、不调用模型、不用localStorage保存原始档案。全部校验完成前不得改变世界。导入16KiB目标≤500ms，正式实现时实测。

## 边界与异常
| 场景 | 预期行为 | 对应AC |
| --- | --- | --- |
| 授权缺失/false/字符串 | DIGITAL_PROFILE_NOT_AUTHORIZED | M3-AC-02 |
| 超过16KiB/非JSON/未知字段 | TOO_LARGE / INVALID / FIELD_NOT_ALLOWED（完整码见AC-02） | M3-AC-02 |
| 第二人/议案关闭 | DIGITAL_PROFILE_LIMIT_REACHED / DIGITAL_PROFILE_VOTING_CLOSED | M3-AC-03 |
| 同名 | 允许，依靠agentId区分 | M3-AC-03 |
| 20/21码点、HTML文本、住宅不存在 | 长度校验、纯文本；DIGITAL_PROFILE_HOME_NOT_FOUND | M3-AC-04 |

## Non-Goals
不从网页/聊天记录抓取资料，不进行身份认证或人格克隆，不支持多个数字人物、头像URL、单人删除或云存储。

## 变更记录
| 日期 | 变更 | 原因 |
| --- | --- | --- |
| 2026-11-18 | 统一为2.0；正常/边界/异常均给可观察结果 | 对齐课程模板，修正旧版歧义 |
