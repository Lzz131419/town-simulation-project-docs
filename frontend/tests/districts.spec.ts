import layout from "../../shared/world-map.json" with { type: "json" };
import { test, expect, type Page } from "./fixtures/live-test";
const own = async (page: Page) =>
  (await (await page.request.get("/api/world")).json()).world.agents.lizhanbo;

test("new districts connect a real furniture chain to community delivery", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await page.locator("[name=username]").fill("lizhanbo");
  await page.locator("[name=password]").fill("lizhanbo");
  await page.getByRole("button", { name: "进入雾河镇", exact: true }).click();
  await expect(page.locator(".world-live")).toContainText("共享世界已连接");
  const resume = page.getByRole("button", {
    name: "继续我的生活",
    exact: true,
  });
  if (await resume.isVisible()) await resume.click();
  await page.request.put("/api/me/control", { data: { mode: "manual" } });
  await page.request.put("/api/me/plan", { data: { actions: [] } });
  for (const name of ["手作街区", "南岸商埠", "南部田园", "全镇"]) {
    const button = page.getByRole("button", { name, exact: true });
    await button.click();
    await expect(button).toHaveAttribute("aria-pressed", "true");
  }
  const before = await own(page);
  const steps = [
    ["蓝花亚麻田", "收割亚麻"],
    ["蓝线织坊", "织造布料"],
    ["木作工坊", "制作木材"],
    ["木作工坊", "制作木材"],
    ["榫卯家具坊", "制作家具"],
  ];
  // Queue through real map-place controls, including a recipe with missing inputs.
  for (const [place, actionName] of steps) {
    await page.getByRole("button", { name: "地点导览", exact: true }).click();
    await page
      .locator(".map-guide")
      .getByRole("button", { name: place, exact: true })
      .click();
    await page
      .getByRole("dialog", { name: place, exact: true })
      .locator(".place-action-card")
      .filter({ has: page.getByText(actionName, { exact: true }) })
      .getByRole("button", { name: /加入计划/ })
      .click();
    await page.getByRole("button", { name: "关闭地点", exact: true }).click();
  }
  await page.getByRole("button", { name: "地点导览", exact: true }).click();
  await page
    .locator(".map-guide")
    .getByRole("button", { name: "南岸交付站", exact: true })
    .click();
  await expect(page.locator(".delivery-request")).toHaveCount(6);
  const request = page.locator(".delivery-request").filter({
    has: page.getByRole("heading", { name: "新居家具", exact: true }),
  });
  await expect(
    request.getByRole("button", { name: "前往交付", exact: true }),
  ).toBeDisabled();
  await request.getByRole("button", { name: "加入计划", exact: true }).click();
  await expect.poll(async () => (await own(page)).plan.length).toBe(6);
  expect((await own(page)).cash).toBe(before.cash);
  expect((await own(page)).inventory).toEqual(before.inventory);
  await page.getByRole("button", { name: "关闭地点", exact: true }).click();
  await page.locator(".journey-plan summary").click();
  await page.getByRole("button", { name: "执行这份计划", exact: true }).click();
  await expect
    .poll(async () => (await own(page)).completed, { timeout: 45000 })
    .toBe(before.completed + 6);
  const after = await own(page);
  expect(after.mode).toBe("manual");
  expect(after.plan).toEqual([]);
  expect(after.inventory.flax).toBe(before.inventory.flax + 1);
  expect(after.inventory.wood).toBe(before.inventory.wood + 1);
  expect(after.inventory.cloth).toBe(before.inventory.cloth);
  expect(after.inventory.furniture).toBe(before.inventory.furniture);
  expect(after.cash).toBe(before.cash + 22);
  expect(after.delivery_log.items).toContain("furniture");
  expect(errors).toEqual([]);
});

test("canvas buildings stay clickable while map controls do not click through", async ({
  page,
}) => {
  await page.goto("/");
  await page.locator("[name=username]").fill("lizhanbo");
  await page.locator("[name=password]").fill("lizhanbo");
  await page.getByRole("button", { name: "进入雾河镇", exact: true }).click();
  await expect(page.locator(".world-live")).toContainText("共享世界已连接");
  const resume = page.getByRole("button", {
    name: "继续我的生活",
    exact: true,
  });
  if (await resume.isVisible()) await resume.click();
  await expect(page.locator(".map-loading")).toHaveCount(0);
  await page.getByRole("button", { name: "中心街区", exact: true }).click();
  const view = page.locator(".minimap-viewport");
  await expect
    .poll(async () => Number(await view.getAttribute("width")))
    .toBeGreaterThan(100);
  const frame = await page.locator(".phaser-host canvas").boundingBox();
  const [x, y, w, h] = await Promise.all(
    ["x", "y", "width", "height"].map(async (k) =>
      Number(await view.getAttribute(k)),
    ),
  );
  const farm = layout.buildings.find((b) => b.id === "farm")!;
  await page.mouse.click(
    frame!.x + ((farm.x + farm.w / 2 - x) / w) * frame!.width,
    frame!.y + ((farm.y + farm.h / 2 - y) / h) * frame!.height,
  );
  await expect(
    page.getByRole("dialog", { name: "晨光农场", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "关闭地点", exact: true }).click();
  for (const name of [
    "东岸原野",
    "南部田园",
    "手作街区",
    "南岸商埠",
    "全镇",
    "中心街区",
  ]) {
    await page.getByRole("button", { name, exact: true }).click();
    await expect(page.getByRole("dialog")).toHaveCount(0);
  }
});
