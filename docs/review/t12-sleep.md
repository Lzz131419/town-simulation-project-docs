# T12 睡眠系统验收

2026-11-21。共享工作树中实现，无回滚、无 commit、无 database schema 变化、无新增依赖或美术/音频资源。

## Home 模型及视觉选择

`shared/world-map.json` / `PLACES["home"]` 仅有一个河畔住宅目的地 `(325, 520)`，所有玩家与 NPC 共用；agent 没有独立 home ID。美术地图中另有七座 `kind=home` 建筑，因此不伪造个人住宅归属：按当前 sleeping 人数亮起至多七栋住宅，按游戏日轮换起点，同一快照始终复现相同灯光。窗格亮黄、室内暖光采用独立 Graphics 和既有程序生成灯光纹理，不重烘焙地图、不增加图片。

`ResidentLayer` 在 sleeping 变化后用约 400 ms 淡出/淡入整个居民容器，同时禁用睡眠居民头像点击；减少动态偏好下立即切换。`Atmosphere` 只在有睡眠居民且天色变暗时亮窗，醒来、白天、关闭 ambience 都熄灭；烘焙房等公共建筑灯光维持原逻辑。`audio.ts` 将 sleep / wake（包括 reason=disturbed）接入 T9 WebAudio 轻音，继续使用既有玩家过滤、静音、去重和自动播放限制。

夜宅截图：`../../.local/t12-sleep/night-homes.png`（本地忽略目录，不加入资源）。**已用图片查看工具实际查看最终截图**：左侧住宅双窗暖黄且室内有柔光，中间/右侧邻宅保持蓝暗窗，屋顶、家具、路灯和面包房均正常，无站立的睡眠居民。截图采用 T4/T10 独立 Phaser Canvas fixture，无登录、无保存世界修改；不是生产服务器端到端截图。

## 后端规则及边界

- 新增 `domain/sleep.py`，初始世界与 `upgrade_world` 都补 `sleeping=None`、`fatigue=0`、`sleep_history=[]`、`sleep_tracking_since`；旧档从迁移时刻开始观察，不臆造过去缺觉。全部存入原 world JSON。
- rest 先按既有路径回到 home，抵达才入睡；不再立即加 25 精力。前 12 个完整 tick 每 tick +7，之后深睡每 tick +10；浅睡速率已大于旧站休每四个决策 tick +25 的平均速率。数值、阈值、时段差异统一放在 `balance.sleep` 并随 catalog 发布。
- 普通居民精力 >=95、早上 06:00 或连续 36 tick 时醒；陈禾的精力阈值为 100，但同样受早晨/六小时上限约束。睡眠每 tick 在决策/移动前推进，manual 玩家也恢复；睡眠期间 API/start_action/execute 禁止动作，计划最后一步为 rest 时等醒后才 plan_done。
- 将需求中的“两天/48”解释为**滚动 48 个游戏小时=288 tick**，期间累计睡眠少于 24 tick 才置 fatigue=1；不是把 48 当作游戏日。计数有界且 JSON 重放一致。
- 疲劳精力上限 80，所有 ACTIONS 成本额外 +2；顺序为 `基础消耗 + T1雨天额外3 + 疲劳额外2`，无倍率相乘。雨天 farm 为 9+3+2=14；食物恢复也受 80 上限约束。rest 也计算 +2，但允许精力不足时开始，扣到最低 0，确保零精力仍能睡觉恢复；饥饿且不足 2 精力时 fallback 选择 rest，避免反复尝试无法支付成本的吃饭。
- 疲劳使 80 上限低于 95 醒来阈值，能连续睡满 30 tick 后清除，再正常恢复至醒来阈值；天亮/36 tick 上限仍优先限制总时长。醒来时保留计划，下一 tick 才继续。
- 成功的定向 gift/social 唤醒目标、双方关系各 -1，发出“被吵醒了”；被打断的 social 不再叠普通交流加成。无目标的社交与 NPC 私人订单/赠礼/慷慨赠礼选人过滤 sleeping，睡眠 NPC 不发起互动。
- 夜间回家优先于个性工作覆盖，但仍允许先吃背包中的食物。林溪 19:00 回家（比默认提前 2 小时，晚于 18:00–19:00 聚餐），苏晴 22:00 回家并将社交时段延长到 15:00；差异配置化。常规社交/聚餐时段不因睡眠时段被抑制；已在睡觉的玩家不被计入聚餐。
- T7b proxy_life 继续走 fallback→rest→抵达→sleeping；睡眠不依赖 npc 标记。
- 共享树同期新增的 T11 reinforce 可行性检查已使用 `action_energy_cost(w, a, ...)`，避免旧 energy_cost 名称失效并纳入疲劳成本。

## 事件样例

完整事件和每 tick 精力/阶段保存在 `t12-sleep-events.json`，由真实 domain execute + tick_world 执行生成。

| 场景 | tick / 时间 | 事件 / 精力 |
| --- | --- | --- |
| 健康、精力0 | 78 / 21:00 | sleep + rest，入睡 |
| 健康 | 90 / 23:00 | sleep_phase=deep，精力84 |
| 健康 | 91 / 23:10 | 深睡恢复到94 |
| 健康 | 92 / 23:20 | wake(restored)，精力100，连续14 tick |
| 疲劳、精力0 | 78 / 21:00 | 入睡 |
| 疲劳 | 90 / 23:00 | 深睡，精力上限80 |
| 疲劳 | 108 / 次日02:00 | 连续30 tick，fatigue_recovered，精力90 |
| 疲劳 | 109 / 次日02:10 | wake(restored)，精力100 |

高恢复速率与 >=95 即醒是本需求同时指定的行为，所以健康居民可能在半夜提前自然醒，并非强制睡满六小时。

## 验证与测试调整

新增 `backend/tests/test_sleep.py` 共 15 项（含参数化）：抵达后入睡、浅/深睡速率、三种自然醒、48小时边界、迁移幂等、疲劳恢复/上限/成本、gift/social打扰关系损失、决策/直接/API动作拦截、睡眠目标过滤、托管、个性时段、JSON保存恢复、计划完成顺序和低精力防卡死。

原 `test_personality.py` 的陈禾夜间仍工作断言改为白天/社交/傍晚工作，夜间睡觉由新测试覆盖；原 `test_reliability.py` 的 rest 立即 +12 改为入睡当下不恢复、下一 tick +7，保留夜间饥饿先吃食物断言。没有更新 golden 图片；视觉 fixture 新增灯光/头像状态断言及截图，T4/T10 原六项仍通过。音效测试增加 sleep/wake 纯音色与实时 store 事件链覆盖。

验证日志位于 `.local/t12-sleep/`：

- `pytest.txt`：全量 `cd backend && ../.venv/bin/python -m pytest tests -x -q`，**372 passed in 19.29s**（包含同期 T11 新增 5 项；T12 自增 15 项，相对原基线 352 为 +20）。
- `build.txt`：`npm run build` / vue-tsc + Vite，1664 modules transformed，成功。
- `playwright.txt`：`TOWN_E2E_BASE_URL=http://127.0.0.1:5178 npx playwright test tests/visual-effects.spec.ts tests/audio.spec.ts`，**24 passed (29.0s)**。
- `fixture-types.txt`：fixture、视觉与音效 spec 的独立 TypeScript 检查，退出0。
- 相关 Python Ruff check 与 `git diff --check` 通过。没有运行其他需登录/真实后端的 Playwright 文件，也没有真实扬声器听音验收。

完整日志尾部：

```text
........................................................................ [ 19%]
........................................................................ [ 38%]
........................................................................ [ 58%]
........................................................................ [ 77%]
........................................................................ [ 96%]
............                                                             [100%]
372 passed in 19.29s

vite v6.4.6 building for production...
transforming...
✓ 1664 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                        0.48 kB │ gzip:   0.35 kB
dist/assets/index-UtTWP13A.css        52.02 kB │ gzip:  10.98 kB
dist/assets/phaser-CkuN5Vkn.js         0.47 kB │ gzip:   0.34 kB
dist/assets/TownScene-Bn5xiBMg.js     42.55 kB │ gzip:  17.29 kB
dist/assets/index-B8wr2X6J.js        216.38 kB │ gzip:  77.59 kB
dist/assets/phaser-Czz4FBZH.js     1,481.77 kB │ gzip: 339.84 kB
✓ built in 3.55s

  ✓  22 tests/visual-effects.spec.ts:138:1 › market day props appear immediately, last all day, and expire without rebaking (1.4s)
  ✓  23 tests/visual-effects.spec.ts:166:1 › sleep fades avatars, lights occupied houses at night, and waking restores them (1.5s)
  ✓  24 tests/visual-effects.spec.ts:215:1 › reduced motion hides sleeping residents immediately (898ms)

  24 passed (29.0s)
```

最终回归期间首次收集到同期 T11 新测试时曾遇到 flood warning 事件缺少 outcome 的断言 KeyError，已报告协调方并由 T11 负责者修复；随后最终 372 项通过。独立验证用 5178 Vite 进程已停止，原有 5173 服务未改动。

## 改动范围

T12 修改：`backend/app/balance.py`、`catalog.py`、`domain/actions.py`、`migration.py`、`scheduler.py`、`initiatives.py`、`plans.py`、`tests/test_personality.py`、`tests/test_reliability.py`；`frontend/src/types.ts`、`game/ResidentLayer.ts`、`Atmosphere.ts`、`audio.ts`、`tests/fixtures/visuals.ts`、`tests/visual-effects.spec.ts`、`tests/audio.spec.ts`。新增 `domain/sleep.py`、`tests/test_sleep.py`、本报告及事件 JSON。

以下 `git diff --stat` 是共享工作树整体快照，含已验收未提交和同期 T11 改动，**不能全部归为 T12**；普通 diff 不包含 untracked 新文件，未暂存或提交它们：

```text
 backend/app/api/auth.py                          |  21 +-
 backend/app/api/realtime.py                      |   8 +-
 backend/app/api/world.py                         | 121 +++++++---
 backend/app/balance.py                           | 133 +++++++++++
 backend/app/catalog.py                           |  27 +++
 backend/app/domain/actions.py                    | 255 ++++++++++++++++-----
 backend/app/domain/deliveries.py                 |  27 ++-
 backend/app/domain/economy.py                    |  39 ++++
 backend/app/domain/migration.py                  |  34 ++-
 backend/app/domain/orders.py                     |  65 +++++-
 backend/app/domain/plans.py                      |   2 +-
 backend/app/domain/progression.py                |  11 +-
 backend/app/domain/rules.py                      |   8 +-
 backend/app/domain/scheduler.py                  | 270 ++++++++++++++++++++---
 backend/app/pathfinding.py                       |  17 +-
 backend/app/realtime/protocol.py                 |   6 +
 backend/app/runtime.py                           |  59 +++--
 backend/app/schemas.py                           |   1 +
 backend/app/services/history.py                  |  19 +-
 backend/config/game.json                         |   3 +-
 backend/tests/test_districts.py                  |   7 +-
 backend/tests/test_map_expansion.py              |  11 +-
 backend/tests/test_plan_queue.py                 |  10 +-
 backend/tests/test_reliability.py                |   5 +-
 backend/tests/test_world.py                      |   3 +-
 frontend/src/components/DeliveryBoard.vue        |  21 +-
 frontend/src/components/EventDetails.vue         |   8 +-
 frontend/src/components/RecipeBook.vue           |  12 +-
 frontend/src/components/ReportDashboard.vue      |  60 ++++-
 frontend/src/components/TownInspector.vue        |  74 +++++--
 frontend/src/components/TownMap.vue              |  32 ++-
 frontend/src/components/charts/ResourceChart.vue |   4 +-
 frontend/src/components/dialogs/PlaceDialog.vue  |   4 +-
 frontend/src/components/dialogs/ReturnDialog.vue |  14 +-
 frontend/src/composables/useReports.ts           |  13 +-
 frontend/src/game/Atmosphere.ts                  | 182 ++++++++++++++-
 frontend/src/game/ResidentLayer.ts               |  36 ++-
 frontend/src/game/TownScene.ts                   |  47 +++-
 frontend/src/game/art/map.ts                     |   5 +-
 frontend/src/game/art/vegetation.ts              |  39 +++-
 frontend/src/game/scene-types.ts                 |   5 +-
 frontend/src/realtime/protocol.ts                |  39 +++-
 frontend/src/stores/town.ts                      |  51 ++++-
 frontend/src/styles/game-ui.css                  |  33 +++
 frontend/src/styles/reports.css                  |  29 +++
 frontend/src/types.ts                            |  34 ++-
 frontend/src/views/MarketView.vue                | 123 ++++++++++-
 frontend/src/views/TownView.vue                  |  12 +
 frontend/tests/browser.spec.ts                   |   2 +-
 frontend/tests/districts.spec.ts                 |   2 +-
 frontend/tests/journey.spec.ts                   |   2 +-
 frontend/tests/lighting.spec.ts                  |   2 +-
 frontend/tests/map.spec.ts                       |  24 +-
 frontend/tests/queue.spec.ts                     |   2 +-
 frontend/tests/reliability.spec.ts               |  20 +-
 55 files changed, 1810 insertions(+), 283 deletions(-)
```
