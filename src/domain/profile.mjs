import { requireValue,makeAgent,draft,parseBytes } from '../shared/core.mjs';
// Internal candidate operation: callers must validate input before entering here.
export function addProfile(world, profile) {
 const s=world.state;
 requireValue(!s.agents.some(a=>a.sourceType==='digitalPerson'),'DIGITAL_PROFILE_LIMIT_REACHED');
 requireValue(s.proposal.status==='OPEN','DIGITAL_PROFILE_VOTING_CLOSED');
 const agent=makeAgent('digital-001',profile.displayName,profile.jobCode??'resident','digitalPerson');agent.profile=structuredClone(profile);
 for(const other of [...s.agents,agent]) {agent.relationships[other.agentId]={trust:50,affinity:50};other.relationships[agent.agentId]={trust:50,affinity:50};}
 s.agents.push(agent);
 return {data:{agentId:agent.agentId,agentCount:s.agents.length},events:[draft('DIGITAL_PROFILE_IMPORTED',[agent.agentId],['home-01'],'authorized_profile',[], 'profile:digital-001:import')]};
}
export function validateProfile(profile) {
 const allowed=['profileVersion','displayName','authorizationConfirmed','jobCode','homeFacilityId','bioSummary'];
 requireValue(Object.keys(profile).every(k=>allowed.includes(k)),'DIGITAL_PROFILE_FIELD_NOT_ALLOWED');
 requireValue(profile.authorizationConfirmed===true,'DIGITAL_PROFILE_NOT_AUTHORIZED');
 const name=typeof profile.displayName==='string'?profile.displayName.trim():'';
 requireValue(profile.profileVersion===1 && [...name].length>=1 && [...name].length<=20 && (!Object.hasOwn(profile,'jobCode') || ['farmer','waterWorker','resident'].includes(profile.jobCode)) && (!Object.hasOwn(profile,'bioSummary') || (typeof profile.bioSummary==='string' && [...profile.bioSummary].length<=200)) && (!Object.hasOwn(profile,'homeFacilityId') || typeof profile.homeFacilityId==='string'),'DIGITAL_PROFILE_INVALID');
 requireValue(!Object.hasOwn(profile,'homeFacilityId') || profile.homeFacilityId==='home-01','DIGITAL_PROFILE_HOME_NOT_FOUND');
 return {...profile,displayName:name,jobCode:profile.jobCode??'resident',homeFacilityId:profile.homeFacilityId??'home-01'};
}
export function importProfile(world,bytes) {
 const parsed=parseBytes(bytes,16384,'DIGITAL_PROFILE_TOO_LARGE','DIGITAL_PROFILE_INVALID');
 return addProfile(world,validateProfile(parsed));
}
