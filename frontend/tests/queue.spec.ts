import { test, expect, type Page } from "@playwright/test";
async function login(page: Page) {
  await page.goto("/");
  await page.locator("[name=username]").fill("qianjunhao");
  await page.locator("[name=password]").fill("qianjunhao");
  await page.getByRole("button", { name: "进入雾河镇", exact: true }).click();
  await expect(page.locator(".world-live")).toContainText("共享世界已连接");
  const resume = page.getByRole("button", {
    name: "继续我的生活",
    exact: true,
  });
  if (await resume.isVisible()) await resume.click();
}
const state = (page: Page) =>
  page.request.get("/api/world").then((r) => r.json());
const own = async (page: Page) => (await state(page)).world.agents.qianjunhao;
async function appendRecipe(page: Page, group: string, name: string) {
  await page.getByRole("button", { name: group, exact: true }).click();
  const count = (await own(page)).plan.length;
  await page
    .locator(".recipe-card")
    .filter({ has: page.getByRole("heading", { name, exact: true }) })
    .getByRole("button", { name: /加入计划/ })
    .click();
  await expect.poll(async () => (await own(page)).plan.length).toBe(count + 1);
}

test("queue recipes, reorder and remove steps, finish a real chain and stop", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await login(page);
  await page.request.put("/api/me/control", { data: { mode: "manual" } });
  await page.request.put("/api/me/plan", { data: { actions: [] } });
  const before = await own(page);
  await page
    .getByRole("button", { name: /生活手册/ })
    .first()
    .click();
  await page.getByRole("button", { name: "配方图鉴", exact: true }).click();
  await appendRecipe(page, "制作", "烘焙面包");
  await appendRecipe(page, "采集", "收获谷物");
  await appendRecipe(page, "饮食与恢复", "吃一份面包");
  await appendRecipe(page, "饮食与恢复", "吃一份水果");
  // Saving a queue must not execute it or spend inventory.
  expect((await own(page)).completed).toBe(before.completed);
  expect((await own(page)).inventory).toEqual(before.inventory);
  await page.getByRole("button", { name: "关闭生活手册", exact: true }).click();
  await page.locator(".journey-plan summary").click();
  await page.getByRole("button", { name: "下移第 1 步", exact: true }).click();
  await expect
    .poll(async () => (await own(page)).plan.map((x: any) => x.type))
    .toEqual(["farm", "bake", "eat", "eat_fruit"]);
  await page.getByRole("button", { name: "移除第 4 步", exact: true }).click();
  await expect(page.locator(".plan-queue li")).toHaveCount(3);
  await expect(
    page.getByRole("button", { name: "上移第 1 步", exact: true }),
  ).toBeDisabled();
  await page.screenshot({
    path: "../.local/queue-desktop.png",
    style: ".toast{visibility:hidden}",
  });
  await page.getByRole("button", { name: "执行这份计划", exact: true }).click();
  await expect
    .poll(async () => (await own(page)).completed, { timeout: 25000 })
    .toBe(before.completed + 3);
  const result = await own(page);
  expect(result.mode).toBe("manual");
  expect(result.plan).toEqual([]);
  expect(result.inventory.grain).toBe(before.inventory.grain + 1);
  expect(result.inventory.bread).toBe(before.inventory.bread + 2);
  await expect(page.locator(".journey-description strong")).toHaveText(
    "本轮计划已完成",
  );
  const tick = (await state(page)).world.tick;
  await expect
    .poll(async () => (await state(page)).world.tick)
    .toBeGreaterThan(tick + 8);
  expect((await own(page)).completed).toBe(result.completed);
  expect(errors).toEqual([]);
});

test("failed finite step pauses later work and stale drafts cannot replace new queues", async ({
  page,
}) => {
  await login(page);
  await page.request.put("/api/me/plan", {
    data: { actions: [{ type: "eat_fruit" }, { type: "rest" }] },
  });
  await page.request.put("/api/me/control", { data: { mode: "plan" } });
  await expect.poll(async () => (await own(page)).activity).toBe("计划已暂停");
  await expect(page.locator(".town-journey")).toContainText("水果");
  expect((await own(page)).plan.map((x: any) => x.type)).toEqual(["rest"]);
  await page
    .locator("nav")
    .getByRole("button", { name: "我的 AI 分身", exact: true })
    .click();
  await expect(page.locator(".plan-step")).toHaveCount(1);
  // Another writer changes the persisted plan while this draft stays open.
  await page.request.post("/api/me/plan/append", {
    data: { actions: [{ type: "farm" }] },
  });
  await page.getByRole("button", { name: "保存计划", exact: true }).click();
  await expect(page.locator(".toast")).toContainText("计划已变化");
  expect((await own(page)).plan.map((x: any) => x.type)).toEqual([
    "rest",
    "farm",
  ]);
  await page.getByRole("button", { name: "同步", exact: true }).click();
  await expect(page.locator(".plan-step")).toHaveCount(2);
  await page.getByRole("button", { name: "仅执行本轮", exact: true }).click();
  await expect.poll(async () => (await own(page)).mode).toBe("plan");
  await page.getByRole("button", { name: "退出登录", exact: true }).click();
  await expect(page.locator(".login-card")).toBeVisible();
  await login(page);
  await expect
    .poll(async () => (await own(page)).mode, { timeout: 25000 })
    .toBe("manual");
  expect((await own(page)).activity).toBe("本轮计划已完成");
});
