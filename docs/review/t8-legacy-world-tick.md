# T8：旧存档 tick 崩溃修复与验证

日期：2026-11-21。仅增量修改共享工作树，未回滚、未提交 commit、未更改数据库 schema，未修改既有测试。

## 根因与修复

开发库 `.local/town.db` 实查：世界停在 tick 45019，缺 `season` 和 `weather`；`rng_seed` 已存在。原来 `bootstrap.initialize` 会调用迁移，但 `upgrade_world` 本身漏补 season/weather，且运行时 `_commit` 不做迁移，重启也无法解决漏补字段。

直接读取防御清单（行号以本次完成时为准）：

| 文件 | 行号 | 修改 |
| --- | --- | --- |
| backend/app/domain/weather.py | 23 | RNG 返回值安全读取，默认 balance.weather.initial_seed（当前 42） |
| backend/app/domain/weather.py | 30, 42, 43 | 天气迁移与事件 payload 安全读取，默认 sunny |
| backend/app/domain/weather.py | 48, 56, 57, 63 | 季节轮换、事件 payload、行动可用性安全读取，默认 spring |
| backend/app/domain/weather.py | 71, 81, 84, 87, 90 | 能耗和产量修正使用天气/季节默认值 |
| backend/app/domain/scheduler.py | 184, 213, 300, 314 | 日程天气判断、饥饿增长、桥等待期限安全读取 |
| backend/app/domain/fortune.py | 40 | 洪水事件中的桥关闭期限安全读取 |

全后端 `backend/app/**/*.py` 先用 rg 搜索，再用 Python AST 区分读取与赋值：season/weather/rng_seed/bridge_closed_until/market_modifiers/action_modifiers/feast_day/supply 的直接下标 **读取数为 0**；合法赋值保留。

迁移兜底：

- `backend/app/domain/migration.py:13` 添加 season/weather 缺失字段补齐，默认值与 catalog.initial_world 一致。
- `backend/app/runtime.py:155` 在 `_commit` 的 deepcopy 后、回调前调用 upgrade_world，迁移与 tick 同事务提交并沿用原 revision 机制。
- `backend/app/domain/scheduler.py:250` 在 tick_world 的第一步调用 upgrade_world，覆盖独立模拟、回放与直接调用入口。
- 保留幂等扫描而不增加版本标记或缓存；复杂度为 O(角色数 × 物品数)，已有 map_version 时不重算路径。当前 12 角色世界重复 3 组、每组 10,000 次，最佳均值 **9.46 微秒/次**；runtime tick 两次扫描合计约 19 微秒。旧地图重定位只发生于实际需要地图迁移时。

## 新增回归测试

`backend/tests/test_migration.py` 新增 4 个测试：

1. `:57` 旧档补齐默认值与 initial_world 一致，现金、原有库存数量、tick 和 economy_total 不变；鱼整数库存转为 qty=2/fresh=100 的批次，再次迁移返回 False 且完整世界不变。
2. `:76` 从 initial_world 删除 migration 补齐的所有新增顶层字段、agent 字段以及新物品，批次库存退回整数后直接 tick_world **200 次**；断言 tick=200、世界/角色/库存字段齐备、实际跨过黎明并产生天气事件、RNG 已推进、资金/库存不变量通过、再次迁移无变化。
3. `:88` 未迁移的天气工具函数与 initial_world 默认行为一致；同时覆盖季节边界及天气/季节事件 payload。
4. `:107` 测试数据库写入旧档，mutate 回调在调用 tick_world 前断言迁移已完成；完成后读回验证 tick=1、revision+1 与字段齐备。

测试命令与尾部：

```text
cd backend && ../.venv/bin/python -m pytest tests -x -q
........................................................................ [ 85%]
.................................................                        [100%]
337 passed in 18.58s
```

基线 333，新增 4 个测试全部通过；git diff --check 通过。

## 真实开发存档恢复

确认 `backend/run.py` 没有 reload。先 SIGTERM 旧 scripts/dev.py supervisor PID 25977，并确认 8000/5173 已释放，避免两个 world clock 同时写库。

使用仓库 `.venv/bin/python` 在仓库根目录导入真实 app.database，数据库 URL 为 `sqlite:///.local/town.db`，执行一次 `asyncio.run(TownRuntime().mutate(tick_world))`。没有手工修改世界 JSON，字段修复完全通过迁移完成：

```json
{
  "before": {"tick": 45019, "revision": 45055, "missing": ["season", "weather"]},
  "after": {"tick": 45020, "revision": 45056, "season": "spring", "weather": "sunny", "rng_seed": 42},
  "invariants": "passed",
  "upgrade_still_needed": false
}
```

之后执行 python3 scripts/dev.py 重启，supervisor PID 34273，backend PID 34274，日志 `/tmp/town-t8-dev.log`。重新读库观察到 **自动 tick 45029 → 45030、revision 45066 → 45067**，天气已自然变化为 cloudy；没有额外调用 mutate 推进这两个观察点。

`GET /api/health/ready` 返回 HTTP 200，database/world_clock 均 true；`GET /metrics` 显示 `town_ticks_total 10`，没有 tick_failures_total 样本；前端 5173 返回 HTTP 200。服务继续在后台运行，无剩余阻塞。
