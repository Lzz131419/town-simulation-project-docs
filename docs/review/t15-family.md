# T15 家庭关系验收报告

已在原有未提交共享工作树上完成实现；未回滚、未提交、未改数据库 schema、未引入依赖或运行时资源。

## 实现

- 陈禾 / 苏晴为夫妻家庭 A，许宁 / 陆川为家人家庭 B；初始双向关系 80，下限 20；林溪、周木及玩家没有家庭分组。
- 首位家人认领一栋住宅时全家共享 home_id，保留单个 owner_id 作为产权代表。睡眠恢复、容量、升级与回家路径读取同一住宅；同宅任一家人入睡只点亮该宅一盏灯。
- 每日 18:00–19:00 家庭成员都在家门 48 单位内且未睡眠时共餐，饥饿 -15、双向关系 +2、写记忆与 family/meal 事件。每个家庭每个日历周最多 5 次；每人 shared_meal_day 与广场 feast 双向互斥，任一家人已赴广场聚餐会跳过全家的家庭共餐。
- 每个日界线按家庭一次判定，任一方向关系 <40 且持久化 RNG 抽样 <0.15 时争吵，双方饥饿 +5，当天相互社交在选人、发起和执行处均被屏蔽。争吵记忆进入现有 dispute gossip；随后 288 tick 内首次双方社交或共餐额外 +10 并发出和解事件。
- 玩家与已拥有住宅的家庭成员完成社交后，玩家对该人的关系达到 60，有 25% 概率收到邀请。每家庭/玩家冷却 432 tick，48 tick 内 visit 到同宅任何家人可赴约，双向全家关系 +8、玩家饥饿 -10、记忆与 invite 事件；受邀拜访不叠加普通 visit 的 +4。
- 受邀 visit 在实际到达时立即结算，截止 tick 到达仍有效；普通 visit 保留 T14 停留时间。家人不进入 visit 候选，回家也不消耗邀请。
- TownInspector 显示夫妻/家人及住宅全体住户；邀请采用持续高亮提示并提供“前去赴约”按钮，处理实时增量与消失；家庭共餐/争吵/和解分别使用温暖双音、低哑下行音、三和弦，沿用 T9 静音、播放上限、历史抑制和去重。

## 自动验证

后端执行：`cd backend && ../.venv/bin/python -m pytest tests -x -q`。

```text
........................................................................ [ 15%]
........................................................................ [ 31%]
........................................................................ [ 47%]
........................................................................ [ 63%]
........................................................................ [ 79%]
........................................................................ [ 95%]
......................                                                   [100%]
454 passed in 23.81s
```

新增 `backend/tests/test_family.py` 共 29 项，覆盖家庭认领顺序/满宅同住、共餐时间/距离/离线/限频/聚餐互斥、争吵概率与当天社交阻断、邻里纠纷及扰眠的关系下限、和解时效与一次性加成、邀请发出/赴约/截止到达/过期/家庭级冷却、visit 过滤、迁移资产保留/部分字段补齐/幂等、持久化 JSON 重放、实际 tick 调度。

前端执行：`cd frontend && npm run build`。

```text
> mist-river-town-client@2.0.0 build
> vue-tsc -b && vite build

vite v6.4.6 building for production...
transforming...
✓ 1666 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                        0.48 kB │ gzip:   0.35 kB
dist/assets/index-sdGeeNwq.css        52.29 kB │ gzip:  11.04 kB
dist/assets/phaser-CkuN5Vkn.js         0.47 kB │ gzip:   0.34 kB
dist/assets/TownScene-WC3wlyCu.js     45.92 kB │ gzip:  18.51 kB
dist/assets/index-CsjzCQfs.js        221.01 kB │ gzip:  79.26 kB
dist/assets/phaser-Czz4FBZH.js     1,481.77 kB │ gzip: 339.84 kB
✓ built in 4.24s
```

相关前端执行：`npx playwright test tests/family.spec.ts tests/audio.spec.ts tests/homes.spec.ts --reporter=line`。

```text
[13/21] tests/audio.spec.ts:433:1 › autoplay resume rejection retries, zero volume stays silent, controls fit the supported minimum width
[14/21] tests/audio.spec.ts:470:1 › unavailable WebAudio does not break incoming events or the UI
[15/21] tests/audio.spec.ts:490:1 › market ambience is daytime-only and uses the same mute/environment gates
[16/21] tests/audio.spec.ts:504:1 › live market patches toggle chip, murmur and occasional chime, then expire
[17/21] tests/family.spec.ts:79:1 › invitations survive incremental sync; malformed state is rejected atomically
[18/21] tests/family.spec.ts:97:1 › family sounds differ and NPC events obey dedupe and history suppression
[19/21] tests/family.spec.ts:122:1 › live invite schedules visit and inspector shows relatives and household residents
[20/21] tests/homes.spec.ts:3:1 › three home levels render together, upgrades flash, and only an owner's sleeping home lights
[21/21] tests/homes.spec.ts:50:1 › home upgrades arrive through world deltas and invalid levels reject atomically
  21 passed (22.7s)
```

新增前端 3 项验证家庭增量字段及无效包原子拒绝、家庭音色与 NPC 事件历史/去重、真实 Vue 页面中的实时邀请/赴约请求/夫妻关系及住户显示。页面测试使用 API/WebSocket 隔离 mock，未改在线存档；现有该仓库 5173 Vite 进程 cwd 已核对。音效验证为合成参数及自动化播放调用验证，并非人工听感评测。

本次涉及的 Python 文件 ruff 检查与 `git diff --check` 均通过。

## 完整事件 JSON

完整事件与前后状态见 [t15-family-events.json](./t15-family-events.json)。

- 争吵 → 和解：家庭双向关系预置 30，固定 RNG=0，tick 96 `family/quarrel`；tick 204 实际 tick 调度触发 `family/meal` → `family/reconcile`，最终双方关系 42（30 + 2 + 10）。
- 邀请 → 赴约：玩家/陈禾初始双向 60，tick 10 真实 social 动作后 65，固定 RNG=0 发邀请（expires_tick=58）；真实排队 visit 在 tick 11 到达并触发 `invite/accepted`，玩家/陈禾关系 73、玩家/苏晴关系 38，玩家饥饿 60 → 50。

以上两条是构造前置状态后运行真实业务函数与调度器的可复现场景，区别于下面的自然模拟；JSON 保存了全部事件而非手写示例。

## 两天模拟后的 7 栋住宅

从全新 initial_world 连续运行 288 tick，无强制认领或强制事件；NPC 使用默认作息，六位玩家保持原有 manual 状态。资金/状态不变量通过。

| 住宅 | owner 代表 | 实际住户 | 等级 |
|---|---|---|---|
| home-1 | 林溪 | 林溪 | 1 |
| home-2 | 空置 | — | 1 |
| home-3 | 空置 | — | 1 |
| home-4 | 周木 | 周木 | 1 |
| home-5 | 许宁 | 许宁、陆川 | 1 |
| home-6 | 空置 | — | 1 |
| home-7 | 陈禾 | 陈禾、苏晴 | 1 |

六名 NPC 共同占用四栋，三栋仍可认领；六位玩家均尚未主动认领。该两天样本产生 4 次 home_claimed、1 次广场 feast，未自然触发 family/invite；这不作为自然事件触发频率或长期生活效果的证据。

## 边界与口径

- 复用现有 144 tick/日与 dawn_offset_ticks=48 的日界线，即 tick 96、240 等；未重定义项目原有“黎明”时钟。每周为该日号的固定 7 天日历周，不是滑动 7 天窗口。
- 只有真实共处且清醒时才共餐，不为保证事件强制传送、召回或叫醒 NPC；离线标记不排除在家的家人。因此默认两天样本没有家庭共餐，长期自然触发率未评估。
- 邀请要求家庭有房，玩家无需先有房；玩家对主人的关系用完成 social 后的值判定。冷却从发出时起算，对同一家庭/同一玩家生效；不同家庭和不同玩家分别计时。
- 有效邀请以抵达该住宅为履约，主人途中离家不会将玩家改道广场；这是有邀请的例外，普通 T14 串门仍要求主人在家。期限是世界 tick，不是现实时间；超出截止 tick 后仅邀请者与玩家双向 -2，不扣其他家人的关系。
- 血缘/夫妻关系下限仅家庭适用，非家庭原规则不变。和解消耗争吵标记但不解除当天社交冷静期；共餐可在当天和解，过 288 tick 则无额外 +10。
- 旧档缺失家庭关系才补 80，已有关系保留并钳制到最低 20。旧档家人若各有房，选已有住宅中等级最高者（同级按 id），归并 home_id，释放其余 owner_id；所有建筑等级、个人现金/库存/任务/计划保留。释放后的房屋等级也保留；未重置资产。
- 轻前端保留既有住宅点击选 owner 的交互，owner 面板显示全体住户；兄妹使用“家人”标签，避免额外推断性别/长幼。家庭结构是预设字段，本任务未增加结婚、离婚或玩家组建家庭操作。

## 共享工作树 diff

下列是任务完成时实际 `git diff --stat`，包含此前全部未提交改动，不能当作 T15 单独变更量；Git 默认不计未跟踪文件。全文也保存于 [t15-diff-stat.txt](./t15-diff-stat.txt)。

```text
backend/app/api/auth.py                          |  21 +-
 backend/app/api/realtime.py                      |   8 +-
 backend/app/api/world.py                         | 125 ++++++--
 backend/app/balance.py                           | 183 ++++++++++++
 backend/app/catalog.py                           |  49 +++
 backend/app/domain/actions.py                    | 294 ++++++++++++++----
 backend/app/domain/deliveries.py                 |  27 +-
 backend/app/domain/economy.py                    |  39 +++
 backend/app/domain/migration.py                  |  89 +++++-
 backend/app/domain/orders.py                     |  65 +++-
 backend/app/domain/plans.py                      |   2 +-
 backend/app/domain/progression.py                |  11 +-
 backend/app/domain/rules.py                      |  21 +-
 backend/app/domain/scheduler.py                  | 366 ++++++++++++++++++++---
 backend/app/pathfinding.py                       |  17 +-
 backend/app/realtime/protocol.py                 |   6 +
 backend/app/runtime.py                           |  59 +++-
 backend/app/schemas.py                           |   1 +
 backend/app/services/history.py                  |  19 +-
 backend/config/game.json                         |  62 +++-
 backend/tests/test_districts.py                  |   7 +-
 backend/tests/test_map_expansion.py              |  11 +-
 backend/tests/test_plan_queue.py                 |  10 +-
 backend/tests/test_reliability.py                |   9 +-
 backend/tests/test_world.py                      |   3 +-
 frontend/src/components/DeliveryBoard.vue        |  21 +-
 frontend/src/components/EventDetails.vue         |   8 +-
 frontend/src/components/RecipeBook.vue           |  12 +-
 frontend/src/components/ReportDashboard.vue      |  60 +++-
 frontend/src/components/TownInspector.vue        | 149 ++++++++-
 frontend/src/components/TownMap.vue              |  32 +-
 frontend/src/components/charts/ResourceChart.vue |   4 +-
 frontend/src/components/dialogs/PlaceDialog.vue  |   4 +-
 frontend/src/components/dialogs/ReturnDialog.vue |  14 +-
 frontend/src/components/layout/ShellHeader.vue   |  15 +-
 frontend/src/composables/useReports.ts           |  13 +-
 frontend/src/game/Atmosphere.ts                  | 180 ++++++++++-
 frontend/src/game/ResidentLayer.ts               |  87 +++++-
 frontend/src/game/TownScene.ts                   |  52 +++-
 frontend/src/game/art/map.ts                     |   5 +-
 frontend/src/game/art/vegetation.ts              |  39 ++-
 frontend/src/game/scene-types.ts                 |   5 +-
 frontend/src/realtime/protocol.ts                |  76 ++++-
 frontend/src/stores/town.ts                      |  51 +++-
 frontend/src/styles/game-ui.css                  |  33 ++
 frontend/src/styles/reports.css                  |  29 ++
 frontend/src/types.ts                            |  65 +++-
 frontend/src/views/MarketView.vue                | 123 +++++++-
 frontend/src/views/ProjectView.vue               |   4 +-
 frontend/src/views/TownView.vue                  |  62 +++-
 frontend/tests/browser.spec.ts                   |   2 +-
 frontend/tests/districts.spec.ts                 |   2 +-
 frontend/tests/journey.spec.ts                   |   2 +-
 frontend/tests/lighting.spec.ts                  |   2 +-
 frontend/tests/map.spec.ts                       |  24 +-
 frontend/tests/queue.spec.ts                     |   2 +-
 frontend/tests/reliability.spec.ts               |  20 +-
 57 files changed, 2384 insertions(+), 317 deletions(-)
```

T15 实际编辑文件：

- 后端：`backend/app/balance.py`、`catalog.py`、`domain/family.py`（新增）、`homes.py`、`migration.py`、`scheduler.py`、`initiatives.py`、`actions.py`、`leisure.py`、`fortune.py`、`sleep.py`、`backend/tests/test_family.py`（新增）。
- 前端：`frontend/src/types.ts`、`components/TownInspector.vue`、`views/TownView.vue`、`game/Atmosphere.ts`、`game/audio.ts`、`realtime/protocol.ts`、`frontend/tests/family.spec.ts`（新增）。
- 证据：本报告、`t15-family-events.json`、`t15-pytest.txt`、`t15-build.txt`、`t15-frontend-tests.txt`、`t15-diff-stat.txt`。
