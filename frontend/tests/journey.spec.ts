import { test, expect } from "./fixtures/live-test";
import layout from "../../shared/world-map.json" with { type: "json" };
import { pathDistance, traversedPath } from "../src/game/motion";

test("motion follows actual traversed corners, never the replaced route length", () => {
  const start = { x: 0, y: 0 };
  const old = [
    { x: 16, y: 0 },
    { x: 16, y: 16 },
    { x: 32, y: 16 },
  ];
  // Server stopped halfway through its second segment; old route is now cancelled.
  expect(traversedPath(start, old, { x: 16, y: 8 })).toEqual([
    { x: 16, y: 0 },
    { x: 16, y: 8 },
  ]);
  expect(traversedPath(start, old, start)).toEqual([]);
  expect(traversedPath(start, old, { x: 32, y: 16 })).toEqual(old);
  // Unknown relocation must snap, not draw a straight walk through an obstacle.
  expect(traversedPath(start, old, { x: 300, y: 300 })).toBeNull();
  expect(traversedPath(start, [], { x: 16, y: 0 })).toBeNull();
  const changed = [
    { x: 16, y: 0 },
    { x: 16, y: -16 },
  ];
  expect(traversedPath(start, changed, { x: 16, y: -8 })).toEqual([
    { x: 16, y: 0 },
    { x: 16, y: -8 },
  ]);
  expect(pathDistance(start, old)).toBe(48);
  expect(pathDistance(start, [])).toBe(0);
});

test("recipe sources, food, stopped journey and expanded camera remain consistent", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await page.locator("[name=username]").fill("qianjunhao");
  await page.locator("[name=password]").fill("qianjunhao");
  await page.getByRole("button", { name: "进入雾河镇", exact: true }).click();
  await expect(page.locator(".phaser-host canvas")).toBeVisible();
  const resume = page.getByRole("button", {
    name: "继续我的生活",
    exact: true,
  });
  if (await resume.isVisible()) await resume.click();
  const state = () => page.request.get("/api/world").then((r) => r.json());
  const own = async () => (await state()).world.agents.qianjunhao;
  await page
    .getByRole("button", { name: /生活手册/ })
    .first()
    .click();
  await page.getByRole("button", { name: "配方图鉴", exact: true }).click();
  const forge = page.locator(".recipe-card").filter({ hasText: "打造工具" });
  await expect(forge).toContainText("缺 2 矿石");
  await forge.getByRole("button", { name: "山脚矿洞", exact: true }).click();
  await expect(
    page.getByRole("dialog", { name: "山脚矿洞", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "关闭地点", exact: true }).click();
  const bread = (await own()).inventory.bread;
  await page
    .getByRole("group", { name: "背包食物" })
    .getByRole("button", { name: "吃一份面包", exact: true })
    .click();
  await expect.poll(async () => (await own()).inventory.bread).toBe(bread - 1);
  await expect(
    page
      .getByRole("group", { name: "背包食物" })
      .getByRole("button", { name: "吃一份水果", exact: true }),
  ).toBeDisabled();
  const plan = [{ type: "rest" }, { type: "farm" }];
  await page.request.put("/api/me/plan", { data: { actions: plan } });
  await page.request.post("/api/me/action", {
    data: { type: "move", place: "mine" },
  });
  const journey = page.getByRole("region", { name: "我的当前行动" });
  await expect(journey).toContainText("山脚矿洞");
  await expect(journey).toContainText("约");
  await expect(journey).toContainText("待执行 2 项");
  await journey.getByRole("button", { name: "停止行动", exact: true }).click();
  await expect(journey).toContainText("等待新安排");
  const stopped = await own();
  expect(stopped.path).toEqual([]);
  expect(stopped.task).toBeNull();
  expect(stopped.plan.map((x: any) => x.type)).toEqual(plan.map((x) => x.type));
  await expect(page.locator(".resident-hero p")).toHaveText("等待新安排");
  // Compare minimap view rectangle center, allowing the bounds clamp at edges.
  await page.getByRole("button", { name: "东岸原野", exact: true }).click();
  const rect = page.locator(".minimap-viewport");
  await expect(rect).toBeVisible();
  const centerX = async () =>
    Number(await rect.getAttribute("x")) +
    Number(await rect.getAttribute("width")) / 2;
  await expect.poll(centerX).toBeGreaterThan(950);
  const initialCenter = await centerX();
  const viewWidth = async () => Number(await rect.getAttribute("width"));
  const initialWidth = await viewWidth();
  for (let i = 0; i < 3; i++) {
    await page.getByTitle("扩大地图", { exact: true }).click();
    await expect(page.locator(".app-shell")).toHaveClass(/map-focus/);
    await expect(
      page.getByRole("button", { name: "东岸原野", exact: true }),
    ).toHaveAttribute("aria-pressed", "true");
    await expect.poll(viewWidth).toBeGreaterThan(initialWidth + 100);
    await expect
      .poll(async () =>
        Math.abs(
          (await centerX()) -
            Math.min(
              layout.districts.find((d) => d.id === "east")!.x,
              layout.bounds.x + layout.bounds.width - (await viewWidth()) / 2,
            ),
        ),
      )
      .toBeLessThan(2);
    await page.getByRole("button", { name: "退出大地图", exact: true }).click();
    await expect
      .poll(async () => Math.abs((await centerX()) - initialCenter))
      .toBeLessThan(2);
    await expect
      .poll(async () => Math.abs((await viewWidth()) - initialWidth))
      .toBeLessThan(2);
  }
  expect(errors).toEqual([]);
});
