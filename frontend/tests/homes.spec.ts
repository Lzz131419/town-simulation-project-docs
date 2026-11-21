import { expect, test } from "@playwright/test";

test("three home levels render together, upgrades flash, and only an owner's sleeping home lights", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/tests/fixtures/visuals.html");
  await page.waitForFunction(() => Boolean((window as any).visuals));
  const homes = [1, 2, 3, 4, 5, 6, 7].map((i) => ({
    id: `home-${i}`,
    x: 0,
    y: 0,
    level: i <= 3 ? i : 1,
    owner_id: i === 2 ? "worker" : null,
  }));
  const step = (options: any) =>
    page.evaluate((o) => (window as any).visuals.step(o), options);
  const initial = await step({
    homes,
    names: true,
    home_id: "home-2",
    weather: "sunny",
    tick: 24,
    time: 1000,
  });
  expect(initial.homeArt[0]).toEqual([]);
  expect(initial.homeArt[1].length).toBeGreaterThan(0);
  expect(initial.homeArt[2].length).toBeGreaterThan(initial.homeArt[1].length);
  expect(initial.homeFlash).toBe(1);
  const stable = await step({ time: 2000 });
  expect(stable.homeFlash).toBe(0);
  await page.evaluate(() => (window as any).visuals.focusHomes());
  await page.waitForTimeout(250);
  await page
    .locator("canvas")
    .screenshot({ path: "../.local/t13-homes/three-level-homes.png" });
  const night = await step({
    tick: 84,
    sleeping: { since_tick: 84, phase: "deep" },
  });
  expect(night.homeLights).toEqual([0, 1, 0, 0, 0, 0, 0]);
  expect((await step({ tick: 228 })).homeLights).toEqual(night.homeLights);
  const bench = await step({ home_id: null });
  expect(bench.homeLights).toEqual([0, 0, 0, 0, 0, 0, 0]);
  expect(bench.textures).toBe(initial.textures);
  expect(errors).toEqual([]);
});

test("home upgrades arrive through world deltas and invalid levels reject atomically", async () => {
  const { applyPacket } = await import("../src/realtime/protocol");
  const before = {
    type: "world" as const,
    revision: 1,
    events: [],
    world: {
      schema_version: 2,
      tick: 0,
      agents: {},
      market: {},
      treasury: 0,
      orders: [],
      project: {
        name: "",
        wood: 0,
        wood_target: 0,
        cash: 0,
        cash_target: 0,
        completed: false,
        contributors: {},
      },
      activity_goal: { name: "", trades: 0, target: 0 },
      homes: [{ id: "home-1", x: 223.5, y: 103.5, owner_id: null, level: 1 }],
    },
  };
  const home = { ...before.world.homes[0], level: 2 };
  const patch = {
    type: "patch",
    revision: 2,
    base_revision: 1,
    events: [],
    agents: {},
    removed_agents: [],
    set: { homes: [home] },
  };
  expect(applyPacket(before, patch).world.homes[0].level).toBe(2);
  expect(() =>
    applyPacket(before, { ...patch, set: { homes: [{ ...home, level: 4 }] } }),
  ).toThrow("无效增量世界");
  expect(before.world.homes[0].level).toBe(1);
});
