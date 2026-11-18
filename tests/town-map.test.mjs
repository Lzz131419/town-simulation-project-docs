import test from "node:test";
import assert from "node:assert/strict";
import {
  locations,
  layoutResidents,
  presentationFor,
} from "../src/ui/town-map.mjs";
import { SCENARIO, createWorld } from "../src/shared/core.mjs";
test("Map uses exactly the five real facility IDs and does not mutate world state", () => {
  const world = createWorld(SCENARIO),
    before = structuredClone(world);
  assert.deepEqual(
    Object.values(locations)
      .map((x) => x.facilityId)
      .sort(),
    world.state.facilities.map((x) => x.facilityId).sort(),
  );
  for (const agent of world.state.agents)
    presentationFor(agent, world.events, 0);
  assert.deepEqual(world, before);
});
test("Activity map follows this resident and this day, prioritizing real social activity", () => {
  const a = createWorld(SCENARIO).state.agents[0];
  const e = (day, type, actorIds = [a.agentId]) => ({ day, type, actorIds });
  assert.equal(presentationFor(a, [e(1, "WORKED")], 1).place, "farm");
  assert.equal(
    presentationFor(a, [e(1, "WORKED"), e(1, "SOCIAL_INTERACTION")], 1).place,
    "plaza",
  );
  assert.equal(
    presentationFor(a, [e(1, "WORKED"), e(2, "RESTED")], 2).place,
    "home",
  );
  assert.equal(
    presentationFor(
      a,
      [e(1, "SOCIAL_INTERACTION", ["resident-002"]), e(1, "WORKED")],
      1,
    ).place,
    "farm",
  );
});

test("All 31 residents retain distinct presentation positions when resting together", () => {
  const world = createWorld(SCENARIO);
  world.state.agents.push({
    ...world.state.agents[0],
    agentId: "digital-001",
    sourceType: "digitalPerson",
  });
  const events = world.state.agents.map((a) => ({
    day: 7,
    type: "RESTED",
    actorIds: [a.agentId],
  }));
  const points = layoutResidents(world.state.agents, events, 7);
  assert.equal(new Set(points.map((p) => `${p.to.x},${p.to.y}`)).size, 31);
});
