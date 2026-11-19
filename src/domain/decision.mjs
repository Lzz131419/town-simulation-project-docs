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
export function executeProposal(world,{proposalId,proposalVersion}) {
 const s=world.state,p=s.proposal,r=s.resources;
 requireValue(proposalId===p.proposalId,'PROPOSAL_NOT_FOUND');
 requireValue(proposalVersion===p.version,'PROPOSAL_VERSION_MISMATCH');
 requireValue(p.status!=='EXECUTED','PROPOSAL_ALREADY_EXECUTED');
 requireValue(p.status==='APPROVED','PROPOSAL_NOT_APPROVED');
 requireValue(r.treasury>=p.cost,'INSUFFICIENT_TREASURY',`公库${r.treasury}镇币，维修需${p.cost}镇币，还差${p.cost-r.treasury}镇币`);
 const effects=[change('town',r,'treasury',r.treasury-p.cost),change('town',r,'water',r.water+p.waterEffect),change('town',s,'communityTrust',clamp(s.communityTrust+p.trustEffect)),change('town',s,'externalSpent',s.externalSpent+p.cost),change(p.proposalId,p,'status','EXECUTED')];
 return {data:{proposalId,status:p.status,treasury:r.treasury,water:r.water,communityTrust:s.communityTrust,externalSpent:s.externalSpent},events:[draft('PROPOSAL_EXECUTED',[p.proposerAgentId],[p.proposalId,'town'],'approved_and_funded',effects,`proposal:${p.proposalId}:execute`)]};
}
