import { test, expect } from "./fixtures/live-test";
import { applyPacket, type Snapshot } from "../src/realtime/protocol";
import { api, ApiError } from "../src/api";

async function login(page: any) {
  await page.goto("/");
  await page.locator("[name=username]").fill("wangjue");
  await page.locator("[name=password]").fill("wangjue");
  await page.getByRole("button", { name: "进入雾河镇" }).click();
  await expect(page.locator(".world-live")).toContainText("共享世界已连接");
  const resume = page.getByRole("button", {
    name: "继续我的生活",
    exact: true,
  });
  if (await resume.isVisible()) await resume.click();
}

test("patch validates continuity and schema without damaging current state", async ({
  request,
}) => {
  await request.post("/api/auth/login", {
    data: { username: "wangjue", password: "wangjue" },
  });
  const current: Snapshot = await request
    .get("/api/world")
    .then((r) => r.json());
  const patch = {
    type: "patch",
    revision: current.revision + 1,
    base_revision: current.revision,
    set: { tick: current.world.tick + 1 },
    agents: {},
    removed_agents: [],
    events: [],
  };
  const next = applyPacket(current, patch)!;
  expect(next.world.tick).toBe(current.world.tick + 1);
  expect(applyPacket(next, current)).toBe(next);
  expect(() => applyPacket(current, { ...patch, base_revision: -1 })).toThrow(
    "世界版本不连续",
  );
  expect(() =>
    applyPacket(current, {
      ...patch,
      agents: { wangjue: { id: "wangjue", x: "bad" } },
    }),
  ).toThrow();
  expect(() =>
    applyPacket(current, { ...patch, set: { agents: {} } }),
  ).toThrow();
  expect(() =>
    applyPacket(current, { ...patch, set: { orders: [null] } }),
  ).toThrow();
  expect(() =>
    applyPacket(current, { ...patch, set: { project: {} } }),
  ).toThrow();
  const supply = { completed: 1, goods: { furniture: 1 } };
  expect(
    applyPacket(current, { ...patch, set: { supply } })!.world.supply,
  ).toEqual(supply);
  expect(() =>
    applyPacket(current, {
      ...patch,
      set: { supply: { completed: -1, goods: {} } },
    }),
  ).toThrow();
  expect(() =>
    applyPacket(current, {
      ...patch,
      agents: {
        lizhanbo: {
          ...current.world.agents.lizhanbo,
          delivery_log: { day: 1, items: null },
        },
      },
    }),
  ).toThrow();
  expect(current.world.agents.wangjue).toBeDefined();
});

test("request timeout covers response body and never retries mutations", async () => {
  const original = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async (_input, init) => {
    calls++;
    return {
      ok: true,
      status: 200,
      json: () =>
        new Promise((_resolve, reject) => {
          init?.signal?.addEventListener(
            "abort",
            () => reject(Error("aborted")),
            { once: true },
          );
        }),
    } as Response;
  };
  try {
    await expect(
      api("/test", "POST", {}, { timeoutMs: 20 }),
    ).rejects.toMatchObject({ code: "timeout" });
    expect(calls).toBe(1);
    globalThis.fetch = async () => new Response("bad-json", { status: 200 });
    await expect(api("/test")).rejects.toBeInstanceOf(ApiError);
  } finally {
    globalThis.fetch = original;
  }
});

test("startup failure and stalled server offer a working retry", async ({
  page,
}) => {
  await page.route("**/api/me", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ detail: "小镇服务暂不可用" }),
    }),
  );
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "暂时连接不上小镇" }),
  ).toBeVisible();
  await page.unroute("**/api/me");
  await page.getByRole("button", { name: "重新连接" }).click();
  await expect(page.locator(".login-card")).toBeVisible();
  await page.route("**/api/me", () => {});
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "暂时连接不上小镇" }),
  ).toBeVisible({ timeout: 16000 });
  await expect(page.locator(".connection-error")).toContainText("连接超时");
});

test("broken websocket reconnects and resyncs after a malformed packet", async ({
  page,
}) => {
  const packets: any[] = [];
  let connections = 0;
  let disconnect: (() => void) | undefined;
  await page.routeWebSocket("**/api/ws*", (socket) => {
    connections++;
    const server = socket.connectToServer();
    disconnect = () => {
      socket.close({ code: 1012, reason: "test restart" });
      server.close();
    };
    let corrupted = false;
    server.onMessage((message) => {
      const packet = JSON.parse(String(message));
      packets.push(packet);
      if (!corrupted) {
        corrupted = true;
        socket.send("{malformed");
      } else socket.send(message);
    });
  });
  await login(page);
  await expect
    .poll(() => packets.filter((p) => p.type === "world").length)
    .toBeGreaterThan(1);
  await expect.poll(() => packets.some((p) => p.type === "patch")).toBeTruthy();
  disconnect!();
  await expect.poll(() => connections, { timeout: 10000 }).toBeGreaterThan(1);
  await expect(page.locator(".world-live")).toContainText("共享世界已连接", {
    timeout: 35000,
  });
});

test("economic charts show real samples at both desktop sizes", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await login(page);
  // Fresh isolated worlds need two real scheduler samples before drawing a trend.
  await expect
    .poll(
      async () => {
        const report = await page.request
          .get("/api/report")
          .then((r) => r.json());
        return report.series.length;
      },
      { timeout: 15000 },
    )
    .toBeGreaterThan(1);
  await page
    .locator("nav")
    .getByRole("button", { name: "生活记录", exact: true })
    .click();
  // T7 defaults to daily turnover; this assertion exercises sampled treasury.
  await page.getByLabel("趋势指标").selectOption("treasury");
  await expect(page.locator(".trend-chart svg")).toBeVisible();
  await expect(page.locator(".fiscal-note")).toContainText("5%");
  const report = await page.request.get("/api/report").then((r) => r.json());
  expect(report.series.length).toBeGreaterThan(1);
  await expect(page.locator(".chart-readout strong")).toContainText(
    String(report.series.at(-1).treasury),
  );
  await page.getByLabel("趋势指标").selectOption("trades");
  await expect(page.locator(".chart-readout strong")).toContainText("笔");
  for (const width of [1440, 1280]) {
    await page.setViewportSize({ width, height: width === 1440 ? 900 : 720 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    await page.screenshot({
      path: `test-results/review-report-${width}.png`,
      fullPage: true,
    });
  }
  await page.locator(".resource-chart").scrollIntoViewIfNeeded();
  await expect(page.locator(".resource-chart")).toBeVisible();
  await page.screenshot({
    path: "test-results/review-report-detail.png",
  });
  expect(errors).toEqual([]);
});
