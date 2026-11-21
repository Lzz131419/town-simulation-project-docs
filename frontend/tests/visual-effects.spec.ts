import { expect, test, type Page } from "@playwright/test";
import { weatherVisuals, workPose } from "../src/game/visual-state";

async function step(page: Page, options: Record<string, unknown> = {}) {
  return page.evaluate(
    (options) => (window as any).visuals.step(options),
    options,
  );
}
async function open(
  page: Page,
  reducedMotion: "reduce" | "no-preference" = "no-preference",
) {
  await page.emulateMedia({ reducedMotion });
  await page.goto("/tests/fixtures/visuals.html");
  await page.waitForFunction(() => Boolean((window as any).visuals));
}

test("weather applies on construction, switches layers, and respects ambience", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await open(page);
  const initial = await page.evaluate(() => (window as any).visuals.snapshot());
  expect(initial.rain.length).toBeGreaterThan(0);
  const sunny = await step(page, { weather: "sunny" });
  expect(sunny.rain).toEqual([]);
  expect(sunny.fog).toBe(false);
  const rain = await step(page, { weather: "rain" });
  expect(rain.rain.length).toBeGreaterThan(0);
  expect(rain.water.length).toBeGreaterThan(sunny.water.length);
  const storm = await step(page, { weather: "storm" });
  expect(storm.rain.length).toBeGreaterThan(rain.rain.length);
  expect(storm.shade).toBeGreaterThan(rain.shade);
  const cloudy = await step(page, { weather: "cloudy" });
  expect(cloudy.rain).toEqual([]);
  expect(cloudy.fog).toBe(true);
  const snowyCloud = await step(page, { season: "winter" });
  expect(snowyCloud.rain.length).toBeGreaterThan(0);
  const snowyRain = await step(page, { weather: "rain" });
  expect(snowyRain.rain).toEqual(snowyCloud.rain);
  const winterStorm = await step(page, { weather: "storm" });
  expect(winterStorm.rain).toEqual(storm.rain);
  const off = await step(page, { ambience: false });
  expect(off.rain).toEqual([]);
  expect(off.water).toEqual([]);
  expect(off.fog).toBe(false);
  expect(off.shade).toBe(0);
  expect((await step(page, { ambience: true })).rain).toEqual(storm.rain);
  expect(errors).toEqual([]);
});

test("season palettes restore exactly and snow stays on a separate roof layer", async ({
  page,
}) => {
  await open(page);
  const summer = await step(page, { season: "summer" });
  const autumn = await step(page, { season: "autumn" });
  expect(autumn.leaf).not.toEqual(summer.leaf);
  expect(autumn.leaf[0]).toBeGreaterThan(autumn.leaf[1]);
  expect(autumn.roof).toBe(false);
  const winter = await step(page, { season: "winter" });
  expect(winter.leaf[0]).toBeGreaterThan(summer.leaf[0]);
  expect(winter.leaf[2]).toBeGreaterThan(summer.leaf[2]);
  expect(winter.roof).toBe(true);
  const spring = await step(page, { season: "spring" });
  expect(spring.leaf).toEqual(summer.leaf);
  expect(spring.roof).toBe(false);
  expect(spring.textures).toBe(summer.textures);
});

test("work poses run only when both server path and interpolation have stopped", async ({
  page,
}) => {
  await open(page);
  const upright = await step(page, { task: "farm", time: 0 });
  const bent = await step(page, { time: 550 });
  expect(bent.avatar.height).toBeLessThan(upright.avatar.height);
  const chop = await step(page, { task: "chop", time: 760 });
  expect(chop.avatar.angle).not.toBe(0);
  const walking = await step(page, { path: [{ x: 200, y: 370 }], time: 1000 });
  expect(walking.avatar.angle).toBe(0);
  expect(walking.avatar.height).toBe(48);
  // Arrival snapshot has no server path, but the local avatar is still catching up.
  const arriving = await step(page, {
    path: [],
    position: { x: 200, y: 370 },
    time: 1200,
  });
  expect(arriving.avatar.angle).toBe(0);
  expect(arriving.avatar.texture).not.toContain("front-0");
  for (let i = 0; i < 100; i++) await step(page, { time: 1300 + i * 16 });
  const fishing = await step(page, { task: "fish", time: 3000 });
  expect(fishing.avatar.angle).toBe(0);
  const reel = await step(page, { time: 5250 });
  expect(reel.avatar.angle).not.toBe(0);
  const idle = await step(page, { task: null, time: 5400 });
  expect(idle.avatar.angle).toBe(0);
  expect(idle.avatar.x).toBe(0);
  expect(idle.avatar.height).toBe(48);
});

test("reduced motion freezes precipitation and disables work movement", async ({
  page,
}) => {
  await open(page, "reduce");
  const a = await step(page, {
    season: "winter",
    weather: "cloudy",
    time: 1000,
  });
  const b = await step(page, { time: 3000 });
  expect(a.rain.length).toBeGreaterThan(0);
  expect(a.rain).toEqual(b.rain);
  expect(a.avatar).toEqual(b.avatar);
  expect(weatherVisuals({ weather: "rain" }, true, true).count).toBe(
    weatherVisuals({ weather: "rain" }, true, false).count / 2,
  );
});

test("all requested task aliases have two poses; unsupported tasks stay still", () => {
  for (const task of [
    "farm",
    "harvest_veg",
    "harvest_flax",
    "gather",
    "gather_honey",
    "forage",
  ])
    expect(workPose(task, 550).height).toBeLessThan(workPose(task, 0).height);
  for (const task of ["chop", "craft"])
    expect(workPose(task, 380).angle).not.toBe(workPose(task, 0).angle);
  expect(workPose("rest", 550)).toEqual(workPose(undefined, 0));
  expect(weatherVisuals({}, true, false).precipitation).toBe("none");
});

test("market day props appear immediately, last all day, and expire without rebaking", async ({
  page,
}) => {
  await open(page);
  const before = await step(page, {
    weather: "sunny",
    season: "summer",
    tick: 1103,
  });
  expect(before.stalls).toEqual([false, false, false, false]);
  const fair = await step(page, {
    tick: 1152,
    market_day: { until_tick: 1248 },
  });
  expect(fair.stalls).toEqual([true, true, true, true]);
  expect(fair.textures).toBe(before.textures);
  await page.evaluate(() => (window as any).visuals.focusMarket());
  await page.waitForTimeout(400);
  await page
    .locator("canvas")
    .screenshot({ path: "test-results/t10-market-day-stalls.png" });
  expect((await step(page, { tick: 1247, ambience: false })).stalls).toEqual(
    fair.stalls,
  );
  expect((await step(page, { tick: 1248 })).stalls).toEqual(before.stalls);
  expect((await step(page, { market_day: {} })).textures).toBe(before.textures);
});

test("sleep fades avatars, lights occupied houses at night, and waking restores them", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await open(page);
  const awake = await step(page, {
    tick: 84,
    weather: "sunny",
    task: null,
    time: 2000,
  });
  expect(awake.homeLights).toEqual([0, 0, 0, 0, 0, 0, 0]);
  expect(awake.sleepingAlpha).toBe(1);
  const fading = await step(page, {
    sleeping: { since_tick: 84, phase: "light" },
    time: 2100,
  });
  expect(fading.sleepingAlpha).toBeGreaterThan(0);
  expect(fading.sleepingAlpha).toBeLessThan(1);
  expect(fading.sleepingInteractive).toBe(false);
  expect(fading.homeLights).toEqual([1, 0, 0, 0, 0, 0, 0]);
  for (let i = 0; i < 70; i++) await step(page, { time: 2200 + i * 50 });
  const sleeping = await step(page, { time: 6000 });
  expect(sleeping.sleepingAlpha).toBe(0);
  expect(sleeping.textures).toBe(awake.textures);
  await page.evaluate(() => (window as any).visuals.focusHomes());
  await page.waitForTimeout(200);
  await page
    .locator("canvas")
    .screenshot({ path: "../.local/t12-sleep/night-homes.png" });
  expect((await step(page, { tick: 228 })).homeLights).toEqual([
    1, 0, 0, 0, 0, 0, 0,
  ]);
  expect((await step(page, { ambience: false })).homeLights).toEqual(
    awake.homeLights,
  );
  expect((await step(page, { ambience: true, tick: 24 })).homeLights).toEqual(
    awake.homeLights,
  );
  await step(page, { tick: 84, sleeping: null, time: 6100 });
  for (let i = 0; i < 30; i++) await step(page, { time: 6200 + i * 20 });
  const restored = await step(page, { time: 7000 });
  expect(restored.sleepingAlpha).toBe(1);
  expect(restored.sleepingInteractive).toBe(true);
  expect(restored.homeLights).toEqual(awake.homeLights);
  expect(errors).toEqual([]);
});

test("reduced motion hides sleeping residents immediately", async ({
  page,
}) => {
  await open(page, "reduce");
  const asleep = await step(page, {
    sleeping: { since_tick: 84, phase: "deep" },
    tick: 84,
  });
  expect(asleep.sleepingAlpha).toBe(0);
  expect(asleep.sleepingInteractive).toBe(false);
  expect((await step(page, { sleeping: null })).sleepingAlpha).toBe(1);
});

test("leisure shows activity, two play hops and occasional daydream thoughts", async ({
  page,
}) => {
  await open(page);
  const low = await step(page, {
    task: "play",
    activity: "在广场玩耍",
    time: 0,
  });
  const hop = await step(page, { time: 260 });
  expect(hop.avatar.y).toBeLessThan(low.avatar.y);
  expect(hop.activity).toBe("在广场玩耍");
  const quiet = await step(page, {
    task: "daydream",
    activity: "看着河水发呆",
    time: 0,
  });
  expect(quiet.thought).toBe(true);
  expect(quiet.avatar.y).toBe(0);
  expect(quiet.activity).toBe("看着河水发呆");
  expect((await step(page, { time: 2000 })).thought).toBe(false);
  const visit = await step(page, {
    task: "visit",
    activity: "串门",
    time: 2500,
  });
  expect(visit.avatar.y).toBe(0);
  expect(visit.thought).toBe(false);
  const stroll = await step(page, {
    task: "stroll",
    path: [{ x: 220, y: 370 }],
  });
  expect(stroll.activity).toBe("↗ 散步");
  await step(page, { position: { x: 220, y: 370 }, path: [], time: 1300 });
  const moving = await step(page, { time: 1316 });
  expect(moving.avatar.texture).not.toContain("front-0");
});

test("reduced motion keeps leisure static and thought readable", async ({
  page,
}) => {
  await open(page, "reduce");
  expect((await step(page, { task: "play", time: 260 })).avatar.y).toBe(0);
  const quiet = await step(page, { task: "daydream", time: 2000 });
  expect(quiet.avatar.y).toBe(0);
  expect(quiet.thought).toBe(true);
});
