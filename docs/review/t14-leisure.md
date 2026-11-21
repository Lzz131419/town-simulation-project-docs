# T14 居民主动生活验收记录

已在共享未提交工作树上实现；未回滚、未提交，未更改数据库 schema，未添加依赖或图片/音频资源。

## 实现与地点

| 行为 | place / 实际目的地 | 效果 |
| --- | --- | --- |
| stroll | `meadow` 南岸营地，沿现有路径行走 | energy -2，无产出；「在河边散步」 |
| visit | catalog `home`；运行时使用目标的 `owned_home` 对应门口 | 熟悉度至少40且有住宅；主人清醒在家才坐下，双方关系+4、分别记忆；不在家/睡眠则改道 `plaza`，无关系奖励 |
| daydream | `fishery` 钓鱼台（地图无 `riverside`，复用现成河岸地点） | 基础能耗0，恢复2点；「看着河水发呆」 |
| play | `plaza` 邻里广场 | 80像素欧式距离内清醒居民（含发起者）至少2人，所有参与者两两关系+2、hunger+3；独自返还1点精力；基础耗能3 |
| shop_browse | `market` 河畔集市 | energy -2，不购买；有库存且买价低于base时记忆「看到X最近便宜」，topic=`market_price` |

精力结算沿用T12疲劳附加成本与精力上限。串门本身基础能耗0；主人在途中离家也会重新寻路到广场，抵达后才结算。每个生活动作到达后停留2 tick（可配），前端可见动作而不是单tick闪过。

## 决策、事件与摘要

- `balance.leisure` / `game.json`：默认40%概率，勤奋乘0.5；wake后1小时（当前06:00–07:00）、15:00–17:00、19:00–21:00，排除社交时段与个体睡眠时间。当前已有social为12:00–14:00，sociable延长到15:00，保留原配置。
- 饥饿、低精力、睡眠和紧急防洪/升级继续优先；先计算个性override，生活抽签命中时可替代普通生产/出售/捐建override，避免勤奋和商人永远没有生活；未命中完全回到旧fallback。
- 随机数使用世界seed、tick、居民id派生的稳定本地Random，读取不消耗天气随机流；保存恢复可重放；无需新增持久化schema。
- 事件统一 `type="leisure"`、`details.kind`；无钱物、交易数或XP变化。`emit` 的形参改为 `event_type`，允许详情使用 `kind`。经济报表显式跳过leisure，测试用带amount/outputs的leisure事件证明不计交易与产出。
- T7b离线玩家同样走生活分支。回归摘要预留一项最常做的生活，例如「你去河边散了步」；串门落空另写「你串门时邻居不在，去广场坐了坐」，不会谎报成功到访。
- activity通过原world API投影传递，后端API断言及真实Phaser测试均验证。stroll复用行走、visit在门口静止、play复用T4两姿态小跳；daydream静止并偶尔显示「…」气泡。气泡已实现，减少动态模式下保留静态气泡、禁用跳动。

## 测试证据

命令：`cd backend && ../.venv/bin/python -m pytest tests -x -q`

```text
........................................................................ [ 16%]
........................................................................ [ 33%]
........................................................................ [ 50%]
........................................................................ [ 67%]
........................................................................ [ 84%]
.................................................................        [100%]
425 passed in 19.12s
```

基线390，新增 `backend/tests/test_leisure.py` 35项。覆盖五种动作、串门关系/记忆与途中改道、玩耍范围边界/睡眠排除/全员关系、精力上限、个性权重与勤奋概率、时间/睡眠/工作窗口、经济API、离线托管摘要、活动API投影、三天模拟与JSON恢复重放。

命令：仓库根 `npm run build`

```text
> mist-river-town@2.0.0 build
> npm --prefix frontend run build


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
dist/assets/TownScene-Dn6a3qQ7.js     45.94 kB │ gzip:  18.51 kB
dist/assets/index-B7AjtjYv.js        218.54 kB │ gzip:  78.35 kB
dist/assets/phaser-Czz4FBZH.js     1,481.77 kB │ gzip: 339.84 kB
✓ built in 3.03s
```

命令：`cd frontend && ./node_modules/.bin/playwright test tests/visual-effects.spec.ts`

```text
✓ leisure shows activity, two play hops and occasional daydream thoughts
✓ reduced motion keeps leisure static and thought readable
10 passed (11.8s)
```

既有8项视觉测试也通过。使用现有该仓库的5173 Vite服务与隔离Phaser fixture；没有修改在线存档。修改的Python文件ruff检查通过，`git diff --check`通过。

## 三天自然模拟

原样 `initial_world()`，默认seed=42，连续432次 `tick_world`（3×144），没有传送、注入关系、认领住宅或强制概率；每tick不变量通过。

| 居民 / 个性 | 散步 | 串门 | 发呆 | 玩耍 | 逛集市 | 合计 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 林溪 / introvert | 0 | 0 | 1 | 0 | 0 | 1 |
| 陈禾 / diligent | 1 | 0 | 0 | 0 | 0 | 1 |
| 周木 / merchant | 1 | 0 | 0 | 0 | 3 | 4 |
| 许宁 / generous | 0 | 0 | 0 | 3 | 0 | 3 |
| 苏晴 / sociable | 0 | 0 | 0 | 1 | 2 | 3 |
| 陆川 / quiet | 0 | 0 | 2 | 0 | 1 | 3 |

林溪独处、周木以逛集市为主、许宁以玩耍为主、陆川以发呆为主；陈禾只发生一次生活行为。短窗口样本不足以统计证明每个人偏好（例如苏晴3次中2次闲逛），且这次自然模拟没有成功串门，不能把单元测试当成自然模拟发生过串门。成功串门/落空/途中主人离开由定向真实动作链测试验证。

补充固定随机数偏好检验：每个性3000次15:00决策，Random(1414)，只为这项控制实验设置一个熟悉度40且有住宅的可访问邻居；不属于自然三天模拟。

| 个性 | 生活命中 | 独处：散步+发呆 | 社交：串门+玩耍 | 逛集市 |
| --- | ---: | ---: | ---: | ---: |
| introvert | 1194 | 966 | 133 | 95 |
| diligent | 622 | 362 | 168 | 92 |
| merchant | 1206 | 172 | 171 | 863 |
| generous | 1198 | 156 | 954 | 88 |
| sociable | 1198 | 156 | 954 | 88 |
| quiet | 1171 | 981 | 124 | 66 |

原始事件、完整计数和实验条件见 [t14-leisure-events.json](t14-leisure-events.json)。

复现自然模拟：

```sh
cd backend
../.venv/bin/python - <<'PYCODE'
from collections import Counter
from app.catalog import initial_world
from app.domain.scheduler import tick_world
w, events = initial_world(), []
for _ in range(432):
    tick_world(w, events)
for a in w['agents'].values():
    if a['npc']:
        print(a['name'], a['personality'], Counter(
            e['details']['kind'] for e in events
            if e['actor_id'] == a['id'] and e['type'] == 'leisure'))
PYCODE
```

## 变更边界与git差异

T14触及已有文件：`backend/app/{balance.py,catalog.py,api/world.py,domain/actions.py,domain/rules.py,domain/scheduler.py,services/proxy_life.py}`、`backend/config/game.json`、`frontend/src/game/{ResidentLayer.ts,visual-state.ts}`、`frontend/tests/{visual-effects.spec.ts,fixtures/visuals.ts}`。新增 `backend/app/domain/leisure.py`、`backend/tests/test_leisure.py` 和本次 `docs/review/t14-*` 证据。

以下是要求的完整 `git diff --stat`，包含先前T1–T13共享未提交改动，不能全部算作T14；git diff本身不计未跟踪文件（如既有proxy_life/visual-state及本次leisure模块、测试、证据）：

```text
backend/app/api/auth.py                          |  21 +-
 backend/app/api/realtime.py                      |   8 +-
 backend/app/api/world.py                         | 125 ++++++--
 backend/app/balance.py                           | 161 ++++++++++
 backend/app/catalog.py                           |  37 +++
 backend/app/domain/actions.py                    | 287 ++++++++++++++----
 backend/app/domain/deliveries.py                 |  27 +-
 backend/app/domain/economy.py                    |  39 +++
 backend/app/domain/migration.py                  |  50 +++-
 backend/app/domain/orders.py                     |  65 ++++-
 backend/app/domain/plans.py                      |   2 +-
 backend/app/domain/progression.py                |  11 +-
 backend/app/domain/rules.py                      |  21 +-
 backend/app/domain/scheduler.py                  | 356 ++++++++++++++++++++---
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
 frontend/src/components/TownInspector.vue        | 120 +++++++-
 frontend/src/components/TownMap.vue              |  32 +-
 frontend/src/components/charts/ResourceChart.vue |   4 +-
 frontend/src/components/dialogs/PlaceDialog.vue  |   4 +-
 frontend/src/components/dialogs/ReturnDialog.vue |  14 +-
 frontend/src/components/layout/ShellHeader.vue   |  15 +-
 frontend/src/composables/useReports.ts           |  13 +-
 frontend/src/game/Atmosphere.ts                  | 177 ++++++++++-
 frontend/src/game/ResidentLayer.ts               |  87 +++++-
 frontend/src/game/TownScene.ts                   |  52 +++-
 frontend/src/game/art/map.ts                     |   5 +-
 frontend/src/game/art/vegetation.ts              |  39 ++-
 frontend/src/game/scene-types.ts                 |   5 +-
 frontend/src/realtime/protocol.ts                |  55 +++-
 frontend/src/stores/town.ts                      |  51 +++-
 frontend/src/styles/game-ui.css                  |  33 +++
 frontend/src/styles/reports.css                  |  29 ++
 frontend/src/types.ts                            |  51 +++-
 frontend/src/views/MarketView.vue                | 123 +++++++-
 frontend/src/views/ProjectView.vue               |   4 +-
 frontend/src/views/TownView.vue                  |  12 +
 frontend/tests/browser.spec.ts                   |   2 +-
 frontend/tests/districts.spec.ts                 |   2 +-
 frontend/tests/journey.spec.ts                   |   2 +-
 frontend/tests/lighting.spec.ts                  |   2 +-
 frontend/tests/map.spec.ts                       |  24 +-
 frontend/tests/queue.spec.ts                     |   2 +-
 frontend/tests/reliability.spec.ts               |  20 +-
 57 files changed, 2178 insertions(+), 316 deletions(-)
```
