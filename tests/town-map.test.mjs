import test from "node:test";
import assert from "node:assert/strict";
import {
  activityRoute,
  dailyJourney,
  locations,
  layoutResidents,
  presentationFor,
  residentMotion,
  visibleSocialPairs,
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

test("Activity routes keep residents moving around their current facility", () => {
  const first = activityRoute("plaza", 2),
    second = activityRoute("plaza", 2);
  assert.deepEqual(first, second);
  assert.ok(first.length >= 4);
  assert.ok(new Set(first.map((p) => `${p.x},${p.y}`)).size > 1);
});

test("Daily journey follows the recorded work, market and social sequence", () => {
  const world = createWorld(SCENARIO),
    agent = world.state.agents[0],
    event = (sequence, type) => ({
      day: 1,
      sequence,
      type,
      actorIds: [agent.agentId],
    });
  assert.deepEqual(
    dailyJourney(
      agent,
      [
        event(1, "WORKED"),
        event(2, "FOOD_PURCHASED"),
        event(3, "SOCIAL_INTERACTION"),
      ],
      1,
    ),
    ["farm", "market", "plaza"],
  );
});

function journeyFixture() {
  const world = createWorld(SCENARIO),
    events = ["WORKED", "FOOD_PURCHASED", "SOCIAL_INTERACTION"].map((type, index) => ({
      day: 1,
      sequence: index + 1,
      type,
      actorIds: world.state.agents.map((agent) => agent.agentId),
    }));
  return layoutResidents(world.state.agents, events, 1);
}

const distance = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);

test("Resident movement stays continuous at the reproduced 5199/5200ms jump and the journey loop", () => {
  const person = journeyFixture()[0],
    before = structuredClone(person);
  // This boundary previously jumped 132.66 map units in one millisecond.
  assert.ok(distance(residentMotion(person, 5199), residentMotion(person, 5200)) < 0.1);
  const arrived = residentMotion(person, 5200);
  assert.equal(arrived.x, person.journey[1].anchor.x);
  assert.equal(arrived.y, person.journey[1].anchor.y);
  const loop = person.journey.length * 5200;
  assert.ok(distance(residentMotion(person, loop - 1), residentMotion(person, loop)) < 0.1);
  assert.equal(residentMotion(person, loop).x, person.journey[0].anchor.x);
  assert.equal(residentMotion(person, loop).y, person.journey[0].anchor.y);
  assert.deepEqual(person, before);
});

test("Staggered residents stay continuous at every facility boundary over two loops", () => {
  for (const person of journeyFixture()) {
    const offset = person.index * 0.17,
      firstBoundary = Math.floor(offset) + 1;
    for (let boundary = firstBoundary; boundary < firstBoundary + person.journey.length * 2; boundary++) {
      const time = (boundary - offset) * 5200;
      assert.ok(
        distance(residentMotion(person, time - 1), residentMotion(person, time + 1)) < 0.1,
        `${person.id} jumps at ${time}ms`,
      );
    }
  }
});

test("Single-facility wandering has a continuous loop and pauses its walking pose at stops", () => {
  const person = layoutResidents(createWorld(SCENARIO).state.agents, [], 0)[0],
    loop = person.route.length * 5200;
  assert.ok(distance(residentMotion(person, loop - 1), residentMotion(person, loop)) < 0.1);
  assert.equal(residentMotion(person, 0).moving, false);
  assert.equal(residentMotion(person, 3000).moving, true);
  assert.equal(residentMotion(person, 3000).currentPlace, "farm");
  assert.equal(residentMotion(person, 3000).inTransit, false);
});

test("Travel has no facility activity and reduced motion stays at the last recorded stop", () => {
  const person = journeyFixture()[0],
    inTransit = residentMotion(person, 3000);
  assert.equal(inTransit.moving, true);
  assert.equal(inTransit.inTransit, true);
  assert.equal(inTransit.currentPlace, null);
  const reduced = residentMotion(person, 0, true),
    final = person.journey.at(-1);
  assert.deepEqual(reduced, {
    ...final.anchor,
    currentPlace: final.place,
    moving: false,
    inTransit: false,
  });
  for (const time of [5199, 5200, 15600, 1000000])
    assert.deepEqual(residentMotion(person, time, true), reduced);
});

test("Social links require recorded partners together at the plaza, never residents in motion", () => {
  const agents = createWorld(SCENARIO).state.agents.slice(0, 4),
    events = [[0, 1], [2, 3]].map((pair, index) => ({
      day: 1,
      sequence: index + 1,
      type: "SOCIAL_INTERACTION",
      actorIds: pair.map((i) => agents[i].agentId),
    })),
    people = layoutResidents(agents, events, 1).map((person) => ({
      ...person,
      ...residentMotion(person, 0, true),
    }));
  assert.deepEqual(visibleSocialPairs(people).map((pair) => pair.map((p) => p.id)), [
    [agents[0].agentId, agents[1].agentId],
    [agents[2].agentId, agents[3].agentId],
  ]);
  for (const state of [{ moving: true }, { inTransit: true }, { currentPlace: "market" }]) {
    const changed = people.map((person, index) => index === 0 ? { ...person, ...state } : person);
    assert.equal(visibleSocialPairs(changed).length, 1);
  }
  assert.deepEqual(visibleSocialPairs(people.map((person) => ({ ...person, socialPartners: [] }))), []);
});
