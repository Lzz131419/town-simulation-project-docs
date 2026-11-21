# T5 后端实现与验证证据

已在共享未提交工作树上完成每日五种事件、桥封闭、NPC 私人订单、赠送和广场聚餐；没有提交 commit，没有修改前端或数据库 schema。

## 验证

执行：`cd backend && ../.venv/bin/python -m pytest tests -x -q`

```text
........................................................................ [ 24%]
........................................................................ [ 48%]
........................................................................ [ 73%]
........................................................................ [ 97%]
......                                                                   [100%]
294 passed in 14.51s
```

T5 新增 `backend/tests/test_events.py` 共 33 项参数化测试，单独运行结果 `33 passed in 0.37s`；修改涉及的后端文件通过 Ruff，`git diff --check` 通过。
当前总数包含 W1 和共享工作树中并行加入的食物新鲜度测试，并非只在原始 229 项上增加 T5。

## 关键断言行号

以下均为 `backend/tests/test_events.py`：

- 43–65：五个固定种子在真实日界触发卡池，验证 emit、市场/蜂蜜/桥/纠纷效果。
- 77–86：seed=42 六黎明序列、JSON 保存恢复后的世界和事件一致。
- 97–104：纠纷关系下限 0，双方后续闲聊优先引用纠纷。
- 112–125：封桥同岸可达、跨岸 route/start_action 抛明确错误且无副作用、到期恢复。
- 135–139：封桥阻止已经开始的跨河行程，每次封闭仅提示一次，到期继续移动。
- 149–156：价格纯函数按 0.8 折扣与次日清理；165–169 验证过期修饰自然失效。
- 176–189：关系门槛 60、定向字段、托管扣款、总报酬取整到 7、双方记忆与 order 文案。
- 198–204：6 小时冷却与同物订单去重；222–225：贫穷/重复/容量不足跳过。
- 236–239：snapshot 与 delta 按 uid 过滤私人订单，源世界不被改变。
- 248–256、270–273：未受邀者无法交付，受邀者领取准确托管金额，取消/过期退款，资金守恒。
- 283–302：关系门槛 80、最低卖价食物、批次新鲜度保留、双方记忆、1 天冷却。
- 340–361：18 点聚餐、关系总和最高 NPC 发起、饥饿下限/关系上限、双向加成、每日一次。
- 366–377：时间/人数/范围/NPC 主持条件；386–389：tick_world 实际调度。
- 401–409：旧存档增量补字段、幂等且不覆盖已有状态。
- 422–431：真实 API 列表定向可见，其他玩家交付请求返回 400。

## 实现选择与兼容说明

- 每个黎明只推进一次已有 LCG，将同一个 draw 用于天气与事件；因此保留 T1 已有固定种子天气序列与全部测试，卡池和天气使用同一随机样本（不是相互独立的两次抽样）。纠纷双方从该事件区间内的余数选取，不额外推进随机状态。
- `price(w,item,side)` 签名与纯函数属性保留；折扣应用于动态报价后，仍保证整数价格、最低 1 及买卖价差。
- 私人订单报酬按 `int(sell_price * quantity * 1.2)` 对总额一次取整；为使原有前端 `quantity * unit_price` 正确显示，该类订单单价可为小数（例：2 份每份 3.5，总托管 7），实际现金和托管始终为整数。
- 订单列表通过现有 `personalize` 同时覆盖 HTTP 与 WebSocket snapshot/delta；`fill_order` 另有定向授权校验。公开新闻和居民记忆仍沿用原有共享展示。
- 同岸 A* 不经过封闭河面，跨岸无替代道路时抛 `河水上涨，桥暂时无法通行`；既有跨河行程等待到期恢复。
- NPC 主动邀请每 6 tick 检查一次，订单至少隔 36 tick，赠礼至少隔 144 tick；普通调度允许 NPC 空闲时发起，赠礼复用 T2 gift 并保留共享新鲜度批次。
- 聚餐窗口为 18:00–19:00，半径按欧氏距离 100，所有在场居民参与；主持人在在场 NPC 中按对全镇其他居民的关系总和选择。

## 固定 seed=42 的六个黎明

```json
[
  {
    "tick": 96,
    "type": "fortune",
    "text": "河面涨水，桥暂时封闭，请等待水位回落",
    "details": {
      "card": "flood",
      "bridge_closed_until": 120
    }
  },
  {
    "tick": 240,
    "type": "fortune",
    "text": "河面涨水，桥暂时封闭，请等待水位回落",
    "details": {
      "card": "flood",
      "bridge_closed_until": 264
    }
  },
  {
    "tick": 384,
    "type": "fortune",
    "text": "河面涨水，桥暂时封闭，请等待水位回落",
    "details": {
      "card": "flood",
      "bridge_closed_until": 408
    }
  },
  {
    "tick": 528,
    "type": "fortune",
    "text": "邻里纠纷：许宁与陆川闹了些不愉快",
    "details": {
      "card": "dispute",
      "participants": [
        "npc-4",
        "npc-6"
      ]
    }
  },
  {
    "tick": 672,
    "type": "fortune",
    "text": "蜂群分家，今日采集蜂蜜收获增加",
    "details": {
      "card": "bees"
    }
  },
  {
    "tick": 816,
    "type": "fortune",
    "text": "商队来访，今日市场工具和布料优惠供应",
    "details": {
      "card": "caravan"
    }
  }
]
```

## 私人订单与聚餐 JSON 样例

```json
{
  "private_order_event": {
    "tick": 0,
    "actor_id": "npc-2",
    "type": "order",
    "text": "陈禾想要2份鲜鱼，出7镇币",
    "details": {
      "order_id": 1,
      "escrow": 7,
      "private_to": "wangjue"
    }
  },
  "private_order": {
    "id": 1,
    "buyer_id": "npc-2",
    "item": "fish",
    "quantity": 2,
    "unit_price": 3.5,
    "escrow": 7,
    "status": "open",
    "created_tick": 0,
    "expires_tick": 144,
    "seller_id": null,
    "private_to": "wangjue"
  },
  "feast_event": {
    "tick": 60,
    "actor_id": "npc-2",
    "type": "feast",
    "text": "陈禾发起广场聚餐，街坊们围坐在一起",
    "details": {
      "participants": [
        "npc-1",
        "npc-2",
        "wangjue"
      ]
    }
  }
}
```

## git diff --stat（共享工作树整体快照）

包含 W1 及其他并行任务已有变更，不应全部归因于 T5；git 默认 stat 不包含未跟踪的新文件。

```text
 backend/app/api/world.py                         |   5 +-
 backend/app/balance.py                           |  75 +++++++++
 backend/app/catalog.py                           |  21 +++
 backend/app/domain/actions.py                    | 143 ++++++++++++-----
 backend/app/domain/deliveries.py                 |   5 +-
 backend/app/domain/economy.py                    |  31 ++++
 backend/app/domain/migration.py                  |  27 +++-
 backend/app/domain/orders.py                     |  38 ++++-
 backend/app/domain/rules.py                      |   5 +-
 backend/app/domain/scheduler.py                  | 196 ++++++++++++++++++++---
 backend/app/pathfinding.py                       |  17 +-
 backend/app/realtime/protocol.py                 |   4 +
 backend/app/services/history.py                  |   6 +-
 backend/tests/test_districts.py                  |   7 +-
 backend/tests/test_map_expansion.py              |  11 +-
 backend/tests/test_reliability.py                |   1 +
 backend/tests/test_world.py                      |   3 +-
 frontend/src/components/DeliveryBoard.vue        |   8 +-
 frontend/src/components/EventDetails.vue         |   8 +-
 frontend/src/components/RecipeBook.vue           |  12 +-
 frontend/src/components/TownInspector.vue        |  70 ++++++--
 frontend/src/components/charts/ResourceChart.vue |   4 +-
 frontend/src/components/dialogs/PlaceDialog.vue  |   4 +-
 frontend/src/game/Atmosphere.ts                  | 131 ++++++++++++++-
 frontend/src/game/ResidentLayer.ts               |  23 ++-
 frontend/src/game/TownScene.ts                   |  47 +++++-
 frontend/src/game/art/map.ts                     |   5 +-
 frontend/src/game/art/vegetation.ts              |  39 ++++-
 frontend/src/game/scene-types.ts                 |   5 +-
 frontend/src/realtime/protocol.ts                |  19 ++-
 frontend/src/stores/town.ts                      |   6 +-
 frontend/src/types.ts                            |  15 +-
 frontend/src/views/MarketView.vue                | 123 +++++++++++++-
 frontend/tests/map.spec.ts                       |  22 ++-
 34 files changed, 976 insertions(+), 160 deletions(-)
```

T5 新文件：`backend/app/domain/fortune.py`、`backend/app/domain/initiatives.py`、`backend/tests/test_events.py`、本报告。
