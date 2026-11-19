import { SCENARIO } from './scenario.mjs';
export { SCENARIO };
export const clamp = value => Math.max(0, Math.min(100, value));
export const uint32 = value => Number.isInteger(value) && value > 0 && value <= 0xffffffff;
export const nonnegative = value => Number.isSafeInteger(value) && value >= 0;
export const metric = value => nonnegative(value) && value <= 100;
export const isObject = value => value !== null && typeof value === 'object' && !Array.isArray(value);
export const sortedAgents = world => [...world.state.agents].sort((a,b) => a.agentId < b.agentId ? -1 : a.agentId > b.agentId ? 1 : 0);
export function fail(code, message = code) { const error = new Error(message); error.code = code; throw error; }
export function requireValue(condition, code, message) { if (!condition) fail(code, message); }
export function canonical(value) {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (isObject(value)) return '{' + Object.keys(value).sort().map(k => JSON.stringify(k)+':'+canonical(value[k])).join(',') + '}';
  return JSON.stringify(value);
}
export function nextRandom(state) { let x=state; x ^= x << 13; x ^= x >>> 17; x ^= x << 5; return x >>> 0; }
export function parseBytes(bytes, limit, tooLarge, invalid) {
  requireValue(bytes instanceof Uint8Array, invalid);
  requireValue(bytes.byteLength <= limit, tooLarge);
  try { const parsed = JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes)); requireValue(isObject(parsed), invalid); return parsed; }
  catch(error) { fail(invalid); }
}
export function draft(type, actorIds, targetIds, reason, effects = [], causedBy) { return {type,actorIds,targetIds,reason,effects,causedBy}; }
export function change(entityId, object, field, after) { const before=object[field]; object[field]=after; return {entityId,field,before,after}; }
export function makeAgent(id, name, job, sourceType = 'generated') {
  return {agentId:id,displayName:name,sourceType,jobCode:job,homeFacilityId:'home-01',...structuredClone(sourceType==='generated'?SCENARIO.agentDefaults:SCENARIO.digitalDefaults),relationships:{}};
}
export function createWorld(config) {
  requireValue(isObject(config) && Object.keys(SCENARIO).every(k=>Object.hasOwn(config,k)), 'SCENARIO_CONFIG_INVALID');
  requireValue(['schemaVersion','ruleVersion','scenarioVersion'].every(k=>config[k]===1), 'SCENARIO_VERSION_UNSUPPORTED');
  requireValue(uint32(config.seed) && canonical({...config,seed:SCENARIO.seed}) === canonical(SCENARIO), 'SCENARIO_CONFIG_INVALID');
  const agents = Array.from({length:30},(_,i) => makeAgent(`resident-${String(i+1).padStart(3,'0')}`,`居民${String(i+1).padStart(2,'0')}`,i<10?'farmer':i<20?'waterWorker':'resident'));
  for (const a of agents) for (const b of agents) a.relationships[b.agentId] = {trust:50,affinity:50};
  return {schemaVersion:1,ruleVersion:1,scenarioVersion:1,seed:config.seed,rngState:config.seed,state:{day:0,agents,facilities:structuredClone(config.facilities),resources:structuredClone(config.resources),communityTrust:60,proposal:structuredClone(config.proposal),shortageApplied:false,externalSpent:0,nextEventSequence:1},events:[]};
}
export function assertInvariants(world) {
  const s=world.state;
  requireValue(nonnegative(s.day) && Object.values(s.resources).every(nonnegative) && metric(s.communityTrust), 'WORLD_INVARIANT_FAILED');
  let money=s.resources.treasury+s.externalSpent;
  for (const a of s.agents) {
    requireValue(nonnegative(a.cash) && [a.energy,a.hunger,a.waterNeed].every(metric), 'WORLD_INVARIANT_FAILED');
    money+=a.cash;
    for (const [id,rel] of Object.entries(a.relationships)) {
      const other=s.agents.find(b=>b.agentId===id);
      requireValue(other && metric(rel.trust) && metric(rel.affinity) && canonical(other.relationships[a.agentId])===canonical(rel), 'WORLD_INVARIANT_FAILED');
    }
  }
  requireValue(nonnegative(s.externalSpent) && money===1600, 'WORLD_INVARIANT_FAILED');
}
