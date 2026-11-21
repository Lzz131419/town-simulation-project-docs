# T7a 声望与头衔完成证据

在共享 W1+W2 未提交改动之上完成，没有回滚、提交 commit 或修改数据库 schema。新增 26 项后端测试；前端仅改 Resident 类型与 TownInspector 名称展示（主标题和伙伴列表）。

## 验证

执行 `cd backend && ../.venv/bin/python -m pytest tests -x -q`，完整日志 `.local/t7a-evidence/pytest.log`：

```text
........................................................................ [ 22%]
........................................................................ [ 45%]
........................................................................ [ 67%]
........................................................................ [ 90%]
................................                                         [100%]
320 passed in 14.94s
```

执行 `cd frontend && npm run build`，完整日志 `.local/t7a-evidence/build.log`：

```text
> mist-river-town-client@2.0.0 build
> vue-tsc -b && vite build

vite v6.4.6 building for production...
transforming...
✓ 1661 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                        0.48 kB │ gzip:   0.35 kB
dist/assets/index--1pBi-2w.css        50.98 kB │ gzip:  10.73 kB
dist/assets/phaser-CkuN5Vkn.js         0.47 kB │ gzip:   0.34 kB
dist/assets/TownScene-DQZtBk0U.js     41.01 kB │ gzip:  16.80 kB
dist/assets/index-O6BNqrLy.js        203.24 kB │ gzip:  73.16 kB
dist/assets/phaser-Czz4FBZH.js     1,481.77 kB │ gzip: 339.84 kB
✓ built in 3.16s
```

`git diff --check` 通过。前端完成编译验证，未运行浏览器视觉验收。

## 实现位置

- 所有玩家/NPC 初始值：`backend/app/catalog.py:145`。
- 旧存档增量迁移、保留已有分数和当日预算：`backend/app/domain/migration.py:25`。
- 全部声望数值、每日上限、头衔阈值、折扣门槛与倍率配置：`backend/app/balance.py:103`。
- 交付成功 +2：`backend/app/domain/deliveries.py:43`；调用方传入事件列表。
- 统一赠礼成功 +5，仅赠送方一次（玩家、NPC 策略、主动赠礼共用）：`backend/app/domain/actions.py:223`。
- 私人订单成交 seller +3，公开订单无声望奖励：`backend/app/domain/orders.py:89`。
- 私人订单过期 buyer -3，公开订单过期不罚：`backend/app/domain/scheduler.py:261`。
- 每日累计绝对变动量上限 10、截断剩余分值、每次实际变化 emit reputation(delta/reason/total)：`backend/app/domain/reputation.py:14`。
- 黎明先重置全员每日预算，再处理订单到期，防止到期扣分在同一 tick 被清空：`backend/app/domain/scheduler.py:251`；辅助按日惰性重置 `backend/app/domain/reputation.py:7` 支持直接调用/恢复存档。
- 头衔只按当前最高档分数计算，可随扣分降级：`backend/app/domain/reputation.py:29`。
- HTTP 世界与 WebSocket 公共投影：`backend/app/realtime/protocol.py:15`；报告 me/ranking：`backend/app/api/world.py:139`、`:146`。
- Inspector 名字前缀：`frontend/src/components/TownInspector.vue:88`、`:204`；Resident 可选字段：`frontend/src/types.ts:39`。
- 买入实际单价：`backend/app/domain/actions.py:18`，买入事件 details 的 discount 为本单总节省镇币，另含 quoted_unit_price 和 unit_price：`:172`。
- 自动买面包预算也使用折后价：`backend/app/domain/scheduler.py:46`。
- 新增测试：`backend/tests/test_reputation.py`。

## 折扣顺序与边界

price(w,item,side) 签名不变，保持纯函数。库存动态价先按原规则 floor(x+0.5) 四舍五入；有效 market_modifiers 再乘倍率并 floor(x+0.5)；声望 >=50 时在 actions.buy_price 将该单价乘 0.95 并 floor 向下取整，最后受 ceil(0.5×基础买价)、floor(1.8×基础买价) 和同一成交前库存快照 sell+1 约束；最终单价再乘购买数量。

例：cloth 库存 8 时原价 9，声望49买价9、声望50买价8；商队0.8时先得到7，再声望折扣得到6，购买2件节省2镇币。低价物品可能被价差或下限约束而没有实际优惠，discount=0。买卖报价比较使用同一个成交前库存快照，成交改变库存后下一笔报价可以变化。

补齐 `backend/app/domain/economy.py:34` 的事件折扣包络：原先商队叠加高库存时 cloth 可从5折成4，低于基础买价9的整数下限5，导致后续声望折扣钳制到5反而涨价；现在事件后的买卖价同样遵循原基础价包络，声望不会造成加价。现有事件和定价测试全绿，新增测试覆盖全部可买物品、5档库存、无事件/0.8事件、纯函数和资金库存不变量。

每日上限是正负共用的累计绝对值，而非净变化：例如 +5 后只能再 -5，当天预算耗尽不再产生零变化声望事件。声望允许负数，未设未要求的零下限。

## 从0获得头衔的真实领域执行样例

原始输出：`.local/t7a-evidence/sequence.json`，用 initial_world、execute、逐 tick tick_world、personalize 运行，不直接赋高分。

| actor | tick | reason | delta | total | 当前头衔 |
|---|---:|---|---:|---:|---|
| npc-1 林溪 | 0 | gift | +5 | 5 | 无 |
| npc-1 林溪 | 0 | gift | +5 | 10 | 无 |
| npc-1 林溪 | 96 | gift | +5 | 15 | 无 |
| npc-1 林溪 | 96 | gift | +5 | 20 | 可靠的 |
| npc-1 林溪 | 240 | delivery | +2 | 22 | 可靠的 |

最终投影为「可靠的 林溪」，存档 agent 无 title 字段，check_invariants 通过。tick96/240 沿用当前系统 is_dawn 的日界线。

## git diff --stat

下列为共享工作树当前完整输出，包含原有 W1+W2 改动，不能当作 T7a 独占 diff；git diff --stat 本身不显示未跟踪文件，本任务另新增 `backend/app/domain/reputation.py`、`backend/tests/test_reputation.py` 及本报告。

```text
 backend/app/api/world.py                         |  10 +-
 backend/app/balance.py                           |  89 ++++++++++
 backend/app/catalog.py                           |  22 +++
 backend/app/domain/actions.py                    | 165 +++++++++++++-----
 backend/app/domain/deliveries.py                 |  10 +-
 backend/app/domain/economy.py                    |  36 ++++
 backend/app/domain/migration.py                  |  32 +++-
 backend/app/domain/orders.py                     |  42 ++++-
 backend/app/domain/rules.py                      |   5 +-
 backend/app/domain/scheduler.py                  | 206 ++++++++++++++++++++---
 backend/app/pathfinding.py                       |  17 +-
 backend/app/realtime/protocol.py                 |   6 +
 backend/app/services/history.py                  |   6 +-
 backend/tests/test_districts.py                  |   7 +-
 backend/tests/test_map_expansion.py              |  11 +-
 backend/tests/test_reliability.py                |   1 +
 backend/tests/test_world.py                      |   3 +-
 frontend/src/components/DeliveryBoard.vue        |   8 +-
 frontend/src/components/EventDetails.vue         |   8 +-
 frontend/src/components/RecipeBook.vue           |  12 +-
 frontend/src/components/TownInspector.vue        |  74 ++++++--
 frontend/src/components/charts/ResourceChart.vue |   4 +-
 frontend/src/components/dialogs/PlaceDialog.vue  |   4 +-
 frontend/src/game/Atmosphere.ts                  | 131 +++++++++++++-
 frontend/src/game/ResidentLayer.ts               |  23 ++-
 frontend/src/game/TownScene.ts                   |  47 +++++-
 frontend/src/game/art/map.ts                     |   5 +-
 frontend/src/game/art/vegetation.ts              |  39 ++++-
 frontend/src/game/scene-types.ts                 |   5 +-
 frontend/src/realtime/protocol.ts                |  19 ++-
 frontend/src/stores/town.ts                      |   6 +-
 frontend/src/types.ts                            |  17 +-
 frontend/src/views/MarketView.vue                | 123 +++++++++++++-
 frontend/tests/map.spec.ts                       |  22 ++-
 34 files changed, 1049 insertions(+), 166 deletions(-)

```

T7a 修改文件：backend/app/balance.py、catalog.py、domain/{actions,deliveries,economy,migration,orders,scheduler}.py、realtime/protocol.py、api/world.py、frontend/src/types.ts、frontend/src/components/TownInspector.vue；新增文件如上。所有授权实现和指定验证均完成，无剩余阻塞。
