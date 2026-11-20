# 雾河镇：多人数字分身生活空间

六名小组成员登录同一个小镇，控制自己的居民，生产、交易、留言和共同建设。每个人可以连接自己的大模型，让 AI 把意图整理成行动计划；离线后只执行已有计划和规则，不继续发起模型请求。

当前是 **v2 本地可运行版本**，技术栈为 Vue 3 + TypeScript + Phaser 3、FastAPI + SQLAlchemy、SQLite、LangGraph。电脑端操作区采用白底黑线与少量贴纸色，地图为原创高清彩色场景。本仓库同时保留第06–09周课程材料、v1历史实现与当前v2代码。完整提交范围和阅读顺序见[本次交付目录](docs/submission-2026-11-20.md)。

## 本地启动

需要 Node.js 22+、Python 3.12。首次运行：

```sh
npm run setup
npm start
```

打开 <http://127.0.0.1:5173>；接口文档在 <http://127.0.0.1:8000/docs>。`npm start` 检查端口占用，不会终止其他项目。停止后重新启动，世界从数据库继续，停服期间不补算时间。

| 姓名 | 用户名 | 密码 |
| --- | --- | --- |
| 张果 | zhangguo | zhangguo |
| 王崛 | wangjue | wangjue |
| 李展博 | lizhanbo | lizhanbo |
| 孙祥 | sunxiang | sunxiang |
| 钱俊昊 | qianjunhao | qianjunhao |
| 姚富恩 | yaofuen | yaofuen |

## 可以做什么

- **小镇生活**：六名玩家与六名系统居民共享地图；查看状态、手动行动、缩放和平移、跟随角色、导览与小地图定位，行动到达后结算。生活手册追踪六项目标、徽章和成长等级。
- **邻里档案**：查看居民资产、活动、关系，定位角色；可前往指定邻居身边交流，到达后更新双方关系。
- **生产与交付**：5个分区、21个地点与15种商品；采收、织布、制作家具、熬汤，在南岸交付站完成每日物资委托，实际消耗物资并领取报酬。详见[街区扩展](docs/v2/district-expansion.md)。
- **集市交易**：购买、出售与补给；交易计入共同里程碑。
- **合作订单**：发布采购并托管镇币，其他玩家交付，取消或到期退款；同一订单只支付一次。
- **共同建设**：捐木材与镇币建设仓库，完成后全体背包容量由 30 增至 60。
- **邻里留言**：给其他成员发送持久化私信。
- **我的 AI 分身**：保存目标、模型连接、最多八步计划、保留余额和每日预算；选择规则托管、仅执行本轮或本人接管。
- **进度与归档**：世界进度自动保存在服务器；创建、查看、导出和删除个人归档，恢复个人计划与规则。
- **生活记录**：筛选与分页查看事件、个人成果、关系及小组共建情况；回归时展示离线行动摘要。

个人归档不会回滚共享世界的资产，避免覆盖其他玩家进度。未配置模型也能手动操作、编辑计划和运行规则托管。

## 模型连接

在“我的 AI 分身”填写支持 OpenAI Chat Completions 格式的 HTTPS API 基础地址（如服务商提供的 `/v1` 地址）、API Key 和模型名称。系统会在基础地址后追加 `/chat/completions`。测试连接也调用一次模型。每次规划由玩家主动发起，不存在无限循环的后台模型调用。

LangGraph 流程为上下文 → 模型 → 行动校验 → 保存计划；保存计划后由玩家启用执行。模型只规划已有动作，不能创建不存在的交易、替别人操作或改变规则。普通断线/退出会取消本地未完成请求，异常断网通过心跳租约识别；已发送给服务商的请求是否计费由服务商决定。

**真实外部模型尚未联调**：目前验证了模拟模型响应、真实 LangGraph 流程和 HTTP 请求适配器。服务端持久化目前运行在本机，未部署到外部云端；PostgreSQL/Docker 配方已提供，尚未运行验收。

## 工程结构

```text
frontend/src/
  views/          九个业务页面与登录页
  components/     布局、地图包装、居民检查器与弹窗
  composables/    AI、留言、归档、记录、成长展示各自的状态与请求
  stores/         会话、世界连接与页面编排
  game/           场景编排、人物动画、环境动态与 art/ 原创美术
  styles/         基础、布局、纸面线稿主题与游戏 HUD
backend/app/
  api/            HTTP / WebSocket 接口与认证依赖
  services/       应用命令与运行时装配
  domain/         行动、订单、托管调度、成长计数与业务不变量
  ai/             LangGraph 规划与模型 HTTP 适配
  infrastructure/ 阻塞任务协调、错误响应、结构迁移
  bootstrap.py    启动迁移与数据初始化
  runtime.py      世界事务、时钟与在线连接
  models.py       数据模型
  database.py     连接与会话
backend/migrations/ Alembic 版本化结构升级
backend/tests/    新版业务与接口测试
frontend/tests/   多浏览器上下文联调
scripts/          环境安装与本地启动
```

不以代码行数作为完成指标。模块依赖和扩展原则见[架构说明](docs/v2/architecture.md)。单个后端进程持有世界时钟，当前必须使用一个 worker。

## 验证与设计资料

```sh
npm test                 # v2 后端测试
npm run test:coverage     # 后端覆盖率报告，90%门禁
npm run build            # Vue 类型检查和构建
npm run lint             # Ruff 与前端格式检查
npm run test:browser      # 需先启动服务，并安装 Google Chrome；可用 TOWN_E2E_BASE_URL 指定独立测试服务
npm run test:legacy       # v1 的 44 项规则回归
npm run docs:check        # 文档结构与本地链接
```

[产品设计](docs/v2/product-design.md) · [新版 Spec](docs/v2/spec.md) · [系统架构](docs/v2/architecture.md) · [实现计划](docs/v2/implementation-plan.md) · [验证记录](docs/v2/verification.md) · [ADR-003](adr/ADR-003-shared-town-v2.md)

## 课程文档与 v1 历史

第 06–09 周文档、五模块 Spec、十二项任务和 v1 原生 JavaScript 实现保留，方便对照课程交付；它们不是 v2 技术与功能约束。v2 基于用户明确提出的多人账号、Vue、游戏引擎、FastAPI、数据库及模型服务重新设计。

| 历史材料 | 入口 |
| --- | --- |
| 06 上下文与协作 | [context](context.md)、[AI 规则](agent-rules.md)、[团队安排](docs/team-guide.md) |
| 07 原版 Spec | [v1 范围](spec/mvp1-scope.md)、[五模块 Spec](spec/README.md)、[冷启动记录](docs/test/cold-start-01.md) |
| 08 原版架构 | [v1 架构](docs/architecture.md)、[ADR-001](adr/ADR-001-runtime-and-state.md)、[ADR-002](adr/ADR-002-atomicity-and-replay.md) |
| 09 原版任务 | [十二项 Plan](plans/mvp1-plan.md)、[Issue 材料](plans/issues/README.md) |
| 原版验收 | [交付检查表](docs/delivery-checklist.md)、[追踪矩阵](docs/traceability.md)、[v1 实现结果](docs/test/implementation-results.md) |

`src/` 与 `tests/` 是保留的 v1；v2 正式源码在 `frontend/`、`backend/`。运行时数据库、密钥、日志与本地截图位于被 Git 忽略的 `.local/`。

本地可靠性整改：[审查处理矩阵](docs/v2/review-response.md) · [运行、指标与备份](docs/v2/operations.md) · [后端工程审查与整改](docs/v2/backend-engineering.md)。

当前地图扩展：[东岸、南岸营地与资源循环](docs/v2/map-expansion.md)。
