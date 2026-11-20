# v2 本地验证记录

日期：2026-11-19。环境：macOS、Python 3.12.10、Node.js 22.23.3、SQLite WAL、Google Chrome（Playwright channel）。所有结果来自本机；未触发本轮远程 CI、未部署外部云端。

## 验证结果

| 检查 | 结果 | 原始记录 |
| --- | --- | --- |
| 新版后端业务/接口/AI 流程 | 31 项通过 | [pytest](evidence/backend-tests.txt) |
| Vue 类型检查与生产构建 | 通过，strict 与未使用变量检查启用 | [build](evidence/frontend-build.txt) |
| 后端 lint 与前端格式 | 通过 | [lint](evidence/lint.txt) |
| 浏览器联调 | 3 项场景通过 | [Playwright](evidence/browser-tests.txt) |
| v1 回归 | 44 项通过，历史版本验证 | [legacy](evidence/legacy-tests.txt) |
| v1 原子性与重放探针 | 5 项通过，历史规则验证 | [spike](evidence/spike-tests.txt) |
| 真实服务进程重启 | 世界 tick、revision 与完整状态摘要一致 | [restart](evidence/restart-verification.json) |
| FastAPI 直接托管生产网页 | Chrome 登录、接口、WebSocket 与地图成功 | [production smoke](evidence/production-smoke.txt) |
| 文档结构/引用 | 通过，语义与人工评审另行判断 | [docs check](evidence/docs-check.txt) |

重启验证：正常停止服务，在 revision=1057、tick=1049 读取数据库；用长时钟间隔重启以隔离自然时间推进，再通过已登录 HTTP 请求读取同一状态。前后完整世界 JSON 的 SHA-256 均为 `1b2322398c3845749901ad276f23158f0aa2db29e0e3266d1d25b893ae8ceba5`。之后恢复默认 2 秒时钟。该验证确认进程重启保留状态，不意味着时钟停服期间会继续运行。

## 浏览器场景

1. 六个独立浏览器上下文同时登录，在线人数为 6；王崛采收到达后获得谷物，另一名玩家读到相同资产变化；遍历九个功能入口，发送跨成员留言、创建/查看归档、扩大地图与 Escape 返回；1280×720 无页面水平溢出。
2. 保存个人计划并开启规则托管，退出再登录，托管模式保持；随后手动接管。
3. 两名成员通过界面发布并交付面包采购，验证托管扣款、唯一交付、买卖双方余额与买方物资变化。

浏览器脚本在[测试文件](../../frontend/tests/browser.spec.ts)。测试使用本地演示账户与数据，不包含真实外部模型连接。

## 验收追踪

| 验收 | 证据与范围 |
| --- | --- |
| V2-AC-01、V2-AC-02 | 六账号参数化、认证/归属测试；六上下文联调 |
| V2-AC-03、V2-AC-04 | 到达后结算、拒绝无副作用、路径避障、600 tick 守恒与状态边界 |
| V2-AC-05 | 托管/交付/取消/到期、重复交付、两卖家并发只支付一次；界面联调 |
| V2-AC-06 | 仓库资源目标与容量解锁测试 |
| V2-AC-07 | 完整 LangGraph mock、非法动作拒绝、HTTP MockTransport 请求与用量验证；真实模型未验收 |
| V2-AC-08 | 离线入口拦截、断开取消任务、迟到结果拒绝、120 tick 离线规则不调用模型 |
| V2-AC-09 | 保留余额、每日预算与容量边界测试 |
| V2-AC-10 | 私信隔离与浏览器跨成员收发；事件筛选/分页接口与页面已实现 |
| V2-AC-11 | 归档所有权/安全恢复；跨会话持久化；真实进程重启状态比较 |
| V2-AC-12 | 离线推进后的完成次数、余额变化、事件上限与其他用户隔离测试 |
| V2-AC-13 | 1440×900/DPR2、1280×720/DPR1 的实际画布尺寸、导览、跟随、缩放/重置、小地图、扩大/恢复与无页面错误检查 |
| V2-AC-14 | 成功/失败计数、徽章唯一发放、订单重复交付、旧字段兼容、迁移幂等、归档恢复不回退；浏览器采收达成徽章并刷新保留 |
| V2-AC-15 | 指定目标到达后双向关系、无效/本人/离开目标拒绝、熟悉度上限；浏览器选择李展博交流并刷新保留 |

后端测试入口：[world](../../backend/tests/test_world.py)、[agent](../../backend/tests/test_agent.py)、[lifecycle](../../backend/tests/test_lifecycle.py)。

## 视觉检查

实际截图：[桌面地图](evidence/town-desktop.png)、[1280 地图](evidence/town-1280.png)、[AI 工作区](evidence/agent-desktop.png)、[登录](evidence/login.png)、[合作订单](evidence/orders-desktop.png)、[共同建设](evidence/project-desktop.png)。

已检查地图占据主区、业务区纸面线稿配色、中文标签、九页面入口和桌面溢出。场景使用原项目原创画面，未下载 Stanford Smallville 的游戏素材。截图是本地运行结果，不是设计稿。

## 登录与工作区视觉修订验证

2026-11-19 根据用户反馈完成第二轮视觉修订。构建、Ruff、前端格式检查通过；使用 Chrome 检查居民切换、密码显示/隐藏、登录/退出和九个工作区入口，无页面脚本错误。1440×900 与 1280×720 登录布局均可完整显示，无横向溢出。此轮以界面验证为主，未重复运行不受本次改动影响的后端业务测试。

[本轮界面检查](evidence/ui-review.txt) · [检查摘要](evidence/ui-refresh-verification.json) · [新版登录 1440](evidence/login.png) · [新版登录 1280](evidence/login-1280.png)

### 居民面板白底修订

2026-11-19：移除用户截图所指的灰色填充。生产构建与代码检查通过；Chrome 验证头像、物资、AI 入口、选中行与侧栏实际背景为白色或透明，居民切换、AI 页面跳转正常，1440/1280 桌面无水平溢出，无页面脚本错误。

[居民面板截图](evidence/town-desktop.png) · [完整居民列表](evidence/resident-roster.png) · [账户区](evidence/account.png)

### Lofi 参考配色验证

2026-11-19：应用统一浅蓝灰/白色/石墨色 token。前端构建和格式检查通过；Chrome 检查九个页面入口、居民选择、密码显隐、登录与退出，无页面脚本错误；1440×900 和 1280×720 桌面布局正常。实际计算样式确认工作区为浅蓝灰，侧栏、顶栏、头像、AI 入口和居民选中行仍为白色，物资统计背景透明。

[配色检查](evidence/lofi-palette-verification.json) · [登录 1280](evidence/login-1280.png) · [登录 1440](evidence/login.png) · [AI 工作区](evidence/agent-desktop.png)

### 线稿贴纸主题（当前版本）

2026-11-19：依据用户提供的最新预览截图实现黑色线稿、白色纸面及少量彩色贴纸，替换上一轮浅蓝灰主题。上方各次视觉修订按历史记录保留，通用页面截图现已更新为本轮实际运行结果。

Chrome 实测 1440×900 与全新 1280×720 浏览器上下文：九个页面均无横向溢出，登录、居民切换、密码显隐和退出正常；居民姓名开关、地图缩放、重置与扩大/恢复正常。1280 桌面普通地图尺寸为 741×462，扩大后宽度超过 1200；侧栏、居民面板和头像为白色，物资统计透明，当前导航为黄绿色。未发现页面脚本错误。此轮没有调用外部模型，也没有重新运行未受影响的后端业务测试。

[本轮检查](evidence/sketch-review.txt) · [布局与实际颜色](evidence/sketch-verification.json) · [登录](evidence/login.png) · [1280 小镇](evidence/town-1280.png) · [AI 工作区](evidence/agent-desktop.png)

### 高清场景、成长与指定交流（当前游戏版本）

2026-11-19：本轮替换旧低细节像素地图，增加高清地形、各类室内、四向行走、环境动态和真实事件结果浮字；新增生活手册与指定邻居交流。业务壳层沿用纸面线稿主题。此前各轮视觉记录为历史快照，以本节和当前证据为准。

- 后端38项测试通过，覆盖已有业务与本轮成长、迁移和交流边界。构建与代码检查通过。
- 完整浏览器4个场景通过：六成员同时在线与采收、各业务页与归档、离线计划保留、双人托管订单，以及新加入的采收徽章与指定李展博交流/刷新保留。使用独立SQLite测试库和8011测试服务、0.5秒tick，没有修改本地玩家世界来造验收数据。默认运行仍为2秒tick。
- 真实Chrome界面检查：1440×900/DPR2画布为1794×1254，CSS尺寸897×627；1280×720/DPR1画布为737×458，CSS尺寸相同。检查了生活手册六项、Escape关闭、地点导览、跟随开关、地图缩放/重置、小地图定位和扩大/恢复，无页面脚本错误与横向溢出。
- 更新前备份了本地世界。成长字段为增量兼容，已有资产、计划和世界时钟保留；历史分项成长未编造。徽章与等级不增发资金、不改变能力，不调用外部模型。

[后端测试](evidence/game-backend-tests.txt) · [四个浏览器场景](evidence/game-browser-tests.txt) · [画布与交互检查](evidence/game-verification.json) · [普通地图](evidence/town-desktop.png) · [大地图](evidence/town-expanded.png) · [生活手册](evidence/life-journal.png)

## 尚未验证与不应推断的结论

- 没有使用任何成员真实 API Key；不能把 mock 成功写成某家模型服务已经可用，也不能声称已经评估了人格一致性或真实成本。
- 已验证取消本地异步请求和离线不续发；不保证第三方撤销已接收请求的费用。
- PostgreSQL、Docker 镜像/Compose、远程设备访问和外部云端持久化尚未验收。
- 未进行多进程、多世界或大规模压力测试；六浏览器上下文不等于已经实测六台物理设备。
- 没有伪造非作者人工评审、用户试玩反馈、课程教师接受或线上提交状态。
- CI 工作流已在本地更新，GitHub 尚未运行此新版工作流。

## 审查整改验收（2026-11-19）

| 新增验收 | 对应证据 |
| --- | --- |
| V2-AC-16 | test_reliability.py：slow_socket、cancelled_worker、delta_roundtrip、protocol2_patch、resync；浏览器坏包与断线恢复 |
| V2-AC-17 | reliability.spec.ts：request timeout、startup failure、broken websocket；模型失败保持计划测试 |
| V2-AC-18 | test_reliability.py：daily_levy、poor_treasury、npc_schedule、ten_days_rules |
| V2-AC-19 | test_reliability.py：history_upsert；reliability.spec.ts：economic charts；实际桌面截图 |

本轮测试使用独立测试库，不修改用户数据库生成证据。测试结果及范围在[审查响应](review-response.md)记录；备份shell与Compose通过静态检查，stub执行证明失败保留旧文件，不代表真实PostgreSQL恢复成功。没有调用成员真实模型、没有GitHub提交。

[后端测试](evidence/review-backend-tests.txt) · [浏览器回归](evidence/review-browser-tests.txt) · [1440报表](evidence/review-report-1440.png) · [1280报表](evidence/review-report-1280.png) · [运行与备份](operations.md)

本轮最终结果：后端 **72 passed**；完整浏览器场景 **9 passed**；补强嵌套同步字段校验后，5个可靠性场景再次通过；旧版 **44 passed**。生产构建、Ruff、Prettier、文档结构/链接、Compose配置及shell语法检查通过。最后关系图文字偏移修订后再次构建，并用真实Chrome重新查看1440/DPR2及1280/DPR1报表和本地地图，无页面脚本错误与横向溢出。

更新运行服务前已生成SQLite一致性备份，integrity_check为ok；备份时世界tick为8636、revision为8663、12居民、总资金2840。重启后仍延续原世界（tick8721、revision8749），资金总量2840，health正常。原端口5173/8000继续服务，测试端口8011在验收后关闭。

[最终画布与运行记录](evidence/review-ui-verification.json) · [协议补充回归](evidence/review-protocol-retest.txt) · [图表细节1440](evidence/review-report-detail-1440.png) · [图表细节1280](evidence/review-report-detail-1280.png) · [当前本地地图](evidence/review-local-town.png) · [构建](evidence/review-build.txt) · [代码检查](evidence/review-lint.txt) · [文档检查](evidence/review-docs-check.txt)

## 东岸地图与资源循环（2026-11-19 当前地图版本）

| 验收 | 验证 |
| --- | --- |
| V2-AC-20 | test_map_expansion：全部新增地点经桥到达、桥外水面/建筑入口检查、地图迁移、路线接口只读；map.spec：分区与导览操作 |
| V2-AC-21 | test_map_expansion：全部配方、工具增产、失败不扣原料/工具、食品属性上限、新商品订单与托管；map.spec：真实果园采集/食用、工具与烤鱼链 |

- **94项后端测试通过**，包含新增22项；**11个浏览器场景通过**，包含新增地图与完整资源链两个场景。无外部模型调用。
- 生产构建、Ruff、Prettier通过。最终地点面板布局调整后重新构建并在Chrome检查1440×900/DPR2和1280×720/DPR1的四分区、全镇小地图与地点详情，无横向溢出和页面脚本错误。
- 独立测试库使用0.15秒tick；本地用户世界仍为2秒tick。没有把加速测试下的步行秒数当成默认运行速度。
- 当前SQLite一致性备份通过integrity_check。迁移预检保留12名居民的资产、属性、模式、计划、规则和成长；世界总资金仍为2840，幂等检查通过。只为新版几何修正不可通行的位置与当前路线，新增商品库存补0。

[地图与玩法说明](map-expansion.md) · [后端测试](evidence/map-backend-tests.txt) · [浏览器场景](evidence/map-browser-tests.txt) · [画布检查](evidence/map-ui-verification.json) · [存档迁移](evidence/map-migration-verification.json) · [构建](evidence/map-build.txt) · [代码检查](evidence/map-lint.txt)

[东岸1440](evidence/map-east-1440.png) · [东岸1280](evidence/map-east-1280.png) · [全镇](evidence/map-overview-1440.png) · [南岸营地](evidence/map-south-1440.png) · [地点详情](evidence/map-place-1280.png)

收尾补充：修复真实Chrome关闭连接时WebSocket关闭帧可能再次抛出断线异常的问题，新增针对性测试并重跑后端与代码检查。日常5173开发预览通过两种桌面尺寸检查；重启后的地图版本为2，继续原有世界，health正常。

[日常开发预览](evidence/map-local-ui-verification.json) · [默认速度地点详情](evidence/map-local-place-1280.png) · [本地重启与连接检查](evidence/map-local-smoke.txt)

## 行程操作与配方图鉴（2026-11-19）

本轮细化V2-AC-20、21，保持21项验收总数不变。新增组件独立实现，业务状态仍由服务端拥有，没有新增数据迁移或外部模型请求。

- 后端 **95 passed**（本轮原始控制台结果：10.75s）。新增停止行程回归：路径和任务清空，状态正确更新，资产、坐标、成长和未执行计划保留；移动速度目录与寻路常量一致。
- Playwright **13 passed / 53.0s**，其中12项真实浏览器/API集成场景、1项纯路径函数回归。新增场景实际跑通配方缺料来源跳转、背包食用、缺货禁用、停止行程、保留两步计划，以及连续三次扩大/恢复地图。旧六人在线、订单、离线规则、生产链、异常重连和报表回归继续通过。
- 路径纯函数覆盖转角、行走中途停止、替换路径、空路径和权威位置突变，避免旧长度差插值导致绕回或穿越障碍。相机验收按地图边界计算允许的中心钳制，恢复后中心/宽度与原视野误差小于2逻辑单位。
- Chrome检查1440×900/DPR2与1280×720/DPR1的小镇、制作图鉴、饮食恢复图鉴，无脚本错误和横向溢出；长图鉴在弹窗内滚动。构建、Ruff和Prettier通过。最后仅移除禁用配方按钮的灰底后重新构建、复查页面与格式。
- 测试使用独立SQLite库、0.15秒tick；本地世界仍为2秒tick，未用于测试采收/消耗。更新前SQLite一致性备份integrity_check为ok；重启后12居民、地图版本2、总资金2840，tick从备份10843继续至检查11001，health正常。

[完整回归](evidence/journey-browser-tests.txt) · [构建](evidence/journey-build.txt) · [代码检查](evidence/journey-lint.txt) · [桌面检查](evidence/journey-visual.json) · [运行与备份](evidence/journey-local-smoke.json)

[地图与行动栏](evidence/journey-town-1280.png) · [制作图鉴](evidence/journey-recipes-1280.png) · [饮食恢复图鉴](evidence/journey-food-1280.png)

## 行动队列与有限执行（2026-11-20）

新增V2-AC-22：`test_plan_queue.py`验证追加、8步上限、旧值比较冲突、执行完停止、即时/到达失败暂停、归属保护和离线无模型调用；`queue.spec.ts`通过真实界面完成采收→烘焙→食用、调整/移除步骤、缺料暂停、过期草稿拒绝与退出后继续已有安排。

- 后端 **104 passed / 10.84s**；前端Playwright **15 passed**，包含两个新增队列场景。使用独立SQLite库、0.15秒tick，没有在用户世界内制造生产或消费记录。
- 构建、Ruff与Prettier通过。最终增加计划完成/暂停筛选、展开图标和地图加载态后，重新构建并在Chrome检查1440×900/DPR2、1280×720/DPR1：队列完整位于屏幕内，配方可加入计划，AI页提供仅执行本轮，事件分类可用，无页面脚本错误和横向溢出。
- 有限计划失败后保留的是尚未开始的步骤，失败步骤不会自动重试；长期规则模式保留原行为。队列编辑冲突时保留草稿并要求同步；没有宣称自动推导整条生产链。
- 本地服务已按新模式和新接口启动，默认2秒tick。更新前SQLite一致性备份正常；重启后12居民、总资金2840、世界时钟继续，health正常。没有重置原存档，没有GitHub提交或外部模型请求。

[设计与边界](action-queue.md) · [后端测试](evidence/queue-backend-tests.txt) · [前端回归](evidence/queue-browser-tests.txt) · [构建](evidence/queue-build.txt) · [代码检查](evidence/queue-lint.txt)

[桌面检查](evidence/queue-visual.json) · [1280行动队列](evidence/queue-panel-1280.png) · [1280配方入口](evidence/queue-recipes-1280.png) · [本地服务与备份](evidence/queue-local-smoke.json) · [日常预览检查](evidence/queue-local-visual.json)


## 街区与社区交付（2026-11-20）

新增V2-AC-23，并扩展AC-20、21。当前地图版本3包含5分区、21地点、15种商品和3座桥；Spec现有23项验收标准。

- 后端 **123 passed / 13.71s**。覆盖所有地点可达、第三座桥通行、建筑不重叠、旧地图幂等迁移、六种交付的收支守恒、缺料/预算不足/重复/每日上限失败原子性，以及嵌套家具配方的缺料来源。原配方参数化测试同步覆盖新配方与饮食效果。
- Playwright完整回归 **16 passed / 1.5m**。新增实际界面完成收割亚麻→织布→两次木作→家具→交付，检查排队不预支资产、到达后消耗物资并获得22镇币、有限计划完成停止。原六人在线、玩家订单、重连、队列、报表场景继续通过。
- 增量协议测试覆盖供应统计与交付日志，阻止非法结构写入；修复原本未接纳supply字段会触发全量重同步的问题。另以独立浏览器回归 **1 passed / 2.0s** 检查直接点击建筑仍能打开详情、分区按钮不会误触地图建筑；合计17项前端场景通过，见下列原始结果。
- 生产构建、Ruff与Prettier通过。Chrome在1440×900/DPR2、1280×720/DPR1检查五个分区、全镇、21项地点导览与六种交付面板，无横向溢出或页面脚本错误；本地5173开发服务也完成同样检查。地图昼夜效果在截图中关闭以检查原始绘制。
- 测试生产和交付使用独立SQLite库与0.15秒tick。真实本地存档更新前已作一致性备份、integrity_check通过；干运行证明原资产、模式、计划、成长、时间保留，新物资补零。重启后地图版本3、12名居民、21地点、15商品、总资金2840，默认2秒tick，世界时间继续。
- 场景装饰不冒充可驾驶车辆、建造玩法或独立地图副本；本轮没有真实模型调用、远程部署或GitHub提交。

[玩法与边界](district-expansion.md) · [后端测试](evidence/district-backend-tests.txt) · [完整前端回归](evidence/district-browser-tests.txt) · [画布点击回归](evidence/district-canvas-tests.txt) · [构建](evidence/district-build.txt) · [代码检查](evidence/district-lint.txt)

[桌面检查](evidence/district-visual.json) · [迁移预检与备份](evidence/district-migration-verification.json) · [本地服务检查](evidence/district-local-smoke.json)

[全镇](evidence/district-overview-1440.png) · [手作街区1440](evidence/district-craft-1440.png) · [手作街区1280](evidence/district-craft-1280.png) · [南岸商埠](evidence/district-harbor-1440.png) · [南部田园](evidence/district-south-1280.png) · [交付面板](evidence/district-depot-1280.png)


## 地图材质与昼夜渲染（2026-11-20）

细化V2-AC-13、20，保持23项验收标准。静态材质、建筑外壳、路灯定义与时段曲线拆成独立模块；保留地图3的21地点与原有寻路碰撞。

- 生产构建、Ruff与Prettier通过。Playwright **19 passed / 1.6m**，包括此前17项回归以及新增的昼夜曲线、实际画布像素两项检查。像素检查验证夜景亮度低于白昼85%且高于50%，关闭环境效果后平均亮度误差低于4（RGB亮度0–255）；这也防止透明填充使昼夜覆盖永久不可见的旧问题复发。
- Chrome检查1440×900/DPR2和1280×720/DPR1：五个分区、全镇、白昼／黄昏／夜景／关闭效果，页面脚本错误为0，无横向溢出。检查相机实际视野稳定后截图，画布尺寸与设备像素比一致。
- 时段通过浏览器显示tick夹具固定，未修改真实数据库时钟；操作测试使用独立SQLite库。构建后5173预览可用，本轮无需重启后端或迁移存档，没有外部模型调用或GitHub提交。

[材质设计与实现边界](rendering.md) · [构建](evidence/render-build.txt) · [代码检查](evidence/render-lint.txt) · [19项回归](evidence/render-browser-tests.txt) · [桌面检查](evidence/render-visual.json)

[中心街区](evidence/render-day-town-1440.png) · [手作街区](evidence/render-day-craft-1280.png) · [南岸白昼](evidence/render-day-harbor-1440.png) · [全镇](evidence/render-day-overview-1440.png) · [黄昏](evidence/render-dusk-1440.png) · [夜景](evidence/render-night-1280.png) · [关闭环境效果](evidence/render-unlit-1280.png)


## 后端工程化审查与修复

2026-11-20：新增V2-AC-24，细化AC-16、17；Spec现有24项验收标准。

- 后端147项测试通过，语句覆盖率94.09%，新增90%门禁。涵盖线程取消不提前释放锁、慢密码计算不阻塞存活接口、连接校验故障后的时钟恢复、就绪故障与恢复、模型记录创建时取消、严格参数与历史游标边界、迁移/部分索引恢复/冲突拒绝。
- 独立SQLite库上的19项浏览器回归通过；Ruff与前端格式检查通过。真实模型调用为0。
- 停服前后分别备份并演练，10张旧表的行内容与行数不变；真实库升级到Alembic 0002后、启动tick前再次核对完全一致。重启后12名居民、总资金2840保持，tick继续推进；健康检查和5173预览正常。
- V2-AC-24对应`test_backend_engineering.py`迁移与健康检查用例、真实存档副本演练及本地服务检查。未完成PostgreSQL/远程CI/多实例容量验收。

[审查矩阵与边界](backend-engineering.md) · [后端测试](evidence/backend-audit-tests.txt) · [浏览器回归](evidence/backend-audit-browser.txt) · [迁移](evidence/backend-audit-migration.json) · [服务检查](evidence/backend-audit-local-smoke.json)
