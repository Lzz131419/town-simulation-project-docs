import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { SCENARIO,createWorld,nextRandom,assertInvariants } from '../src/shared/core.mjs';
test('T01: fixed fixture has 30 unique residents, five facilities and conserved 1600 coins',()=>{
 assert.deepEqual(SCENARIO,JSON.parse(readFileSync(new URL('../docs/fixtures/scenario-v1.json',import.meta.url))));
 const w=createWorld(SCENARIO); assert.equal(w.state.day,0);assert.equal(new Set(w.state.agents.map(a=>a.agentId)).size,30);assert.equal(w.state.facilities.length,5);assertInvariants(w);
 assert.deepEqual(w,createWorld(SCENARIO)); w.state.resources.food=0;assert.equal(createWorld(SCENARIO).state.resources.food,180);
});
test('T01: reject config changes except nonzero uint32 seed',()=>{
 for(const config of [undefined,{}, {...SCENARIO,seed:0},{...SCENARIO,generatedResidents:29},{...SCENARIO,seed:1.5},{...SCENARIO,extra:1}]) assert.throws(()=>createWorld(config),{code:'SCENARIO_CONFIG_INVALID'});
 assert.throws(()=>createWorld({...SCENARIO,ruleVersion:2}),{code:'SCENARIO_VERSION_UNSUPPORTED'});
 assert.equal(createWorld({...SCENARIO,seed:1}).rngState,1);
});
test('T01: xorshift32 known vector and continuation',()=>{assert.equal(nextRandom(1),270369);assert.equal(nextRandom(270369),67634689);});
