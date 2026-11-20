import { test, expect, type Page } from "@playwright/test";
async function login(page: Page, id: string) {
  await page.goto("/");
  await page.locator("[name=username]").fill(id);
  await page.locator("[name=password]").fill(id);
  await page.getByRole("button", { name: "进入雾河镇", exact: true }).click();
  await expect(page.locator(".world-live")).toContainText("共享世界已连接");
  await expect(page.locator(".phaser-host canvas")).toBeVisible();
  const resume = page.getByRole("button", {
    name: "继续我的生活",
    exact: true,
  });
  if (await resume.isVisible()) await resume.click();
}
async function state(page: Page) {
  return page.request.get("/api/world").then((r) => r.json());
}
async function act(page: Page, id: string, action: unknown) {
  const before = (await state(page)).world.agents[id].completed;
  const r = await page.request.post("/api/me/action", { data: action });
  expect(r.ok()).toBeTruthy();
  await expect
    .poll(async () => (await state(page)).world.agents[id].completed, {
      timeout: 25000,
    })
    .toBeGreaterThan(before);
}

test("east bank navigation, action details, real fruit harvest and consumption", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await login(page, "yaofuen");
  for (const name of ["东岸原野", "南部田园", "全镇", "中心街区"]) {
    const button = page.getByRole("button", { name, exact: true });
    await button.click();
    await expect(button).toHaveAttribute("aria-pressed", "true");
    await expect(page.getByRole("dialog")).toHaveCount(0);
  }
  await page.getByRole("button", { name: "东岸原野", exact: true }).click();
  await page.getByRole("button", { name: "地点导览", exact: true }).click();
  await page
    .locator(".map-guide")
    .getByRole("button", { name: "河畔果园", exact: true })
    .click();
  const dialog = page.getByRole("dialog", { name: "河畔果园", exact: true });
  await expect(dialog).toContainText("获得 2 水果");
  await expect(dialog.locator(".place-travel")).toContainText("步行约");
  const before = (await state(page)).world.agents.yaofuen.inventory.fruit;
  await dialog.getByRole("button", { name: "安排此行动", exact: true }).click();
  await expect
    .poll(
      async () => (await state(page)).world.agents.yaofuen.inventory.fruit,
      { timeout: 25000 },
    )
    .toBe(before + 2);
  await page
    .locator("nav")
    .getByRole("button", { name: "集市交易", exact: true })
    .click();
  await page
    .locator(".product-card")
    .filter({ has: page.getByRole("heading", { name: "水果", exact: true }) })
    .getByRole("button", { name: "食用", exact: true })
    .click();
  await expect
    .poll(async () => (await state(page)).world.agents.yaofuen.inventory.fruit)
    .toBe(before + 1);
  await page
    .locator("nav")
    .getByRole("button", { name: "合作订单", exact: true })
    .click();
  await expect(page.getByLabel("需要什么").locator("option")).toHaveCount(15);
  await page.getByLabel("需要什么").selectOption("tool");
  await page
    .locator("nav")
    .getByRole("button", { name: "我的 AI 分身", exact: true })
    .click();
  await expect(
    page.locator(".plan-add select option[value=grill]"),
  ).toHaveCount(1);
  expect(errors).toEqual([]);
});

test("live material chains produce tools, boosted ore and a cooked meal", async ({
  page,
}) => {
  await login(page, "sunxiang");
  await act(page, "sunxiang", { type: "buy", item: "ore", quantity: 2 });
  await act(page, "sunxiang", { type: "buy", item: "wood", quantity: 2 });
  await act(page, "sunxiang", { type: "forge" });
  expect((await state(page)).world.agents.sunxiang.inventory.tool).toBe(1);
  await act(page, "sunxiang", { type: "mine" });
  let a = (await state(page)).world.agents.sunxiang;
  expect(a.inventory.ore).toBe(4);
  expect(a.inventory.tool).toBe(0);
  await act(page, "sunxiang", { type: "craft" });
  await act(page, "sunxiang", { type: "fish" });
  await act(page, "sunxiang", { type: "grill" });
  a = (await state(page)).world.agents.sunxiang;
  expect(a.inventory.meal).toBe(1);
  expect(a.inventory.fish).toBe(0);
  await act(page, "sunxiang", { type: "eat_meal" });
  expect((await state(page)).world.agents.sunxiang.inventory.meal).toBe(0);
});
