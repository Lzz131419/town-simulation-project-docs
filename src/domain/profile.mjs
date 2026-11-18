import { requireValue,makeAgent,draft } from '../shared/core.mjs';
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
