# T9：WebAudio 合成音效系统

日期：2026-11-21。实现完成，未提交 commit。沿用共享工作树的已验收改动；本任务没有修改后端、依赖清单或任何音频资源文件。

## 实现与设置语义

- 新增 `frontend/src/game/audio.ts`：纯音色参数函数 `soundForEvent` / `environmentFor` + WebAudio 渲染器 `TownAudio`。仅使用 OscillatorNode、内存白噪声 AudioBuffer、BiquadFilterNode、GainNode。
- `stores/town.ts` 的 `apply()` 在验证 snapshot/patch 并更新状态后调用 `audio.consume()`；同一 HTTP refresh / WebSocket 入口，事件 id 高水位及批内去重。登录首帧仅建立基线，重连历史、重复事件、未解锁/静音期间事件不会在以后补播。每包至多 3 个提示，提示间隔 180ms，队列最多超前 450ms。
- **范围选择：只播 `actor_id === 当前玩家 id` 的事件**，全部 NPC/其他居民事件不播；订单成交买方若不是 actor，也不播。无需计算目击距离，避免 NPC 音效轰炸。
- 地图「画面图层」面板新增「声音」总开关、0–100% 音量、独立「环境音」。原「昼夜与环境动态」依然控制视觉 ambience，同时约束环境音；关闭 ambience 或环境音不影响动作音。Phaser `noAudio: true` 保留，因为音频由 store 的独立引擎管理。
- 默认总开关开启、音量 35%；系统 `prefers-reduced-motion: reduce` 时，未保存过偏好的环境音默认关闭，用户可显式开启。设置保存到 localStorage `mist-river-audio-v1`，禁用存储时退化为本会话设置；音量读取校验并限制在 0–1。
- 创建 store/登录/收到事件均不创建 AudioContext；登录后首个 pointerdown/keydown/click 才创建并 resume。被浏览器拒绝时吞掉拒绝，下一交互继续重试同一 context；不支持 WebAudio 不阻断 UI 或世界更新。
- 后台页面暂停 context 并停掉短音；恢复可见后尝试恢复。退出登录清空事件基线、淡出音频，卸载移除监听器、计时器、节点并关闭 context。短音 onended 断开节点。
- 环境增益和滤波截止频率使用 700ms linearRamp，打断切换时 cancelAndHoldAtTime 保持当前值（兼容 fallback）；总音量用 60ms ramp。两个循环噪声源始终复用，不会每个 tick 新建音频图。
- 可选脚步声未实现，避免增加持续提示与 ResidentLayer 相关范围。

## 音效、参数、触发对照

下列 gain 是合成节点峰值，最终还乘以用户全局音量（默认 0.35）。所有短音包络均为 6ms 起音，指数衰减到 0.0001，再用 10ms 收尾到 0，随后停止并断开节点。

| 音效 | event.type / 条件 | 合成参数 |
| --- | --- | --- |
| 收获叮 | farm / harvest_veg / gather / gather_honey / harvest_flax / forage / mine / chop / fish | 正弦 740 / 775 / 810 / 845 / 880 / 915 / 950 / 985 / 1020 Hz；240ms；gain 0.16 |
| 制作咚/锤 | bake / weave / assemble / forge / craft / cook / grill / brew | 正弦 180→70 Hz、170ms、gain 0.20；叠 950 Hz 低通白噪声 35ms、gain 0.05 |
| 硬币 | buy / sell；order 仅 details.transaction_type === filled | 两击间隔 90ms；每击正弦 1320 Hz/100ms/gain 0.09 + 非整数泛音 2112 Hz/70ms/gain 0.035；posted/cancelled 静音 |
| 交付旋律 | delivery | 正弦 523→659→784 Hz；各 180ms，起点 0/110/220ms，gain 0.12 |
| 进食 | eat / eat_*（包含 eat_meal、eat_fruit 等现有动作） | 两个低通白噪声 burst：700 Hz/45ms/gain 0.10；延迟 80ms 后 550 Hz/40ms/gain 0.08 |
| 温暖双音和弦 | social / gift / feast | 同时正弦 330 + 415 Hz；320ms；gain 0.09 / 0.08 |
| 失败低哑音 | blocked / failed / failure | 三角波 130→65 Hz；190ms；gain 0.12 |
| 雨 | weather=rain | 2秒内存白噪声循环、1400 Hz 低通、Q=0.5；gain 0.055 |
| 暴雨 | weather=storm | 同一循环白噪声、2200 Hz 低通；gain 0.10 |
| 极轻风 | weather=cloudy、非冬季 | 第二路循环白噪声、380 Hz 带通、Q=0.5；gain 0.012 |
| 冬风 | season=winter（任意天气） | 第二路循环白噪声、1100 Hz 带通、Q=0.5；gain 0.035；可叠雨层；冬季不合成蟋蟀 |
| 夜间蟋蟀 | lighting.daylight(tick).night > 0 且非冬季 | 每 1700ms 三个 chirp，间隔 85ms；正弦 3600→4100 Hz、45ms、局部 gain 0.3；总线 gain = night / 0.34 × 0.045，与同一 daylight 曲线随昼夜变化 |

未知事件不发声。环境音只在 world 存在且声音、环境音、ambience 三开关均开启时可闻。

## 验证与证据

`cd frontend && npm run build`：exit 0。最终输出：

```text
vite v6.4.6 building for production...
✓ 1662 modules transformed.
dist/index.html                        0.48 kB │ gzip:   0.35 kB
dist/assets/index-Cb4M3Sn2.css        51.48 kB │ gzip:  10.83 kB
dist/assets/phaser-CkuN5Vkn.js         0.47 kB │ gzip:   0.34 kB
dist/assets/TownScene-CEJaU4VI.js     40.65 kB │ gzip:  16.61 kB
dist/assets/index-D1tA9V24.js        214.40 kB │ gzip:  76.98 kB
dist/assets/phaser-Czz4FBZH.js     1,481.77 kB │ gzip: 339.84 kB
✓ built in 3.58s
```

新增 `frontend/tests/audio.spec.ts` 共 13 项：7 组纯参数/动作别名断言；订单和环境纯函数；真实 App/store/WebSocket patch 与完整 snapshot 的 mock AudioContext 集成；设置和持久化；天气/夜间/冬季与 reduced 默认；自动播放拒绝重试/零音量/最小桌面宽度；不支持 AudioContext 的降级。`tests/fixtures/audio.html` + `audio.ts` 仅用作测试挂载真实 App 并 spy `TownAudio.play`，不是生产入口。API/WS 全部 mock，未变更后端运行数据。

测试执行记录（没有把 mock 当成真实听感或后端验收）：

```text
npm run test:browser -- tests/audio.spec.ts
11 passed (15.2s)                         # 最初 11 项

npm run test:browser -- tests/audio.spec.ts tests/visual-effects.spec.ts tests/lighting.spec.ts
19 passed, 1 failed (24.9s)               # 新增边界用例后，共 20 项
# 唯一失败：测试假定整个 app 支持 390px 手机视口；现有 town.css 明确 min-width:1120px
# 将布局断言改为项目现有最小支持宽度 1120px；保留滑块不溢出面板的检查

npm run test:browser -- tests/audio.spec.ts -g 'autoplay resume rejection'
1 passed (2.7s)                           # 上述唯一失败项定向重跑通过
```

最终全部 13 项音频用例与 7 项视觉/光照回归均有通过结果，组合运行没有再次全量重跑。`git diff --check` 通过；7 个新增/修改的前端文件 Prettier 检查通过。使用已有 Vite 5173 服务，已确认其 cwd 是本仓库 frontend。

设置面板截图：`frontend/test-results/t9-audio-settings.png`（测试输出目录，未纳入版本控制）；已实际查看，1120px 宽度下完整显示 3 个声音控件，滑块在面板内。现有 1120px 最小宽度意味着手机整体布局仍不适配，属于已存在限制，此任务未扩展为整体响应式改造。

## 修改文件

T9 修改已有文件：`frontend/src/components/TownMap.vue`、`frontend/src/stores/town.ts`、`frontend/src/styles/game-ui.css`。新增：`frontend/src/game/audio.ts`、`frontend/tests/audio.spec.ts`、`frontend/tests/fixtures/audio.ts`、`frontend/tests/fixtures/audio.html`、本报告。store 原有库存/return_summary/report 等共享改动全部保留。

下面是工作树整体 `git diff --stat`（**包含任务开始前的共享改动，非 T9 独占统计**；git 默认不统计尚未跟踪的新文件，所以上述新文件单独列出）：

```text
 backend/app/api/auth.py                          |  21 ++-
 backend/app/api/realtime.py                      |   8 +-
 backend/app/api/world.py                         | 121 ++++++++++---
 backend/app/balance.py                           |  89 +++++++++
 backend/app/catalog.py                           |  22 +++
 backend/app/domain/actions.py                    | 191 +++++++++++++++-----
 backend/app/domain/deliveries.py                 |  10 +-
 backend/app/domain/economy.py                    |  36 ++++
 backend/app/domain/migration.py                  |  33 +++-
 backend/app/domain/orders.py                     |  65 +++++--
 backend/app/domain/rules.py                      |   5 +-
 backend/app/domain/scheduler.py                  | 220 ++++++++++++++++++++---
 backend/app/pathfinding.py                       |  17 +-
 backend/app/realtime/protocol.py                 |   6 +
 backend/app/runtime.py                           |  59 ++++--
 backend/app/services/history.py                  |  19 +-
 backend/tests/test_districts.py                  |   7 +-
 backend/tests/test_map_expansion.py              |  11 +-
 backend/tests/test_plan_queue.py                 |  10 +-
 backend/tests/test_reliability.py                |   1 +
 backend/tests/test_world.py                      |   3 +-
 frontend/src/components/DeliveryBoard.vue        |   8 +-
 frontend/src/components/EventDetails.vue         |   8 +-
 frontend/src/components/RecipeBook.vue           |  12 +-
 frontend/src/components/ReportDashboard.vue      |  60 ++++++-
 frontend/src/components/TownInspector.vue        |  74 ++++++--
 frontend/src/components/TownMap.vue              |  26 ++-
 frontend/src/components/charts/ResourceChart.vue |   4 +-
 frontend/src/components/dialogs/PlaceDialog.vue  |   4 +-
 frontend/src/components/dialogs/ReturnDialog.vue |  14 +-
 frontend/src/composables/useReports.ts           |  13 +-
 frontend/src/game/Atmosphere.ts                  | 131 +++++++++++++-
 frontend/src/game/ResidentLayer.ts               |  23 ++-
 frontend/src/game/TownScene.ts                   |  47 ++++-
 frontend/src/game/art/map.ts                     |   5 +-
 frontend/src/game/art/vegetation.ts              |  39 +++-
 frontend/src/game/scene-types.ts                 |   5 +-
 frontend/src/realtime/protocol.ts                |  19 +-
 frontend/src/stores/town.ts                      |  51 +++++-
 frontend/src/styles/game-ui.css                  |   5 +
 frontend/src/styles/reports.css                  |  29 +++
 frontend/src/types.ts                            |  19 +-
 frontend/src/views/MarketView.vue                | 123 ++++++++++++-
 frontend/tests/map.spec.ts                       |  22 ++-
 44 files changed, 1456 insertions(+), 239 deletions(-)
```

## 仍需人工试听

- 耳机与外放下：收获是否清脆但不刺耳；制作/blocked 低音是否可分辨；双击硬币、三音交付和社交和弦是否自然；进食噪声是否像轻咀嚼。
- 默认 35% 和最大音量下：多动作短时间叠加是否过响；所有提示与雨/风/蟋蟀的相对响度是否合适。
- 晴→雨→暴雨→阴、夏→冬、昼→夜切换，以及中途反向切换：是否平滑、无爆音、循环接缝是否可闻。
- 真正浏览器/设备的首次交互解锁、静音/恢复、后台→前台、退出登录：是否符合预期；尤其 Safari/iOS 与设备切换。自动化覆盖了 mock resume 拒绝重试，但未作这些平台实机试听。
- 蟋蟀 3.6–4.1kHz 的舒适度和长时间环境音疲劳感；必要时仅调整纯参数而不动事件接线。

自动化确认的是音色描述、路由、节点创建/调度、ramp 与清理，不能据此宣称已经完成真人听感验收；可选脚步声未做。
