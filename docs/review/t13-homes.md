# T13 家园升级验收

已实现住宅认领、1→3 级升级、容量与睡眠加成、三级每日减饥饿、NPC 升级倾向及前端三级视觉。保持共享工作树已有改动，未回滚、未提交；未修改数据库 schema、未增加依赖或美术资源。

## 实现与边界

- 七栋住宅取自 `shared/world-map.json` 的 `house-1…7`，持久身份对应 `home-1…7`，JSON x/y 是房屋视觉中心。寻路使用住宅门前可行走点，七个门口均测试可达；`/api/me/route?place=home` 使用同一目的地。
- 首次安排 `rest` 且路线成功时即认领最近空宅，避免多个在途居民争同一栋；直接执行睡眠也会认领。以后 `home` 指本人住宅，七栋满员后使用广场长椅 `(423,450)`，恢复倍率 0.5。旧档与部分 homes 字段幂等补齐，不覆盖已有等级/资产。
- 1→2 消耗 15 木材 + 60 镇币；2→3 消耗 30 木材 + 150 镇币。木材扣除，现金转入公库，守恒校验保持不变。失败先校验再变更，满级、无家、缺木材/现金、未到家均有原子性测试。
- 各级容量加成 +10/+20/+30，叠加共享仓库基础 30/60；睡眠 ×1.0/1.3/1.6，精力保留两位小数。三级住宅在既有 `is_dawn` 日边界（tick 96、240…）减饥饿 5，最低 0；同 tick 常规饥饿增长照常生效。
- diligent/generous 的 fallback 在基本饥饿/精力需求与防洪之后优先升级，需现金 > reserve×3、足额木材且支付后保留 reserve。升级作为大额家庭支出不受原来 16/20 的每日小额采购限额限制，但记入 spent_today；完成产生事件和个人记忆。
- 二级砖墙与加高烟囱，三级更宽屋檐、院篱和花坛，均为独立 art 图层。升级 900ms 金色边缘/尘点反馈；初始加载已有等级不闪。所有住宅标签显示主人与等级，点击已认领住宅选中主人，TownInspector 显示效果与升级入口。
- 夜间仅 owner_id ↔ home_id 匹配且主人正在睡眠的住宅亮灯；长椅与空宅不亮，换天不轮换。托管回家与正常回家共用路线。
- 顶栏个人容量已接入家园加成，共享仓库文案改成“基础容量”；前端增量协议接受并验证 homes，避免升级后增量包被拒绝。

## capacity 改造点

`capacity(w, a=None)` 保持无 agent 调用返回基础容量。全体生产调用已改造：

| 文件 | 调用点 | 容量所属居民 |
|---|---|---|
| domain/actions.py | 生产、购买 | a |
| domain/actions.py | 赠礼接收 | other |
| domain/orders.py | 订单交付容量 | buyer |
| domain/scheduler.py | 买面包、可执行工作、饥饿烘焙/售货/耕作、背包清理、最终配方空间 | a（共 7 处） |
| domain/scheduler.py | 慷慨居民选择赠礼对象 | other |
| domain/initiatives.py | NPC 私人订单含预留空间 | npc |
| domain/initiatives.py | 自动赠礼接收 | target |

完整搜索：`../../.local/t13-homes/capacity-calls.txt`。`engine.py` 继续兼容重导出；旧 `capacity(w)` 测试仍成立。新增测试还实证超过基础30容量的生产、采购、赠礼与订单交付，以及赠礼按接收者容量判断。

## 测试与视觉证据

后端新增 `backend/tests/test_homes.py` 共18项，旧 T12 sleep/reliability 的公共点定位改成家庭门口，认领事件加入预期序列；没有移除旧的睡眠/疲劳/扰醒/托管断言。

命令：`cd backend && ../.venv/bin/python -m pytest tests -x -q`

```text
........................................................................ [ 18%]
........................................................................ [ 36%]
........................................................................ [ 55%]
........................................................................ [ 73%]
........................................................................ [ 92%]
..............................                                           [100%]
390 passed in 17.97s
```

命令：`cd frontend && npm run build`

```text

> mist-river-town-client@2.0.0 build
> vue-tsc -b && vite build

vite v6.4.6 building for production...
transforming...
✓ 1665 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                        0.48 kB │ gzip:   0.35 kB
dist/assets/index-CUm43841.css        52.02 kB │ gzip:  10.98 kB
dist/assets/phaser-CkuN5Vkn.js         0.47 kB │ gzip:   0.34 kB
dist/assets/TownScene-CFWykvnQ.js     45.34 kB │ gzip:  18.25 kB
dist/assets/index-C5wknDH8.js        218.54 kB │ gzip:  78.35 kB
dist/assets/phaser-Czz4FBZH.js     1,481.77 kB │ gzip: 339.84 kB
✓ built in 3.31s
```

Playwright 命令：`cd frontend && npx playwright test tests/homes.spec.ts tests/visual-effects.spec.ts`。涵盖三级图层、升级闪光衰减、固定归属夜灯、无家灯灭、增量更新验证，以及已有天气、季节/冬雪、工作姿态、集市、睡眠渐隐和 reduced motion 回归。

```text

Running 10 tests using 1 worker

(node:52299) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
  ✓   1 tests/homes.spec.ts:3:1 › three home levels render together, upgrades flash, and only an owner's sleeping home lights (1.5s)
  ✓   2 tests/homes.spec.ts:50:1 › home upgrades arrive through world deltas and invalid levels reject atomically (87ms)
  ✓   3 tests/visual-effects.spec.ts:19:1 › weather applies on construction, switches layers, and respects ambience (1.1s)
  ✓   4 tests/visual-effects.spec.ts:54:1 › season palettes restore exactly and snow stays on a separate roof layer (1.3s)
  ✓   5 tests/visual-effects.spec.ts:73:1 › work poses run only when both server path and interpolation have stopped (1.7s)
  ✓   6 tests/visual-effects.spec.ts:104:1 › reduced motion freezes precipitation and disables work movement (931ms)
  ✓   7 tests/visual-effects.spec.ts:122:1 › all requested task aliases have two poses; unsupported tasks stay still (1ms)
  ✓   8 tests/visual-effects.spec.ts:138:1 › market day props appear immediately, last all day, and expire without rebaking (1.3s)
  ✓   9 tests/visual-effects.spec.ts:166:1 › sleep fades avatars, lights occupied houses at night, and waking restores them (1.4s)
  ✓  10 tests/visual-effects.spec.ts:215:1 › reduced motion hides sleeping residents immediately (783ms)

  10 passed (11.1s)
```

截图：[三级住宅同框](../v2/evidence/three-level-homes.png)。**已实际打开并查看截图**：左侧一级保留原外观，中间二级砖墙与加高烟囱清晰，右侧三级宽屋檐、花坛、院篱清晰，文字无遮挡。截图来自真实 TownScene 的独立 SceneReader fixture，不调用 API、不修改运行中的存档；视觉 fixture 给三栋指定等级，用于确定性验收，不代表现有玩家存档已经升级。

## 认领/升级事件

完整原始事件（含 before/after 资产）：[t13-home-events.json](t13-home-events.json)。由隔离 initial_world 调用真实 start_action/execute 生成，并执行 check_invariants；摘要：

```json
[
  {
    "type": "home_claimed",
    "text": "王崛 在南岸安了家",
    "details": {
      "home_id": "home-5",
      "level": 1
    }
  },
  {
    "type": "upgrade_home",
    "text": "王崛 的家升到了 2 级",
    "details": {
      "home_id": "home-5",
      "level": 2,
      "wood": 15,
      "amount": 60
    }
  },
  {
    "type": "upgrade_home",
    "text": "王崛 的家升到了 3 级",
    "details": {
      "home_id": "home-5",
      "level": 3,
      "wood": 30,
      "amount": 150
    }
  }
]
```

## git diff --stat

下表是当前**全部共享未提交改动**，包含 T13 开始前已有 T1–T12 改动，不能视为 T13 独立 diff；git diff 不列未跟踪文件。

```text
 backend/app/api/auth.py                          |  21 +-
 backend/app/api/realtime.py                      |   8 +-
 backend/app/api/world.py                         | 123 ++++++++--
 backend/app/balance.py                           | 149 ++++++++++++
 backend/app/catalog.py                           |  30 +++
 backend/app/domain/actions.py                    | 266 ++++++++++++++++-----
 backend/app/domain/deliveries.py                 |  27 ++-
 backend/app/domain/economy.py                    |  39 ++++
 backend/app/domain/migration.py                  |  50 +++-
 backend/app/domain/orders.py                     |  65 +++++-
 backend/app/domain/plans.py                      |   2 +-
 backend/app/domain/progression.py                |  11 +-
 backend/app/domain/rules.py                      |  17 +-
 backend/app/domain/scheduler.py                  | 283 +++++++++++++++++++----
 backend/app/pathfinding.py                       |  17 +-
 backend/app/realtime/protocol.py                 |   6 +
 backend/app/runtime.py                           |  59 +++--
 backend/app/schemas.py                           |   1 +
 backend/app/services/history.py                  |  19 +-
 backend/config/game.json                         |  52 ++++-
 backend/tests/test_districts.py                  |   7 +-
 backend/tests/test_map_expansion.py              |  11 +-
 backend/tests/test_plan_queue.py                 |  10 +-
 backend/tests/test_reliability.py                |   9 +-
 backend/tests/test_world.py                      |   3 +-
 frontend/src/components/DeliveryBoard.vue        |  21 +-
 frontend/src/components/EventDetails.vue         |   8 +-
 frontend/src/components/RecipeBook.vue           |  12 +-
 frontend/src/components/ReportDashboard.vue      |  60 ++++-
 frontend/src/components/TownInspector.vue        | 120 ++++++++--
 frontend/src/components/TownMap.vue              |  32 ++-
 frontend/src/components/charts/ResourceChart.vue |   4 +-
 frontend/src/components/dialogs/PlaceDialog.vue  |   4 +-
 frontend/src/components/dialogs/ReturnDialog.vue |  14 +-
 frontend/src/components/layout/ShellHeader.vue   |  15 +-
 frontend/src/composables/useReports.ts           |  13 +-
 frontend/src/game/Atmosphere.ts                  | 177 +++++++++++++-
 frontend/src/game/ResidentLayer.ts               |  36 ++-
 frontend/src/game/TownScene.ts                   |  52 ++++-
 frontend/src/game/art/map.ts                     |   5 +-
 frontend/src/game/art/vegetation.ts              |  39 +++-
 frontend/src/game/scene-types.ts                 |   5 +-
 frontend/src/realtime/protocol.ts                |  55 ++++-
 frontend/src/stores/town.ts                      |  51 +++-
 frontend/src/styles/game-ui.css                  |  33 +++
 frontend/src/styles/reports.css                  |  29 +++
 frontend/src/types.ts                            |  51 +++-
 frontend/src/views/MarketView.vue                | 123 +++++++++-
 frontend/src/views/ProjectView.vue               |   4 +-
 frontend/src/views/TownView.vue                  |  12 +
 frontend/tests/browser.spec.ts                   |   2 +-
 frontend/tests/districts.spec.ts                 |   2 +-
 frontend/tests/journey.spec.ts                   |   2 +-
 frontend/tests/lighting.spec.ts                  |   2 +-
 frontend/tests/map.spec.ts                       |  24 +-
 frontend/tests/queue.spec.ts                     |   2 +-
 frontend/tests/reliability.spec.ts               |  20 +-
 57 files changed, 2013 insertions(+), 301 deletions(-)
```

T13 新增文件：`backend/app/domain/homes.py`、`backend/tests/test_homes.py`、`frontend/src/game/art/homes.ts`、`frontend/tests/homes.spec.ts`、本报告与事件 JSON。另外修改此前已有/未跟踪的 sleep.py、test_sleep.py、visuals.ts 等文件。证据日志与截图保存在 `.local/t13-homes/`。

本次未重启/迁移开发服务的持久数据库，未运行完整前端浏览器套件（已运行本任务及相关视觉回归）；无需新依赖或 schema migration。生产服务加载最新代码后，由既有 upgrade_world 自动补齐旧档。
