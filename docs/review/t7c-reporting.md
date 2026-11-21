# T7c 世界事件流与报表

## Event.details 约定

事件原有 key 保留，新增字段采用稳定的 snake_case key：

- 交易：`amount`（成交总额）、`item`、`quantity`、`unit_price`；买入事件还保留 `quoted_unit_price` 和 `discount`。
- 订单：发布事件带 `transaction_type=posted`，成交事件带 `transaction_type=filled`；取消和到期分别为 `cancelled`、`expired`，避免把托管或退款重复计入成交额。
- 生产：`inputs` 与 `outputs` 都是 `{item: quantity}`，其中 `outputs` 是受天气和季节修正后的实际产出。
- 财政与损耗：`levy.amount` 是单个居民缴纳额，`fiscal.amount` 是当日汇总；`spoilage.quantity` 是变质件数，`spoilage.items` 是按物品拆分。

## WorldSample 维度

采样仍按 `balance.simulation.sample_interval_ticks` 写入，保留 60 个采样点的历史上限。每个 JSON 样本包含：

`tick`、`treasury`、`resident_cash`/`cash`、`completed`、`reputation`、`escrow`、`market`（市场库存快照）、`inventory`（居民持有汇总）、`prices`、`trades`、`energy`、`hunger`、`weather`、`season`。

其中 `completed` 和 `reputation` 是全体居民汇总；`prices` 是按当前市场状态计算的买入价快照，`weather` 和 `season` 是该采样点的共享气候状态。

## 聚合接口

`GET /api/report/economy?days=7` 沿用报表鉴权，按最近 `days * ticks_per_day` 的事件 tick 范围聚合，响应同时提供 `daily` 和 `series`。每日字段为 `trade_amount`、`trade_count`、`production`、`levy_total`、`spoilage_loss`，`totals` 提供同名总计；订单发布、取消、到期不会重复计入成交额。
