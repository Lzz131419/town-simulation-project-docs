# M3 授权数字人物接入

- 文档版本：1.1
- 状态：待评审
- 模块编号：M3
- 主责角色：人物与隐私负责人
- 复核角色：组长/集成负责人
- 上游范围：[mvp1-scope.md](mvp1-scope.md)

## 1. 摘要

本模块允许创建者导入 1 份已获授权的结构化数字人物档案，使数字人物以正式居民身份参与 M1—M5 的规则结算。MVP1 不抓取主页、不生成人物小传、不克隆照片，也不让未授权资料进入模拟。

## 2. 用户故事

### US-1：导入授权数字人物

作为数字人物本人，我想只提交获准字段并成为小镇居民，以便在不泄露额外信息的情况下参与模拟。

### US-2：拒绝无效或未授权档案

作为项目创建者，我想让系统拒绝缺少授权或格式错误的档案，以便避免误用真实人物资料。

### US-3：确认数字人物参与日常规则

作为观察者，我想确认数字人物和规则居民使用同一套工作、消费和投票规则，以便理解其在小镇中的角色。

## 3. 验收标准

### US-1

**AC-01（正常）**

Given 数字人物档案包含全部必填字段并设置 `authorizationConfirmed=true`，When 创建者导入该档案，Then 系统分配唯一 `agentId`、将 `sourceType` 标记为 `digitalPerson`，并在居民名册和详情中显示获准字段。

**AC-02（正常）**

Given 数字人物已成功导入且模拟未暂停，When 创建者推进一个模拟日，Then 该人物参与 M2 的工作、消费、社交或休息结算，并在事件记录中使用同一稳定 `agentId`。

**AC-03（边界）**

Given 场景已有 30 名规则居民且尚未导入数字人物，When 导入 1 份合法档案，Then 导入成功，居民总数变为 31；再次导入第二份档案时系统拒绝。

### US-2

**AC-04（异常）**

Given 档案中缺少 `authorizationConfirmed` 或该值为 `false`，When 创建者尝试导入，Then 世界状态和居民总数不变，返回 `DIGITAL_PROFILE_NOT_AUTHORIZED`，并追加一条 `DIGITAL_PROFILE_IMPORT_FAILED` 失败事件。

**AC-05（异常）**

Given 档案包含白名单外字段，When 创建者尝试导入，Then 系统拒绝整份档案，返回 `DIGITAL_PROFILE_FIELD_NOT_ALLOWED`，不得静默保存额外字段，并追加一条 `DIGITAL_PROFILE_IMPORT_FAILED` 失败事件。

**AC-06（异常）**

Given JSON 缺少必填字段或职业代码无效，When 创建者尝试导入，Then 系统返回 `DIGITAL_PROFILE_INVALID`，当前居民与资源状态保持不变，并追加一条 `DIGITAL_PROFILE_IMPORT_FAILED` 失败事件。

**AC-07（边界）**

Given 已有一名数字人物，When 创建者再次导入，Then 系统返回 `DIGITAL_PROFILE_LIMIT_REACHED`，不改变已有居民，并追加一条 `DIGITAL_PROFILE_IMPORT_FAILED` 失败事件。

### US-3

**AC-08（正常）**

Given 数字人物档案设置了职业 `teacher` 和住宅 `home-01`，When 打开详情，Then 页面显示职业和住宅，并明确标记“已授权数字人物”。

**AC-09（边界）**

Given 数字人物没有提供可选职业，When 导入合法档案，Then 系统使用默认职业 `resident`，并记录默认值来源。

## 4. 功能需求

### FR-01 导入格式

MVP1 只接受 UTF-8 JSON 文件。字段白名单如下：

| 字段 | 必填 | 规则 |
| --- | --- | --- |
| `profileVersion` | 是 | MVP1 固定为 `1` |
| `displayName` | 是 | 1—20 个字符，去除首尾空白 |
| `authorizationConfirmed` | 是 | 必须为布尔值 `true` |
| `jobCode` | 否 | 来自 M2 职业代码表，缺省为 `resident` |
| `homeFacilityId` | 否 | 必须引用当前场景中的住宅设施 |
| `avatarKey` | 否 | 仅允许场景预置头像键，不接受任意 URL |
| `bioSummary` | 否 | 最多 200 字，不得包含外部链接 |

文件不得包含密码、联系方式、证件号、精准住址、健康记录或其他非模拟必需字段。

### FR-02 ID 与授权

- 系统生成 `agentId`，不信任档案提供的外部用户标识。
- 导入结果记录 `authorizationConfirmedAt` 和导入时间，但不记录原始授权文件内容。
- `authorizationConfirmed` 只允许布尔值 `true`；字符串、数字和缺省值一律视为未授权。

### FR-03 校验与导入

1. 解析 JSON。
2. 检查文件大小、字段白名单和必填字段。
3. 检查授权确认。
4. 校验职业和住宅引用。
5. 生成稳定 `agentId`。
6. 以事务方式加入居民状态。
7. 写入一次性导入事件。

任一步失败时，居民、资源和议案状态都不得改变。系统只追加包含错误标识和校验阶段的失败事件，不生成导入成功事件。

### FR-04 参与模拟

- 数字人物不拥有绕过规则的“访客”分支。
- 数字人物的默认需求、余额和关系初始值来自场景配置。
- 其职业、关系和行动结果可被观察，但不得展示未获授权的内部资料。

### FR-05 导出与删除

- 快照只能包含白名单字段和系统生成字段。
- 删除数字人物时只允许将其从模拟中移除，不在 MVP1 中提供云端物理删除承诺。
- 删除操作必须产生审计事件，记录执行时间、对象 ID 和操作者。

## 5. 非功能需求

- **隐私最小化**：只收集完成模拟所需的字段。
- **原子性**：失败导入不得留下半成品居民或成功事件；只保留一条失败审计事件。
- **可审计性**：成功、拒绝和删除均产生稳定事件。
- **可复现性**：导入顺序和动作序列一致时，后续模拟结果一致。
- **无网络依赖**：导入在本地完成，不上传人物档案。
- **可理解性**：界面必须说明导入字段用途和授权边界。

## 6. 边界与异常

| 场景 | 预期行为 | 错误标识或结果 | 对应 AC |
| --- | --- | --- | --- |
| 未提供授权 | 拒绝导入 | `DIGITAL_PROFILE_NOT_AUTHORIZED` | AC-04 |
| 授权值为字符串 `"true"` | 拒绝导入 | `DIGITAL_PROFILE_NOT_AUTHORIZED` | AC-04 |
| 包含白名单外字段 | 整份拒绝 | `DIGITAL_PROFILE_FIELD_NOT_ALLOWED` | AC-05 |
| 必填字段缺失 | 整份拒绝 | `DIGITAL_PROFILE_INVALID` | AC-06 |
| 职业代码未知 | 整份拒绝 | `DIGITAL_PROFILE_INVALID` | AC-06 |
| 住宅 ID 不存在 | 整份拒绝 | `DIGITAL_PROFILE_HOME_NOT_FOUND` | AC-06 |
| 已导入一名数字人物 | 拒绝第二份 | `DIGITAL_PROFILE_LIMIT_REACHED` | AC-07 |
| 文件超过体积上限 | 拒绝读取 | `DIGITAL_PROFILE_TOO_LARGE` | AC-05 |
| 文件不是有效 JSON | 拒绝解析 | `DIGITAL_PROFILE_INVALID` | AC-06 |
| 显示名称去除空白后为空 | 拒绝导入 | `DIGITAL_PROFILE_INVALID` | AC-06 |

## 7. Non-Goals

- 不抓取社交媒体、聊天记录或个人主页。
- 不生成人物照片、声音、人格复刻或行为预测。
- 不在 MVP1 支持多个数字人物。
- 不实现服务端授权中心或身份认证。
- 不保存真实世界的敏感个人字段。
