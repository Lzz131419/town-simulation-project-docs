import test from "node:test";
import assert from "node:assert/strict";
import {
  createWorld,
  SCENARIO,
  assertInvariants,
} from "../src/shared/core.mjs";
import { addProfile } from "../src/domain/profile.mjs";
const profile = {
  profileVersion: 1,
  displayName: "林溪",
  authorizationConfirmed: true,
};
test("M3-AC-01: one person, shared rules, zero cash and symmetric relations", () => {
  const w = createWorld(SCENARIO),
    r = addProfile(w, profile);
  assert.equal(r.data.agentCount, 31);
  const a = w.state.agents.at(-1);
  assert.equal(a.agentId, "digital-001");
  assert.equal(a.cash, 0);
  assert.equal(a.jobCode, "resident");
  assert.equal(a.energy, 70);
  assert.equal(a.homeFacilityId, "home-01");
  assertInvariants(w);
});
test("M3-AC-03: duplicate name accepted; second profile or closed vote rejected without mutation", () => {
  const w = createWorld(SCENARIO);
  addProfile(w, { ...profile, displayName: w.state.agents[0].displayName });
  const before = structuredClone(w);
  assert.throws(() => addProfile(w, profile), {
    code: "DIGITAL_PROFILE_LIMIT_REACHED",
  });
  assert.deepEqual(w, before);
  for (const status of ["APPROVED", "REJECTED", "EXECUTED"]) {
    const x = createWorld(SCENARIO);
    x.state.proposal.status = status;
    const old = structuredClone(x);
    assert.throws(() => addProfile(x, profile), {
      code: "DIGITAL_PROFILE_VOTING_CLOSED",
    });
    assert.deepEqual(x, old);
  }
});
