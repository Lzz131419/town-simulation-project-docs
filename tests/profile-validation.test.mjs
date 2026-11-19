import test from 'node:test';import assert from 'node:assert/strict';
import {createWorld,SCENARIO} from '../src/shared/core.mjs';import {importProfile} from '../src/domain/profile.mjs';import {renderProfile} from '../src/ui/profile-view.mjs';
const p={profileVersion:1,displayName:'林溪',authorizationConfirmed:true},bytes=p=>new TextEncoder().encode(typeof p==='string'?p:JSON.stringify(p));
test('M3-AC-02: ordered validation rejects each invalid input without side effects',()=>{
 const cases=[[new Uint8Array(16385),'TOO_LARGE'],[new Uint8Array([255]),'INVALID'],[bytes('{'),'INVALID'],[bytes('[]'),'INVALID'],[bytes({...p,unknown:1,authorizationConfirmed:false}),'FIELD_NOT_ALLOWED'],[bytes({...p,authorizationConfirmed:false}),'NOT_AUTHORIZED'],[bytes({...p,authorizationConfirmed:'true'}),'NOT_AUTHORIZED'],[bytes({profileVersion:1,displayName:'林溪'}),'NOT_AUTHORIZED'],[bytes({...p,jobCode:'king'}),'INVALID'],[bytes({...p,profileVersion:2}),'INVALID']];
 for(const [input,code] of cases){const w=createWorld(SCENARIO),old=structuredClone(w);assert.throws(()=>importProfile(w,input),{code:'DIGITAL_PROFILE_'+code});assert.deepEqual(w,old);}
});
test('M3-AC-04: Unicode bounds, home and plain-text rendering',()=>{
 for(const [name,valid] of [['😀'.repeat(20),true],['😀'.repeat(21),false],['   ',false],['<b>林溪</b>',true]]){const w=createWorld(SCENARIO);if(!valid)assert.throws(()=>importProfile(w,bytes({...p,displayName:name})),{code:'DIGITAL_PROFILE_INVALID'});else{importProfile(w,bytes({...p,displayName:name}));const element={set innerHTML(v){throw Error('unsafe HTML');}};renderProfile(element,w.state.agents.at(-1));assert.ok(element.textContent.includes(name));}}
 assert.throws(()=>importProfile(createWorld(SCENARIO),bytes({...p,homeFacilityId:'missing'})),{code:'DIGITAL_PROFILE_HOME_NOT_FOUND'});
});
test('M3-AC-02: exactly 16KiB enters JSON validation and accepts whitespace padding',()=>{const json=JSON.stringify(p),input=bytes(json+' '.repeat(16384-bytes(json).length));assert.equal(importProfile(createWorld(SCENARIO),input).data.agentCount,31);});
