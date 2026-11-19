import {requireValue,sortedAgents,draft,change,clamp} from '../shared/core.mjs';
export function previewBallots(world) {
 const s=world.state,p=s.proposal;
 return sortedAgents(world).map(a=>{
  const affinity=a.agentId===p.proposerAgentId?50:(a.relationships[p.proposerAgentId]?.affinity??50),score10=5*a.waterNeed+3*s.communityTrust+2*affinity;
  return {agentId:a.agentId,waterNeed:a.waterNeed,communityTrust:s.communityTrust,affinity,score10,support:score10>=500,ruleVersion:1};
 });
}
export function closeVote(world,{proposalId}) {
 const p=world.state.proposal;
 requireValue(proposalId===p.proposalId,'PROPOSAL_NOT_FOUND');
 requireValue(p.status==='OPEN','VOTE_ALREADY_CLOSED');
 requireValue(world.state.agents.length>0,'NO_ELIGIBLE_VOTERS');
 const ballots=previewBallots(world),support=ballots.filter(b=>b.support).length,oppose=ballots.length-support;
 const effects=[change(p.proposalId,p,'status',support>oppose?'APPROVED':'REJECTED'),change(p.proposalId,p,'ballots',ballots)];
 return {data:{status:p.status,support,oppose,ballots:structuredClone(ballots)},events:[draft('PROPOSAL_VOTED',ballots.map(b=>b.agentId),[p.proposalId],'strict_majority',effects,`proposal:${p.proposalId}:vote`)]};
}
