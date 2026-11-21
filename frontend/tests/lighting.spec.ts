import { test, expect, type Page } from "./fixtures/live-test";
import { daylight } from "../src/game/lighting";

test("lighting is continuous across dawn, dusk and midnight", () => {
  expect(daylight(24)).toEqual({ night: 0, warmth: 0, lamps: 0 });
  expect(daylight(84)).toEqual({ night: 0.34, warmth: 0, lamps: 1 });
  expect(daylight(60).warmth).toBeGreaterThan(0.1);
  for (let tick = 0; tick < 144; tick++) {
    const a = daylight(tick),
      b = daylight(tick + 0.001);
    for (const k of ["night", "warmth", "lamps"] as const) {
      expect(a[k]).toBeGreaterThanOrEqual(0);
      expect(a[k]).toBeLessThanOrEqual(1);
      expect(Math.abs(a[k] - b[k])).toBeLessThan(0.001);
      expect(daylight(tick + 144)[k]).toBeCloseTo(a[k], 8);
    }
  }
});

async function luminance(page: Page) {
  return page.locator(".phaser-host canvas").evaluate((element) => {
    const canvas = element as HTMLCanvasElement;
    const c = canvas.getContext("2d")!;
    let total = 0,
      count = 0;
    for (let y = 0.1; y < 0.95; y += 0.04)
      for (let x = 0.1; x < 0.95; x += 0.04) {
        const p = c.getImageData(
          Math.floor(canvas.width * x),
          Math.floor(canvas.height * y),
          1,
          1,
        ).data;
        total += 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2];
        count++;
      }
    return total / count;
  });
}

test("night actually shades rendered pixels and ambience toggle restores daylight", async ({
  page,
}) => {
  let tick = 24;
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  // Time is a display fixture; API actions and the saved server clock are untouched.
  await page.route("**/api/world", async (route) => {
    const response = await route.fetch(),
      body = await response.json();
    body.world.tick = tick;
    await route.fulfill({ response, json: body });
  });
  await page.routeWebSocket("**/api/ws?protocol=2", (ws) => {
    const server = ws.connectToServer();
    server.onMessage((raw) => {
      const p = JSON.parse(String(raw));
      if (p.world) p.world.tick = tick;
      if (p.set) p.set.tick = tick;
      ws.send(JSON.stringify(p));
    });
  });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await page.locator("[name=username]").fill("zhangguo");
  await page.locator("[name=password]").fill("zhangguo");
  await page.getByRole("button", { name: "进入雾河镇", exact: true }).click();
  await expect(page.locator(".world-live")).toContainText("共享世界已连接");
  const resume = page.getByRole("button", {
    name: "继续我的生活",
    exact: true,
  });
  if (await resume.isVisible()) await resume.click();
  await expect(page.locator(".map-loading")).toHaveCount(0);
  await expect.poll(() => luminance(page)).toBeGreaterThan(90);
  const day = await luminance(page);
  tick = 84;
  await expect(page.locator(".map-world-state")).toContainText("夜晚");
  await expect.poll(() => luminance(page)).toBeLessThan(day * 0.85);
  expect(await luminance(page)).toBeGreaterThan(day * 0.5);
  await page.getByTitle("画面图层", { exact: true }).click();
  await page.getByLabel("昼夜与环境动态").uncheck();
  await expect
    .poll(async () => Math.abs((await luminance(page)) - day))
    .toBeLessThan(4);
  expect(errors).toEqual([]);
});
