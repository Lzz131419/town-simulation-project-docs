import { test, expect } from "./fixtures/live-test";
const ids = [
  "zhangguo",
  "wangjue",
  "lizhanbo",
  "sunxiang",
  "qianjunhao",
  "yaofuen",
];
async function login(page: any, id = "wangjue") {
  await page.goto("/");
  await page.locator("[name=username]").fill(id);
  await page.locator("[name=password]").fill(id);
  await page.getByRole("button", { name: "进入雾河镇" }).click();
  await expect(page.locator(".world-live")).toContainText("共享世界已连接");
  await expect(page.locator(".phaser-host canvas")).toBeVisible();
  const resume = page.getByRole("button", {
    name: "继续我的生活",
    exact: true,
  });
  if (await resume.isVisible()) await resume.click();
}
test("six simultaneous members, real movement, workspace and cloud archive", async ({
  browser,
}) => {
  const contexts = await Promise.all(
    ids.map(() =>
      browser.newContext({ viewport: { width: 1440, height: 900 } }),
    ),
  );
  const pages = await Promise.all(contexts.map((c) => c.newPage()));
  const errors: string[] = [];
  pages[1].on("pageerror", (e) => errors.push(e.message));
  await Promise.all(pages.map((p, i) => login(p, ids[i])));
  const p = pages[1];
  await expect(p.locator(".world-live")).toContainText("6 / 6");
  await p.screenshot({
    path: "../.local/v2-town-desktop.png",
    fullPage: true,
    animations: "disabled",
  });
  const old = await p.request.get("/api/world").then((r) => r.json());
  await p.getByRole("button", { name: "去农场", exact: true }).click();
  await expect
    .poll(
      async () => {
        const s = await p.request.get("/api/world").then((r) => r.json());
        return s.world.agents.wangjue.inventory.grain;
      },
      { timeout: 25000 },
    )
    .toBeGreaterThan(old.world.agents.wangjue.inventory.grain);
  const other = await pages[0].request.get("/api/world").then((r) => r.json());
  expect(other.world.agents.wangjue.inventory.grain).toBeGreaterThan(
    old.world.agents.wangjue.inventory.grain,
  );
  for (const name of [
    "邻里档案",
    "集市交易",
    "合作订单",
    "共同建设",
    "邻里留言",
    "我的 AI 分身",
    "进度与归档",
    "生活记录",
  ]) {
    await p.locator("nav").getByRole("button", { name, exact: true }).click();
    await expect(p.locator(".workspace-page h1")).toHaveText(name);
  }
  await p
    .locator("nav")
    .getByRole("button", { name: "邻里留言", exact: true })
    .click();
  await p.locator("textarea").fill("浏览器联调：我们一起准备河畔集市。");
  await p.getByRole("button", { name: "发送留言", exact: true }).click();
  await expect(p.locator(".message").first()).toContainText("浏览器联调");
  await pages[0]
    .locator("nav")
    .getByRole("button", { name: "邻里留言", exact: true })
    .click();
  await expect(pages[0].locator(".message").first()).toContainText(
    "浏览器联调",
  );
  await p
    .locator("nav")
    .getByRole("button", { name: "我的 AI 分身", exact: true })
    .click();
  await p.screenshot({
    path: "../.local/v2-agent-desktop.png",
    fullPage: true,
    animations: "disabled",
  });
  await expect(
    p.getByRole("button", { name: "让 AI 制定计划", exact: true }),
  ).toBeDisabled();
  await p
    .locator("nav")
    .getByRole("button", { name: "进度与归档", exact: true })
    .click();
  await p.getByPlaceholder("输入归档名称").fill("浏览器验证归档");
  await p.getByRole("button", { name: "创建个人归档", exact: true }).click();
  await expect(p.locator(".archive-card").first()).toContainText(
    "浏览器验证归档",
  );
  await p
    .locator(".archive-card")
    .first()
    .getByRole("button", { name: "查看归档" })
    .click();
  await expect(p.locator(".modal")).toContainText("恢复仅应用自己的计划");
  await p.getByRole("button", { name: "关闭归档" }).click();
  await p
    .locator("nav")
    .getByRole("button", { name: "小镇生活", exact: true })
    .click();
  await p.getByTitle("扩大地图").click();
  await expect(p.locator(".app-shell")).toHaveClass(/map-focus/);
  await p.keyboard.press("Escape");
  await expect(p.locator(".app-shell")).not.toHaveClass(/map-focus/);
  await p.setViewportSize({ width: 1280, height: 720 });
  await p.screenshot({
    path: "../.local/v2-town-1280.png",
    fullPage: true,
    animations: "disabled",
  });
  expect(
    await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
  ).toBeTruthy();
  expect(errors).toEqual([]);
  await Promise.all(contexts.map((c) => c.close()));
});
test("logout keeps saved rule plan and removes online presence", async ({
  browser,
}) => {
  const c = await browser.newContext();
  const p = await c.newPage();
  await login(p);
  await p.request.put("/api/me/plan", {
    data: { actions: [{ type: "rest" }, { type: "farm" }] },
  });
  await p.request.put("/api/me/control", { data: { mode: "rules" } });
  await p.getByRole("button", { name: "退出登录", exact: true }).click();
  await expect(p.locator(".login-card")).toBeVisible();
  await p.screenshot({
    path: "../.local/v2-login.png",
    fullPage: true,
    animations: "disabled",
  });
  await login(p);
  const state = await p.request.get("/api/world").then((r) => r.json());
  expect(state.world.agents.wangjue.mode).toBe("rules");
  await p.request.put("/api/me/control", { data: { mode: "manual" } });
  await c.close();
});

test("two members complete an escrow order through the interface", async ({
  browser,
}) => {
  const buyerContext = await browser.newContext();
  const sellerContext = await browser.newContext();
  const buyer = await buyerContext.newPage();
  const seller = await sellerContext.newPage();
  await login(buyer, "wangjue");
  await login(seller, "zhangguo");
  const state = await buyer.request.get("/api/world").then((r) => r.json());
  await buyer
    .locator("nav")
    .getByRole("button", { name: "合作订单", exact: true })
    .click();
  await buyer.getByLabel("需要什么").selectOption("bread");
  await buyer.getByLabel("数量", { exact: true }).fill("1");
  await buyer.getByLabel("每份报酬").fill("3");
  await buyer
    .getByRole("button", { name: "发布采购订单", exact: true })
    .click();
  const order = buyer
    .locator(".order-row")
    .filter({ hasText: /王崛需要\s*1\s*份面包/ })
    .first();
  await expect(order).toContainText("资金已托管");
  await seller
    .locator("nav")
    .getByRole("button", { name: "合作订单", exact: true })
    .click();
  await seller
    .locator(".order-row")
    .filter({ hasText: /王崛需要\s*1\s*份面包/ })
    .first()
    .getByRole("button", { name: "交付", exact: true })
    .click();
  await expect(order).toContainText("已交付");
  const result = await buyer.request.get("/api/world").then((r) => r.json());
  expect(result.world.agents.wangjue.cash).toBe(
    state.world.agents.wangjue.cash - 3,
  );
  expect(result.world.agents.zhangguo.cash).toBe(
    state.world.agents.zhangguo.cash + 3,
  );
  expect(result.world.agents.wangjue.inventory.bread).toBe(
    state.world.agents.wangjue.inventory.bread + 1,
  );
  await buyer.screenshot({
    path: "../.local/v2-orders-desktop.png",
    fullPage: true,
    animations: "disabled",
  });
  await buyer
    .locator("nav")
    .getByRole("button", { name: "共同建设", exact: true })
    .click();
  await buyer.screenshot({
    path: "../.local/v2-project-desktop.png",
    fullPage: true,
    animations: "disabled",
  });
  await Promise.all([buyerContext.close(), sellerContext.close()]);
});

test("personal milestones and selected-neighbor interaction survive reload", async ({
  page,
}) => {
  await login(page);
  await page.request.put("/api/me/control", { data: { mode: "manual" } });
  for (let i = 0; i < 2; i++) {
    const before = await page.request.get("/api/world").then((r) => r.json());
    const harvest = before.world.agents.wangjue.progress.metrics.harvested ?? 0;
    await page.getByRole("button", { name: "去农场", exact: true }).click();
    await expect
      .poll(
        async () => {
          const data = await page.request
            .get("/api/world")
            .then((r) => r.json());
          return data.world.agents.wangjue.progress.metrics.harvested ?? 0;
        },
        { timeout: 25000 },
      )
      .toBeGreaterThan(harvest);
  }
  await page
    .getByRole("button", { name: /生活手册/ })
    .first()
    .click();
  await expect(page.getByRole("dialog", { name: "生活手册" })).toBeVisible();
  await expect(
    page.locator(".journal-goals article").filter({ hasText: "第一畦收成" }),
  ).toContainText("已达成");
  await page.keyboard.press("Escape");
  await page
    .locator(".inspector-roster button")
    .filter({ hasText: "李展博" })
    .click();
  const before = await page.request.get("/api/world").then((r) => r.json());
  await page
    .getByRole("button", { name: "前去与李展博交流", exact: true })
    .click();
  await expect
    .poll(
      async () => {
        const data = await page.request.get("/api/world").then((r) => r.json());
        return data.world.agents.wangjue.relations.lizhanbo ?? 0;
      },
      { timeout: 25000 },
    )
    .toBeGreaterThan(before.world.agents.wangjue.relations.lizhanbo ?? 0);
  await expect(page.locator(".resident-relationship")).toContainText("熟悉度");
  await page.reload();
  await expect(page.locator(".phaser-host canvas")).toBeVisible();
  const after = await page.request.get("/api/world").then((r) => r.json());
  expect(after.world.agents.wangjue.progress.badges).toContain("grower");
  expect(after.world.agents.lizhanbo.relations.wangjue).toBeGreaterThan(30);
});
