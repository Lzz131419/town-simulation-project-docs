import { expect, test, type WebSocketRoute } from "@playwright/test";
import { applyPacket, type Snapshot } from "../src/realtime/protocol";
import { soundForEvent, TownAudio, type Sound } from "../src/game/audio";
import type { Town, TownEvent } from "../src/types";

const resident = (id: string, name: string, npc = true) => ({
  id,
  name,
  npc,
  online: false,
  x: 325,
  y: 520,
  cash: 80,
  energy: 85,
  hunger: 20,
  inventory: {},
  mode: "manual",
  path: [],
  task: null,
  activity: "在家",
  completed: 0,
  earned: 0,
  relations: { "npc-2": 65, "npc-5": 30 },
  last_outcome: "",
  policy: { reserve: 20, daily_budget: 20, fallback: "work", auto_eat: true },
});
const world: Town = {
  schema_version: 2,
  tick: 10,
  agents: {
    wangjue: resident("wangjue", "王崛", false),
    "npc-2": {
      ...resident("npc-2", "陈禾"),
      family: { group: "a", kin: "spouse" },
      home_id: "home-1",
    },
    "npc-5": {
      ...resident("npc-5", "苏晴"),
      family: { group: "a", kin: "spouse" },
      home_id: "home-1",
    },
  },
  homes: [{ id: "home-1", x: 223.5, y: 103.5, owner_id: "npc-2", level: 1 }],
  market: {},
  treasury: 2000,
  orders: [],
  project: {
    name: "共享仓库",
    wood: 0,
    wood_target: 40,
    cash: 0,
    cash_target: 400,
    contributors: {},
    completed: false,
  },
  activity_goal: { name: "集市", target: 20, trades: 0 },
  family_state: { groups: {}, invitations: {} },
};
const invite = {
  group: "a",
  host_id: "npc-2",
  guest_id: "wangjue",
  home_id: "home-1",
  issued_tick: 10,
  expires_tick: 58,
  status: "pending" as const,
};
const before: Snapshot = { type: "world", revision: 1, world, events: [] };
const packet = {
  type: "patch",
  base_revision: 1,
  revision: 2,
  set: { family_state: { groups: {}, invitations: { "a:wangjue": invite } } },
  agents: {},
  removed_agents: [],
  events: [],
};

test("invitations survive incremental sync; malformed state is rejected atomically", () => {
  expect(
    applyPacket(before, packet)!.world.family_state?.invitations["a:wangjue"],
  ).toEqual(invite);
  expect(() =>
    applyPacket(before, {
      ...packet,
      set: {
        family_state: {
          groups: {},
          invitations: { bad: { ...invite, expires_tick: -1 } },
        },
      },
    }),
  ).toThrow();
  expect(before.world.family_state?.invitations).toEqual({});
});

test("family sounds differ and NPC events obey dedupe and history suppression", () => {
  const sounds = ["meal", "quarrel", "reconcile"].map((kind) =>
    soundForEvent({ type: "family", details: { kind } })!,
  );
  expect(sounds.map((s) => s.voices.length)).toEqual([2, 1, 3]);
  expect(sounds[1].voices[0].hz).toBeLessThan(sounds[0].voices[0].hz);
  const audio = new TownAudio();
  const calls: Sound[] = [];
  audio.play = (sound) => {
    calls.push(sound);
  };
  const event = (id: number, kind: string): TownEvent => ({
    id,
    tick: id,
    actor_id: "npc-2",
    type: "family",
    text: kind,
    details: { kind },
  });
  audio.consume([event(1, "meal")], "wangjue");
  audio.consume([event(2, "quarrel"), event(3, "reconcile")], "wangjue");
  audio.consume([event(2, "quarrel"), event(3, "reconcile")], "wangjue");
  expect(calls).toHaveLength(2);
});

test("live invite schedules visit and inspector shows relatives and household residents", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const actions: unknown[] = [];
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/me/action") actions.push(route.request().postDataJSON());
    const payload =
      path === "/api/me"
        ? { id: "wangjue", name: "王崛", bio: "", goal: "" }
        : path === "/api/world"
          ? before
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
  await expect.poll(() => Boolean(socket)).toBe(true);
  socket!.send(JSON.stringify(packet));
  const banner = page.locator(".family-invite-banner");
  await expect(banner).toContainText("陈禾邀请你到家里做客");
  await expect(banner).toContainText("剩余 48 tick");
  await page
    .locator(".inspector-roster button")
    .filter({ hasText: "陈禾" })
    .click();
  await expect(page.locator(".inspector")).toContainText("苏晴（妻子）");
  await expect(page.locator(".inspector")).toContainText("住户：陈禾、苏晴");
  await page
    .locator(".inspector-roster button")
    .filter({ hasText: "苏晴" })
    .click();
  await expect(page.locator(".inspector")).toContainText("陈禾（丈夫）");
  await expect(page.locator(".inspector")).toContainText("住户：陈禾、苏晴");
  await banner.getByRole("button", { name: "前去赴约" }).click();
  await expect.poll(() => actions.length).toBe(1);
  expect(actions[0]).toMatchObject({ type: "visit", target_id: "npc-2" });
  socket!.send(
    JSON.stringify({
      ...packet,
      base_revision: 2,
      revision: 3,
      set: {
        family_state: {
          groups: {},
          invitations: { "a:wangjue": { ...invite, status: "accepted" } },
        },
      },
    }),
  );
  await expect(banner).toHaveCount(0);
  expect(errors).toEqual([]);
});
