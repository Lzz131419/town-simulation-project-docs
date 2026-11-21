import { expect, test, type Page, type WebSocketRoute } from "@playwright/test";
import {
  defaultAudioSettings,
  environmentFor,
  soundForEvent,
} from "../src/game/audio";
import type { Town, TownEvent } from "../src/types";

const event = (
  id: number,
  type: string,
  actor_id = "wangjue",
  details = {},
): TownEvent => ({
  id,
  tick: 1,
  actor_id,
  type,
  text: `${type}-${id}`,
  details,
});
const world: Town = {
  schema_version: 1,
  tick: 0,
  weather: "rain",
  season: "summer",
  agents: {
    wangjue: {
      id: "wangjue",
      name: "王珏",
      npc: false,
      online: true,
      x: 180,
      y: 370,
      cash: 50,
      energy: 100,
      hunger: 0,
      inventory: {},
      mode: "manual",
      path: [],
      task: null,
      activity: "休息",
      completed: 0,
      earned: 0,
      relations: {},
      last_outcome: "",
      policy: {
        reserve: 0,
        daily_budget: 0,
        fallback: "rest",
        auto_eat: false,
      },
    },
  },
  market: {},
  treasury: 0,
  orders: [],
  project: {
    name: "仓库",
    wood: 0,
    wood_target: 10,
    cash: 0,
    cash_target: 10,
    completed: false,
    contributors: {},
  },
  activity_goal: { name: "交易", trades: 0, target: 10 },
};

async function open(page: Page, reduced = false) {
  await page.emulateMedia({
    reducedMotion: reduced ? "reduce" : "no-preference",
  });
  await page.addInitScript(() => {
    const log = {
      contexts: 0,
      resumes: 0,
      closed: 0,
      starts: [] as any[],
      ramps: [] as any[],
      nodes: [] as any[],
    };
    (window as any).audioLog = log;
    class Param {
      value = 0;
      constructor(public label: string) {}
      setValueAtTime(value: number) {
        this.value = value;
      }
      cancelScheduledValues() {}
      cancelAndHoldAtTime() {}
      linearRampToValueAtTime(value: number, at: number) {
        this.value = value;
        log.ramps.push({ label: this.label, value, at });
      }
      exponentialRampToValueAtTime(value: number, at: number) {
        this.value = value;
        log.ramps.push({ label: this.label, value, at });
      }
    }
    class Node {
      gain = new Param("gain");
      frequency = new Param("frequency");
      Q = new Param("Q");
      buffer: any;
      loop = false;
      type = "sine";
      disconnected = false;
      onended?: () => void;
      constructor(public kind: string) {
        log.nodes.push(this);
      }
      connect() {}
      disconnect() {
        this.disconnected = true;
      }
      start(at = 0) {
        log.starts.push({
          kind: this.kind,
          hz: this.frequency.value,
          loop: this.loop,
          at,
        });
      }
      stop(at?: number) {
        if (at === undefined) this.onended?.();
      }
    }
    class Context {
      state = "suspended";
      sampleRate = 8000;
      destination = new Node("destination");
      get currentTime() {
        return performance.now() / 1000;
      }
      constructor() {
        log.contexts++;
      }
      createGain() {
        return new Node("gain");
      }
      createOscillator() {
        return new Node("oscillator");
      }
      createBiquadFilter() {
        return new Node("filter");
      }
      createBufferSource() {
        return new Node("buffer");
      }
      createBuffer(_channels: number, length: number) {
        return { getChannelData: () => new Float32Array(length) };
      }
      async resume() {
        log.resumes++;
        this.state = "running";
      }
      async suspend() {
        this.state = "suspended";
      }
      async close() {
        log.closed++;
        this.state = "closed";
      }
    }
    (window as any).AudioContext = Context;
  });
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    const payload =
      path === "/api/me"
        ? { id: "wangjue", name: "王珏", bio: "", goal: "" }
        : path === "/api/world"
          ? { type: "world", revision: 1, world, events: [event(10, "farm")] }
          : path === "/api/catalog"
            ? {
                items: {},
                places: {},
                actions: {},
                members: [],
                tick_seconds: 2,
              }
            : path === "/api/return-summary"
              ? null
              : {};
    await route.fulfill({ json: payload });
  });
  let socket: WebSocketRoute | undefined;
  await page.routeWebSocket("**/api/ws?protocol=2", (ws) => {
    socket = ws;
  });
  await page.goto("/tests/fixtures/audio.html");
  await expect(page.getByTitle("画面图层")).toBeVisible();
  await expect.poll(() => Boolean(socket)).toBe(true);
  let revision = 1;
  return {
    patch: async (events: TownEvent[], set: Record<string, unknown> = {}) => {
      socket!.send(
        JSON.stringify({
          type: "patch",
          base_revision: revision,
          revision: ++revision,
          set,
          agents: {},
          removed_agents: [],
          events,
        }),
      );
      await expect
        .poll(async () =>
          page.evaluate(() => (window as any).audioHarness != null),
        )
        .toBe(true);
    },
    snapshot: (events: TownEvent[]) =>
      socket!.send(
        JSON.stringify({ type: "world", revision: ++revision, world, events }),
      ),
  };
}
const calls = (page: Page) =>
  page.evaluate(() => (window as any).audioHarness.calls as string[]);
const starts = (page: Page) =>
  page.evaluate(() => (window as any).audioLog.starts as any[]);

for (const [kind, types] of Object.entries({
  harvest:
    "farm harvest_veg gather gather_honey harvest_flax forage mine chop fish",
  make: "bake weave assemble forge craft cook grill brew",
  coin: "buy sell",
  delivery: "delivery",
  eat: "eat eat_meal eat_fruit eat_fish",
  social: "social gift feast",
  sleep: "sleep wake",
  blocked: "blocked failed failure",
}))
  test(`pure timbres: ${kind} aliases and bounded envelopes`, () => {
    for (const type of types.split(" ")) {
      const sound = soundForEvent({ type });
      expect(sound?.kind).toBe(kind);
      for (const voice of sound!.voices) {
        expect(voice.duration).toBeGreaterThan(0.006);
        expect(voice.duration + voice.delay).toBeLessThan(0.5);
        expect(voice.gain).toBeLessThanOrEqual(0.2);
        expect(voice.hz).toBeGreaterThanOrEqual(65);
        expect(voice.hz).toBeLessThan(2400);
      }
    }
  });

test("orders only sound on settlement; environment follows weather and daylight", () => {
  for (const transaction_type of ["posted", "cancelled", undefined])
    expect(
      soundForEvent({ type: "order", details: { transaction_type } }),
    ).toBeNull();
  expect(
    soundForEvent({ type: "order", details: { transaction_type: "filled" } })
      ?.kind,
  ).toBe("coin");
  expect(soundForEvent({ type: "move" })).toBeNull();
  const settings = defaultAudioSettings(false);
  const rain = environmentFor(world, settings);
  expect(
    environmentFor({ ...world, weather: "storm" }, settings).rain,
  ).toBeGreaterThan(rain.rain);
  expect(
    environmentFor({ ...world, weather: "cloudy" }, settings).wind,
  ).toBeGreaterThan(0);
  expect(
    environmentFor({ ...world, tick: 72 }, settings).crickets,
  ).toBeGreaterThan(0);
  const winter = environmentFor(
    { ...world, tick: 72, season: "winter" },
    settings,
  );
  expect(winter.windHz).toBeGreaterThan(rain.windHz);
  expect(winter.crickets).toBe(0);
  for (const off of [
    { enabled: false },
    { ambience: false },
    { environment: false },
  ]) {
    const env = environmentFor(world, { ...settings, ...off });
    expect([env.rain, env.wind, env.crickets]).toEqual([0, 0, 0]);
  }
  expect(defaultAudioSettings(true).environment).toBe(false);
});

test("real store packets: lazy context, history/dedupe/player filter and all sound families", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const stream = await open(page);
  expect(await calls(page)).toEqual([]);
  expect(await page.evaluate(() => (window as any).audioLog.contexts)).toBe(0);
  await stream.patch([event(11, "farm")]);
  await expect.poll(() => calls(page)).toEqual(["harvest"]);
  expect(await starts(page)).toEqual([]); // locked events are consumed without backlog
  await page.getByTitle("画面图层").click();
  expect(await page.evaluate(() => (window as any).audioLog.contexts)).toBe(1);
  expect(await page.evaluate(() => (window as any).audioLog.resumes)).toBe(1);
  expect(
    (await starts(page)).filter((n) => n.kind === "oscillator"),
  ).toHaveLength(0);
  await stream.patch([
    event(11, "farm"),
    event(12, "farm", "npc"),
    event(13, "order", "wangjue", { transaction_type: "posted" }),
  ]);
  const types = [
    "farm",
    "forge",
    "sell",
    "delivery",
    "eat_fruit",
    "gift",
    "sleep",
    "wake",
    "blocked",
  ];
  const expected = ["harvest"];
  for (let i = 0; i < types.length; i++) {
    await stream.patch([event(20 + i, types[i])]);
    expected.push(soundForEvent({ type: types[i] })!.kind);
    await expect.poll(() => calls(page)).toEqual(expected);
    await page.waitForTimeout(190); // let the bounded cue scheduler advance
  }
  expect(
    (await starts(page)).filter((n) => n.kind === "oscillator").length,
  ).toBeGreaterThan(9);
  stream.snapshot([event(26, "blocked"), event(25, "gift")]);
  await page.waitForTimeout(100);
  expect(await calls(page)).toEqual(expected);
  await page.evaluate(() => (window as any).audioHarness.dispose());
  expect(await page.evaluate(() => (window as any).audioLog.closed)).toBe(1);
  expect(
    await page.evaluate(() =>
      (window as any).audioLog.nodes
        .filter((n: any) => n.kind !== "destination")
        .every((n: any) => n.disconnected),
    ),
  ).toBe(true);
  expect(errors).toEqual([]);
});

test("settings persist; mute suppresses sources; ambience only gates environmental audio", async ({
  page,
}) => {
  const stream = await open(page);
  await page.getByTitle("画面图层").click();
  await page.getByLabel("环境音", { exact: true }).uncheck();
  await page.getByLabel("昼夜与环境动态", { exact: true }).uncheck();
  await stream.patch([event(11, "farm")]);
  await expect
    .poll(
      async () =>
        (await starts(page)).filter((n) => n.kind === "oscillator").length,
    )
    .toBe(1);
  await page.getByLabel("声音", { exact: true }).uncheck();
  const count = (await starts(page)).length;
  await stream.patch([event(12, "forge")]);
  await expect.poll(() => calls(page)).toEqual(["harvest", "make"]);
  expect((await starts(page)).length).toBe(count);
  await page.getByLabel("音量", { exact: true }).fill("0.6");
  const saved = await page.evaluate(() =>
    JSON.parse(localStorage.getItem("mist-river-audio-v1")!),
  );
  expect(saved).toEqual({
    enabled: false,
    volume: 0.6,
    environment: false,
    ambience: false,
  });
  await page.reload();
  await page.getByTitle("画面图层").click();
  await expect(page.getByLabel("声音", { exact: true })).not.toBeChecked();
  await expect(page.getByLabel("音量", { exact: true })).toHaveValue("0.6");
  expect(await page.evaluate(() => (window as any).audioLog.contexts)).toBe(0);
});

test("weather changes ramp gains and filters, night chirps, reduced preference defaults off", async ({
  page,
}) => {
  const stream = await open(page, true);
  await page.getByTitle("画面图层").click();
  await expect(page.getByLabel("环境音", { exact: true })).not.toBeChecked();
  expect(
    await page.evaluate(() =>
      (window as any).audioLog.ramps.some((r: any) => r.value === 0.055),
    ),
  ).toBe(false);
  await page.getByLabel("环境音", { exact: true }).check();
  await expect
    .poll(() =>
      page.evaluate(() =>
        (window as any).audioLog.ramps.some((r: any) => r.value === 0.055),
      ),
    )
    .toBe(true);
  await stream.patch([], { weather: "storm", tick: 72 });
  await expect
    .poll(() =>
      page.evaluate(() =>
        (window as any).audioLog.ramps.some((r: any) => r.value === 0.1),
      ),
    )
    .toBe(true);
  await expect
    .poll(async () =>
      (await starts(page)).some(
        (n) => n.kind === "oscillator" && n.hz === 4100,
      ),
    )
    .toBe(true);
  await stream.patch([], { weather: "cloudy", season: "winter" });
  await expect
    .poll(() =>
      page.evaluate(() =>
        (window as any).audioLog.ramps.some(
          (r: any) => r.label === "frequency" && r.value === 1100,
        ),
      ),
    )
    .toBe(true);
  await page.getByLabel("昼夜与环境动态", { exact: true }).uncheck();
  const before = (await starts(page)).length;
  await page.waitForTimeout(1800);
  expect((await starts(page)).length).toBe(before);
});

test("autoplay resume rejection retries, zero volume stays silent, controls fit the supported minimum width", async ({
  page,
}) => {
  const stream = await open(page);
  await page.evaluate(() => {
    const prototype = (window as any).AudioContext.prototype;
    const resume = prototype.resume;
    let first = true;
    prototype.resume = function () {
      if (first) {
        first = false;
        return Promise.reject(new Error("autoplay denied"));
      }
      return resume.call(this);
    };
  });
  // pointerdown is denied; click is another user gesture and retries the same context.
  await page.getByTitle("画面图层").click();
  expect(await page.evaluate(() => (window as any).audioLog.contexts)).toBe(1);
  expect(await page.evaluate(() => (window as any).audioLog.resumes)).toBe(1);
  await page.getByLabel("音量", { exact: true }).fill("0");
  const count = (await starts(page)).length;
  await stream.patch([event(11, "farm")]);
  await expect.poll(() => calls(page)).toEqual(["harvest"]);
  expect((await starts(page)).length).toBe(count);
  await page.setViewportSize({ width: 1120, height: 844 });
  const panel = await page.locator(".map-layer-menu").boundingBox();
  const slider = await page.getByLabel("音量", { exact: true }).boundingBox();
  expect(slider!.x).toBeGreaterThanOrEqual(panel!.x);
  expect(slider!.x + slider!.width).toBeLessThanOrEqual(
    panel!.x + panel!.width,
  );
  expect(panel!.x).toBeGreaterThanOrEqual(0);
  expect(panel!.x + panel!.width).toBeLessThanOrEqual(1120);
  await page.screenshot({ path: "test-results/t9-audio-settings.png" });
});

test("unavailable WebAudio does not break incoming events or the UI", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const stream = await open(page);
  await page.evaluate(() => {
    (window as any).AudioContext = class {
      constructor() {
        throw Error("unsupported");
      }
    };
  });
  await page.getByTitle("画面图层").click();
  await stream.patch([event(11, "farm")]);
  await expect.poll(() => calls(page)).toEqual(["harvest"]);
  await expect(page.getByLabel("声音", { exact: true })).toBeChecked();
  expect(errors).toEqual([]);
});

test("market ambience is daytime-only and uses the same mute/environment gates", () => {
  const settings = defaultAudioSettings(false);
  const fair = { ...world, tick: 1152, market_day: { until_tick: 1248 } };
  expect(environmentFor(fair, settings).market).toBe(0.018);
  for (const tick of [1104, 1224, 1248])
    expect(environmentFor({ ...fair, tick }, settings).market).toBe(0);
  for (const off of [
    { enabled: false },
    { environment: false },
    { ambience: false },
  ])
    expect(environmentFor(fair, { ...settings, ...off }).market).toBe(0);
});

test("live market patches toggle chip, murmur and occasional chime, then expire", async ({
  page,
}) => {
  const stream = await open(page);
  await page.getByTitle("画面图层").click();
  await stream.patch([], { tick: 1152, market_day: { until_tick: 1248 } });
  await expect(page.locator(".market-day-chip")).toHaveText("集市日");
  await expect
    .poll(() =>
      page.evaluate(() =>
        (window as any).audioLog.ramps.some((r: any) => r.value === 0.018),
      ),
    )
    .toBe(true);
  await expect
    .poll(async () =>
      (await starts(page)).some(
        (n) => n.kind === "oscillator" && n.hz === 1568,
      ),
    )
    .toBe(true);
  await stream.patch([], { tick: 1248, market_day: {} });
  await expect(page.locator(".market-day-chip")).toHaveCount(0);
  const count = (await starts(page)).filter((n) => n.hz === 1568).length;
  await page.waitForTimeout(1800);
  expect((await starts(page)).filter((n) => n.hz === 1568)).toHaveLength(count);
});
