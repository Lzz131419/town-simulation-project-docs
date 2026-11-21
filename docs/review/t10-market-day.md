# T10 集市日实现与验收

在已验收但未提交的共享改动之上完成，未回滚、未暂存、未提交。没有新增依赖、图像或音频资源、数据库 schema。

## 实现与现状调查

- `actions.py` 的 buy/sell 和 `orders.py` 的托管结算均未收交易税/手续费；`economy.collect_daily_levy` 是每日盈余维护金，不是交易税，保持现有规则。按任务替代方案，集市日卖出报价 ×1.1，沿用四舍五入整数报价，并保留 sell < buy；低价商品会因整数取整不变，变质品仍按固定 1 镇币回收。
- `progression.record_progress` 的实际字段是 `progress.xp`、`progress.metrics`、`progress.badges`。集市日动作 XP、metric 增量以及首次解锁里程碑的 20 XP 均 ×2；徽章仍只发一次。公共交付调用 `supply`（正常 10 XP），私人订单调用 `delivery`（正常 12 XP）。成长指标是任务进度，生产事件与真实物资数量不虚增。
- 新增 `balance.market_day`：周期 7 天、持续 144 tick、卖价 1.1、公共奖励 2、成长 2、广场半径 80、关系额外 +2，以及预告/开场文案。预告保留任务指定的「交易免税」原文，开场明确说明本镇无交易税，实际采用卖价奖励。
- 按任务明确的 `day = tick // 144`，在现有 `(tick + 48) % 144 == 0` 日界触发：第 6 天 tick 960 预告，第 7 天 tick 1104 开场，至 tick 1248 前生效，第 8 天日界清理。第 0 天不触发，14、21 天重复。这个编号与已有 UI `gameTime` 的显示日期不同，未改变原日历。
- `w.market_day={until_tick}` 进入初始世界与幂等 `upgrade_world`；过期判断无需等待清理，旧档缺字段视为非集市日。集市处理不增加 RNG 抽取，fortune 使用原黎明 roll，在集市日剔除 caravan 后按剩余 75 权重抽卡。
- 公共交付先检查完整双倍国库预算，实际转账、earned、文本、事件 amount/unit_price 一致；私人/公开玩家订单仍只付 escrow 原额。社交双方均在广场欧氏距离 ≤80 内时，两方向关系额外 +2、上限 100。
- 统一 emit 为当日事件加 `details.market_day=true`。顺便修正 sell 事件原先在库存变化后重新报价的问题，事件 unit_price 现在记录实际成交前报价。
- 前端实时协议允许并验证 market_day；地图白昼/夜晚行显示集市日 chip；广场四个不同颜色条纹棚与木桌使用 Phaser Graphics，不抢交互、不重绘底图、不新增纹理。装饰全天显示，次日日界消失，关闭动态环境仍保留活动装饰。
- 公共交付面板显示双倍酬劳，并按双倍金额判断国库预算；倍数读取 catalog.rules.market_day。
- WebAudio 增加 430Hz 低通噪声层（0.018 gain），白天 06:00–19:00 才开启，每约 6.8 秒允许一声轻叮；复用 T9 懒解锁、音量、声音/环境/动态开关、后台暂停、ramp 和 dispose 机制。没有进行真人听感验收。

## 报表边界

未新增集市专用聚合。已有经济报表会按实际金额计入集市 buy/sell/filled order；源码目前并不把公共 `delivery` 纳入 trade_amount（只有 buy/sell/trade/filled order），所以不能声称公共交付金额已经进入这个周转额字段。公共交付双倍 amount/unit_price 和 market_day 标记已保存于正常事件，供后续按需要筛选；本次遵守“不另做”聚合的约束，没有改变已有报表口径。

## 事件证据

完整真实领域执行样例含 before/after 快照：`docs/review/t10-market-day-events.json`。使用 initial_world、tick_world 和 execute 生成，并通过 check_invariants；不是手写事件。

```json
[
  {
    "tick": 960,
    "actor_id": "town",
    "type": "fortune",
    "text": "明日是集市日：交易免税，交付酬劳加倍，广场将摆出集市摊位",
    "details": {
      "card": "market_day_preview",
      "day": 6
    }
  },
  {
    "tick": 1104,
    "actor_id": "town",
    "type": "fortune",
    "text": "集市日开场！本镇无交易税，今日卖价上浮10%，公共交付酬劳与成长加倍，欢迎来广场赶集",
    "details": {
      "card": "market_day",
      "day": 7,
      "until_tick": 1248,
      "market_day": true
    }
  },
  {
    "tick": 1104,
    "actor_id": "wangjue",
    "type": "delivery",
    "text": "王崛完成「街坊早餐」，获得24镇币",
    "details": {
      "amount": 24,
      "item": "bread",
      "quantity": 3,
      "unit_price": 8.0,
      "market_day": true
    }
  }
]
```

## 浏览器回归隔离与复现

原浏览器套件默认连长期运行的 5173/8000，共享玩家、背包、离线代理与天气，会让后续社交目标移动、生产链缺料。第一次全量尝试在既有服务失败后中止；改用独立 5174/8010 与 `.local/t10/e2e.db`，仍发现用例间代理生活造成污染，因此增加可选 per-test 重置夹具。先前怀疑库存格式，进一步检查确认 bread/grain 仍是整数，未修改这些断言。

- `backend/tests/browser_server.py` 只在显式导入这个测试模块时注册 reset 接口，要求 `TOWN_E2E_RESET_WORLD=1` 以及绝对路径、名为 e2e.db 的 SQLite 文件；正常 `app.main:app` 没有此接口。重置持有 runtime.lock，采用 initial_world、固定首个天气种子、NPC manual；不改生产 balance 参数，不更改业务断言。
- `frontend/tests/fixtures/live-test.ts` 仅在上述环境变量开启时发 reset 请求；七份既有集成测试仅改 test 导入，报表用例额外等待 scheduler 生成至少两个真实样本，并显式选择 treasury 指标；T7 已将默认指标改成 daily turnover，旧测试却仍按 treasury 断言。样本通过原 sample_world 写入，没有假造图表数据；报表截图移到 test-results，避免覆盖既有文档截图。
- `frontend/tests/fixtures/vite.config.ts` 是独立测试端口与代理配置。T4/T9 使用的隔离浏览器 fixture 保留，仅新增集市断言，没有更新或放宽既有视觉断言。

三个终端，从以下各自目录执行即可复现（数据库路径可替换为另一个专用绝对路径，文件名须 e2e.db）：

```sh
# backend/
mkdir -p ../.local/t10
TOWN_E2E_RESET_WORLD=1 TOWN_DATABASE_URL="sqlite:///$(cd .. && pwd)/.local/t10/e2e.db" TOWN_TICK_SECONDS=0.15 ../.venv/bin/python -m uvicorn tests.browser_server:app --host 127.0.0.1 --port 8010

# frontend/
npx vite --config tests/fixtures/vite.config.ts

# frontend/
TOWN_E2E_RESET_WORLD=1 TOWN_E2E_BASE_URL=http://127.0.0.1:5174 npx playwright test
```

后端完整验收：`cd backend && ../.venv/bin/python -m pytest tests -x -q`；前端构建：`cd frontend && npm run build`。测试日志保存在 `.local/t10/`，均为本次运行的真实输出。

## 后端与构建证据

```text
........................................................................ [ 20%]
........................................................................ [ 40%]
........................................................................ [ 61%]
........................................................................ [ 81%]
................................................................         [100%]
352 passed in 30.26s
```

```text
> mist-river-town-client@2.0.0 build
> vue-tsc -b && vite build

vite v6.4.6 building for production...
transforming...
✓ 1664 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                        0.48 kB │ gzip:   0.35 kB
dist/assets/index-DrZqD_bQ.css        51.63 kB │ gzip:  10.87 kB
dist/assets/phaser-CkuN5Vkn.js         0.47 kB │ gzip:   0.34 kB
dist/assets/TownScene-DgZCRgts.js     41.45 kB │ gzip:  16.93 kB
dist/assets/index-DjJ6lVDI.js        215.50 kB │ gzip:  77.30 kB
dist/assets/phaser-Czz4FBZH.js     1,481.77 kB │ gzip: 339.84 kB
✓ built in 3.26s
```

新增 `backend/tests/test_market_day.py` 15 项用例：连续 tick 运行八个日界、6 天预告/7 天开场/8 天恢复、14/21 天重复、第 0 天不触发、144 tick 有效期、卖价与实际转账/事件报价、买卖价差、公共交付 24 镇币及 XP、双倍预算不足原子性、成长/里程碑、社交半径/双向/上限、商队剔除后的完整权重分布、私人和公开 escrow 不翻倍、旧档升级幂等。涉及资产操作均核验 check_invariants。

`git diff --check` 与本次前端变更的 Prettier 检查通过。

## git diff --stat

以下是整个共享工作树相对 HEAD 的真实输出，包含 T1–T9 已存在改动，不能全部归属 T10；未跟踪的新文件不在普通 diff stat 中。

```text
backend/app/api/auth.py                          |  21 ++-
 backend/app/api/realtime.py                      |   8 +-
 backend/app/api/world.py                         | 121 +++++++++---
 backend/app/balance.py                           | 102 +++++++++++
 backend/app/catalog.py                           |  23 +++
 backend/app/domain/actions.py                    | 202 ++++++++++++++++-----
 backend/app/domain/deliveries.py                 |  27 ++-
 backend/app/domain/economy.py                    |  39 ++++
 backend/app/domain/migration.py                  |  33 +++-
 backend/app/domain/orders.py                     |  65 ++++++-
 backend/app/domain/progression.py                |  11 +-
 backend/app/domain/rules.py                      |   8 +-
 backend/app/domain/scheduler.py                  | 222 ++++++++++++++++++++---
 backend/app/pathfinding.py                       |  17 +-
 backend/app/realtime/protocol.py                 |   6 +
 backend/app/runtime.py                           |  59 ++++--
 backend/app/services/history.py                  |  19 +-
 backend/tests/test_districts.py                  |   7 +-
 backend/tests/test_map_expansion.py              |  11 +-
 backend/tests/test_plan_queue.py                 |  10 +-
 backend/tests/test_reliability.py                |   1 +
 backend/tests/test_world.py                      |   3 +-
 frontend/src/components/DeliveryBoard.vue        |  21 ++-
 frontend/src/components/EventDetails.vue         |   8 +-
 frontend/src/components/RecipeBook.vue           |  12 +-
 frontend/src/components/ReportDashboard.vue      |  60 +++++-
 frontend/src/components/TownInspector.vue        |  74 ++++++--
 frontend/src/components/TownMap.vue              |  32 +++-
 frontend/src/components/charts/ResourceChart.vue |   4 +-
 frontend/src/components/dialogs/PlaceDialog.vue  |   4 +-
 frontend/src/components/dialogs/ReturnDialog.vue |  14 +-
 frontend/src/composables/useReports.ts           |  13 +-
 frontend/src/game/Atmosphere.ts                  | 136 +++++++++++++-
 frontend/src/game/ResidentLayer.ts               |  23 ++-
 frontend/src/game/TownScene.ts                   |  47 ++++-
 frontend/src/game/art/map.ts                     |   5 +-
 frontend/src/game/art/vegetation.ts              |  39 +++-
 frontend/src/game/scene-types.ts                 |   5 +-
 frontend/src/realtime/protocol.ts                |  24 ++-
 frontend/src/stores/town.ts                      |  51 +++++-
 frontend/src/styles/game-ui.css                  |  15 ++
 frontend/src/styles/reports.css                  |  29 +++
 frontend/src/types.ts                            |  21 ++-
 frontend/src/views/MarketView.vue                | 123 ++++++++++++-
 frontend/tests/browser.spec.ts                   |   2 +-
 frontend/tests/districts.spec.ts                 |   2 +-
 frontend/tests/journey.spec.ts                   |   2 +-
 frontend/tests/lighting.spec.ts                  |   2 +-
 frontend/tests/map.spec.ts                       |  24 ++-
 frontend/tests/queue.spec.ts                     |   2 +-
 frontend/tests/reliability.spec.ts               |  20 +-
 51 files changed, 1569 insertions(+), 260 deletions(-)
```

T10 新增文件：

- backend/app/domain/market_day.py
- backend/tests/test_market_day.py
- backend/tests/browser_server.py
- frontend/src/game/market-day.ts
- frontend/src/game/art/market-day.ts
- frontend/tests/fixtures/live-test.ts
- frontend/tests/fixtures/vite.config.ts
- docs/review/t10-market-day-events.json
- docs/review/t10-market-day.md

其余 T10 增量修改：后端 balance/catalog/actions/deliveries/economy/fortune/migration/progression/rules/scheduler；前端 types、realtime/protocol、TownMap、DeliveryBoard、Atmosphere、audio、game-ui.css；audio/visual-effects 测试与 visuals fixture；七份既有浏览器用例的可选隔离 fixture 导入与上述报表用例修正。

## 最终浏览器结果与截图

```text
  ✓  28 tests/queue.spec.ts:28:1 › queue recipes, reorder and remove steps, finish a real chain and stop (8.6s)
  ✓  29 tests/queue.spec.ts:84:1 › failed finite step pauses later work and stale drafts cannot replace new queues (4.0s)
  ✓  30 tests/reliability.spec.ts:18:1 › patch validates continuity and schema without damaging current state (42ms)
  ✓  31 tests/reliability.spec.ts:81:1 › request timeout covers response body and never retries mutations (28ms)
  ✓  32 tests/reliability.spec.ts:111:1 › startup failure and stalled server offer a working retry (12.8s)
  ✓  33 tests/reliability.spec.ts:136:1 › broken websocket reconnects and resyncs after a malformed packet (2.0s)
  ✓  34 tests/reliability.spec.ts:171:1 › economic charts show real samples at both desktop sizes (1.5s)
  ✓  35 tests/visual-effects.spec.ts:19:1 › weather applies on construction, switches layers, and respects ambience (1.2s)
  ✓  36 tests/visual-effects.spec.ts:54:1 › season palettes restore exactly and snow stays on a separate roof layer (1.4s)
  ✓  37 tests/visual-effects.spec.ts:73:1 › work poses run only when both server path and interpolation have stopped (1.9s)
  ✓  38 tests/visual-effects.spec.ts:104:1 › reduced motion freezes precipitation and disables work movement (985ms)
  ✓  39 tests/visual-effects.spec.ts:122:1 › all requested task aliases have two poses; unsupported tasks stay still (2ms)
  ✓  40 tests/visual-effects.spec.ts:138:1 › market day props appear immediately, last all day, and expire without rebaking (1.4s)

  40 passed (2.1m)
```

最终完整运行 **40 passed (2.1m)**，其中 T9 audio 全部 15 项（原 13 + 集市 2）、T4 visual-effects 全部 6 项（原 5 + 集市 1）通过。原断言未被删减，报表旧默认指标测试已纠正，并保留实际样本与数值校验。

集市装饰截图：`frontend/test-results/t10-market-day-stalls.png`，1100 × 760；备份 `.local/t10/screenshots/t10-market-day-stalls.png`。**已使用图像查看工具实际查看最终截图**：四个不同颜色条纹棚沿广场南侧步道排列，喷泉/长椅/邻近房屋可见，摊位不覆盖房屋；首版覆盖南侧房屋的问题已修正后重跑全套。截图由真实 Phaser Canvas 的 T4 fixture 渲染生成，不是手绘 mockup；当前是夏季晴天、集市日白天的受控世界快照。

最终构建 `vue-tsc -b && vite build` 成功；后端最终全量 **352 passed in 30.26s**；`git diff --check` 和所改前端文件 Prettier 检查通过。本次独立 5174/8010 服务在验收后关闭，原 5173/8000 服务未重启或改配置；第一次未隔离的浏览器执行曾触发测试账户的正常动作，后续完整验收都使用专用数据库。

无实现遗留、无 commit。保留两项事实边界：音效节点/路由/生命周期已自动化验证但未作真人试听；原报表公共 delivery 不计入 trade_amount，已保留原口径并完整记录双倍事件金额。
