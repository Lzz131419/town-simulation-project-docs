// Isolated mechanism spike. Not a town simulation implementation.
import test from 'node:test';
import assert from 'node:assert/strict';
function nextRng(state) {
  let x = state >>> 0;
  x ^= x << 13; x ^= x >>> 17; x ^= x << 5;
  return x >>> 0;
}
function session(world = { day: 0, rngState: 20261118, events: [] }) {
  let current = structuredClone(world), revision = 0;
  return {
    read: () => structuredClone(current), revision: () => revision,
    step(expected, fail = false) {
      if (expected !== revision) return 'STATE_CONFLICT';
      const candidate = structuredClone(current);
      candidate.day += 1;
      candidate.rngState = nextRng(candidate.rngState);
      candidate.events.push({ day: candidate.day, value: candidate.rngState });
      if (fail) return 'STEP_FAILED';
      current = candidate; revision += 1; return 'OK';
    }
  };
}
test('failure discards candidate state, RNG and events', () => {
  const s = session(), before = s.read();
  assert.equal(s.step(0, true), 'STEP_FAILED');
  assert.deepEqual(s.read(), before); assert.equal(s.revision(), 0);
});
test('same expected revision cannot commit twice', () => {
  const s = session(); assert.equal(s.step(0), 'OK');
  const before = s.read(); assert.equal(s.step(0), 'STATE_CONFLICT');
  assert.deepEqual(s.read(), before); assert.equal(s.revision(), 1);
});
test('15 plus restored 15 matches uninterrupted 30', () => {
  const full = session(), partial = session();
  for (let i = 0; i < 30; i++) full.step(full.revision());
  for (let i = 0; i < 15; i++) partial.step(partial.revision());
  const restored = session(JSON.parse(JSON.stringify(partial.read())));
  for (let i = 0; i < 15; i++) restored.step(restored.revision());
  assert.deepEqual(restored.read(), full.read());
});
test('restore does not append a world event', () => {
  const original = session(); original.step(0);
  const exported = original.read(); const restored = session(exported);
  assert.deepEqual(restored.read(), exported);
});
test('resetting to seed instead of saved RNG breaks continuation', () => {
  const s = session(); for (let i = 0; i < 15; i++) s.step(s.revision());
  const saved = s.read(); const wrong = session({ ...saved, rngState: 20261118 });
  const right = session(saved); right.step(0); wrong.step(0);
  assert.notDeepEqual(wrong.read(), right.read());
});
