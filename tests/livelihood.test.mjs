import test from 'node:test';import assert from 'node:assert/strict';
import {createWorld,SCENARIO} from '../src/shared/core.mjs';
import {work,consume,growNeeds} from '../src/domain/life.mjs';
test('M2-AC-01: energy 19/20 and partial wage',()=>{
 for(const [energy,treasury,expected] of [[20,2,[10,22,0,184]],[19,2,[39,20,2,180]],[20,1,[10,21,0,184]]]) {
  const w=createWorld(SCENARIO),a=w.state.agents[0];a.energy=energy;w.state.resources.treasury=treasury;const events=work(w,a);
  assert.deepEqual([a.energy,a.cash,w.state.resources.treasury,w.state.resources.food],expected);
  assert.equal(events.some(e=>e.type==='WAGE_SHORTFALL'),energy===20&&treasury===1);
 }
});
test('M2-AC-02: hunger, stock and cash thresholds; stock error has precedence',()=>{
 for(const [hunger,food,cash,type] of [[49,1,2,null],[50,1,2,'FOOD_PURCHASED'],[50,0,2,'FOOD_OUT_OF_STOCK'],[50,1,1,'INSUFFICIENT_PERSONAL_FUNDS'],[50,0,1,'FOOD_OUT_OF_STOCK']]){
  const w=createWorld(SCENARIO),a=w.state.agents[0];Object.assign(a,{hunger,cash,waterNeed:30});w.state.resources.food=food;const before=structuredClone(w);const events=consume(w,a);
  assert.equal(events[0]?.type??null,type);
  if(type==='FOOD_PURCHASED'){assert.equal(a.hunger,10);assert.equal(a.cash,0);assert.equal(w.state.resources.food,0);assert.equal(w.state.resources.treasury,1002);}else assert.deepEqual(w,before);
 }
});
test('M2-AC-02: water 69/70 and zero stock',()=>{
 for(const [need,water,type] of [[69,0,null],[70,0,'WATER_OUT_OF_STOCK'],[70,1,'WATER_CONSUMED']]){const w=createWorld(SCENARIO),a=w.state.agents[0];a.waterNeed=need;w.state.resources.water=water;const events=consume(w,a);assert.equal(events[0]?.type??null,type);assert.equal(a.waterNeed,type==='WATER_CONSUMED'?30:need);}
});
test('M2-AC-04: needs clamp at 100',()=>{const w=createWorld(SCENARIO);Object.assign(w.state.agents[0],{hunger:100,waterNeed:99});growNeeds(w);assert.equal(w.state.agents[0].hunger,100);assert.equal(w.state.agents[0].waterNeed,100);});
