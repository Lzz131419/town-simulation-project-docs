# T4 天气、季节与居民工作动画验收

2026-11-21：实现完成，`npm run build` 通过，独立 Chrome/Phaser 状态自验 5/5 通过。没有修改后端、共享 `types.ts`、协议或 store，没有提交 commit；工作树其他 W1/并行任务改动保留。

## 状态来源与实现位置

Store 的 `world` 为 `frontend/src/stores/town.ts:52` 的 ref，实时数据在该文件第 159 行赋值；场景通过 `SceneReader().world` 读取同一份世界数据。仅在场景边界用可选字段扩展类型（`frontend/src/game/scene-types.ts:3`），旧快照没有天气/季节时维持晴天、常绿树。

| 效果 | 实现位置 | 行为 |
| --- | --- | --- |
| 天气与季节分流 | `frontend/src/game/visual-state.ts:5` | 四种天气；winter + rain/cloudy 为雪，winter + storm 仍为暴雨 |
| 初始天气及切换 | `frontend/src/game/Atmosphere.ts:138`、`:141` | 构造时立即应用；天气、季节、ambience 变化绕过 24 FPS 绘制节流 |
| 雨 / 暴雨 / 雪 | `frontend/src/game/Atmosphere.ts:176` | Graphics 斜短线 / 白色圆点；中雨 140、暴雨 260、雪 100 个；暴雨更斜更快 |
| 暴雨变暗 | `frontend/src/game/Atmosphere.ts:34`、`:156` | 独立全图深色覆盖，位于居民之上，暴雨透明度 0.22 |
| 阴天雾与 motes | `frontend/src/game/Atmosphere.ts:48`、`:238` | 径向渐变边缘暗角；motes 从 24 增至 48，白天也可见 |
| 雨打水面 | `frontend/src/game/Atmosphere.ts:229` | 18 / 32 个扩散椭圆，避开桥梁和现有码头船区域；雪不生成雨涟漪 |
| ambience / 减少动态 | `frontend/src/game/Atmosphere.ts:155`、`:168`、`:173` | 关 ambience 清空雨雪、水面动效、motes、雾及天气暗层；减少动态时雨雪静止、半密度且降低透明度 |
| 秋季 / 冬季树冠 | `frontend/src/game/art/vegetation.ts:55`、`:97` | 秋季黄橙色、冬季灰白色；树干保持原色 |
| 全地图树木覆盖 | `frontend/src/game/art/map.ts:19`、`frontend/src/game/art/vegetation.ts:4` | 按绘图 context 设置调色板，覆盖所有 drawTree 调用，包括果园、外围、东岸、南部 |
| 季节更新 / 恢复 | `frontend/src/game/TownScene.ts:42`、`:236` | 首帧按当前季节生成；季节变化刷新同一纹理；春夏互切不重画，秋冬离开后恢复常绿 |
| 冬季屋顶积雪 | `frontend/src/game/TownScene.ts:52` | 独立半透明 Graphics 多边形，仅覆盖原有窄屋顶；积雪本身不烘焙进地图，不遮盖室内 |
| 工作动画门控 | `frontend/src/game/ResidentLayer.ts:297` | 后端 path 和本地补间均停止后播放；开始移动、取消任务、切换任务会复位头像变换 |
| 弯腰 / 挥动 / 收线 | `frontend/src/game/visual-state.ts:40` | 六种采收任务每 550 ms 两帧 squash；chop/craft 每 380 ms 两姿态；fish 每 2.6 s 短暂收线，其余时间静止；减少动态时停止工作动效 |

树木原先与地面、建筑同在一张 Canvas 中，因此树冠换色沿用生成时调色板方案，在季节变化时重新绘制该地图、更新现有 GPU 纹理；屋顶积雪单独绘制且只切换可见性，不因积雪重烘焙。没有每帧重画地图，也没有为每个季节保留多份地图纹理。

## 已运行的验证

在 `frontend` 目录运行：

```sh
npm run build
npm run dev -- --port 5178 --strictPort
TOWN_E2E_BASE_URL=http://127.0.0.1:5178 npx playwright test tests/visual-effects.spec.ts
npx tsc --noEmit --target ES2022 --module ESNext --moduleResolution Bundler --lib ES2022,DOM --skipLibCheck --resolveJsonModule tests/fixtures/visuals.ts tests/visual-effects.spec.ts
```

- Build：vue-tsc + Vite 成功，1661 个模块转换。
- Playwright：Chrome 中的实际 Phaser Canvas 场景，5 passed，6.3 秒。复用现有 Playwright，无新增 Vitest 或依赖。
- 自验页面：`frontend/tests/fixtures/visuals.html` + `visuals.ts`，独立 SceneReader fixture，不请求后端、不登录、不更改存档。
- 验证了初始雨天；sunny/rain/storm/cloudy 切换；冬季雨/阴转雪、暴雨保持雨；环境关闭清空效果及重新打开恢复；减少动态冻结粒子和工作动画；秋冬树叶真实 Canvas 像素换色并恢复春季原色；纹理数量不增长；屋顶覆盖层可见性；移动、抵达补间、工作、取消任务切换。
- 第一轮季节像素断言发现目标 Canvas 遗留 scale/translate 导致地图被二次变换，已在像素复制时 resetTransform 修复并重新全量运行这 5 项，通过。
- 新代码与测试 Prettier 检查、`git diff --check` 通过；测试 fixture 额外 TypeScript 检查通过。
- 已查看秋季和冬季截图：树冠变色、屋顶覆盖及室内保留正常；截图在 `.local/t4-visuals/autumn.png`、`.local/t4-visuals/winter.png`（忽略文件，不入 Git）。
- 独立验收用的 5178 Vite 进程已停止。

## Diff 范围

已运行全工作树 `git diff --stat`；完整输出保存在 `.local/t4-visuals/worktree-diff-stat.txt`，其中包含其他派发任务的并行改动，不能全部归入 T4。

T4 已跟踪文件的 `git diff --stat -- frontend/src/game`：

```text
 frontend/src/game/Atmosphere.ts     | 131 +++++++++++++++++++++++++++++++++---
 frontend/src/game/ResidentLayer.ts  |  23 +++++--
 frontend/src/game/TownScene.ts      |  47 ++++++++++++-
 frontend/src/game/art/map.ts        |   5 +-
 frontend/src/game/art/vegetation.ts |  39 +++++++++--
 frontend/src/game/scene-types.ts    |   5 +-
 6 files changed, 231 insertions(+), 19 deletions(-)
```

另新增 `frontend/src/game/visual-state.ts`（67 行）、`frontend/tests/visual-effects.spec.ts`（136 行）、`frontend/tests/fixtures/visuals.ts`（150 行）、`frontend/tests/fixtures/visuals.html`（11 行）及本报告；未暂存，因此普通 `git diff --stat` 不包含这些新文件。

## 仍需人工浏览器确认

- 不同屏幕、缩放与地区下，雨雪密度、斜率、雾的暗角强度是否符合美术预期；自动化验证的是实际 Graphics 绘制指令与部分像素，不能替代主观视觉验收。
- 长时间观看弯腰、挥动及收线的节奏与辨识度，尤其多人同时工作时；当前无需新资源，采用原头像形变，非独立手臂骨骼动画。
- 较弱设备上的季节切换瞬时耗时和暴雨运行帧率；由于地图为统一烘焙画布，换季会有一次地图重绘，尚未进行性能基准。
- 完整真实服务下自然天气/季节推进与工作任务生命周期的端到端体验；此次使用隔离状态 fixture，没有触发后端任务或等待真实季节推进。
- Chrome 以外浏览器与 WebGL 渲染模式；本次浏览器自动化使用 Chrome + Phaser Canvas。
