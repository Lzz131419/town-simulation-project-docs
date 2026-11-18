import { clamp,change,draft,sortedAgents,nextRandom,assertInvariants } from '../shared/core.mjs';
export function growNeeds(world) {
 return sortedAgents(world).map(a=>draft('NEEDS_GREW',[a.agentId],[a.agentId],'daily_needs',[
  change(a.agentId,a,'hunger',clamp(a.hunger+20)),change(a.agentId,a,'waterNeed',clamp(a.waterNeed+20))]));
}
export function work(world,agent) {
 const r=world.state.resources,id=agent.agentId;
 if(agent.energy<20 || agent.jobCode==='resident') return [draft('RESTED',[id],[id],'rest', [change(id,agent,'energy',clamp(agent.energy+20))])];
 const resource=agent.jobCode==='farmer'?'food':'water',pay=Math.min(2,r.treasury);
 const effects=[change('town',r,resource,r[resource]+4),change(id,agent,'energy',agent.energy-10),change(id,agent,'cash',agent.cash+pay),change('town',r,'treasury',r.treasury-pay)];
 const events=[draft('WORKED',[id],['town'],`production_4_wage_${pay}`,effects)];
 if(pay<2) events.push(draft('WAGE_SHORTFALL',[id],['town'],`wage_shortfall_${2-pay}`));
 return events;
}
export function consume(world,a) {
 const r=world.state.resources,id=a.agentId,events=[];
 if(a.hunger>=50) {
  if(r.food===0) events.push(draft('FOOD_OUT_OF_STOCK',[id],['market-01'],'food_stock_zero'));
  else if(a.cash<2) events.push(draft('INSUFFICIENT_PERSONAL_FUNDS',[id],['market-01'],'food_price_2'));
  else events.push(draft('FOOD_PURCHASED',[id],['market-01','town'], 'one_food_for_2', [change('town',r,'food',r.food-1),change(id,a,'cash',a.cash-2),change('town',r,'treasury',r.treasury+2),change(id,a,'hunger',a.hunger-40)]));
 }
 if(a.waterNeed>=70) {
  if(r.water===0) events.push(draft('WATER_OUT_OF_STOCK',[id],['well-01'],'water_stock_zero'));
  else events.push(draft('WATER_CONSUMED',[id],['well-01','town'],'one_water_free',[change('town',r,'water',r.water-1),change(id,a,'waterNeed',a.waterNeed-40)]));
 }
 return events;
}
export function settleLivelihood(world) {
 world.state.day+=1;
 world.rngState=nextRandom(world.rngState);
 const agents=sortedAgents(world),offset=world.rngState%agents.length,order=[...agents.slice(offset),...agents.slice(0,offset)];
 const events=growNeeds(world);
 for(const agent of order) events.push(...work(world,agent));
 for(const agent of order) events.push(...consume(world,agent));
 return events;
}
export function socialize(world) {
 const plaza=world.state.facilities.find(f=>f.facilityId==='plaza-01');
 if(!plaza.open || plaza.capacity===0) return [draft('FACILITY_UNAVAILABLE',[],['plaza-01'],'plaza_closed_or_zero_capacity')];
 const agents=sortedAgents(world).filter(a=>a.energy>=5&&a.hunger<80).slice(0,plaza.capacity);
 if(agents.length<2) return [draft('SOCIAL_SKIPPED',[],['plaza-01'],'fewer_than_two')];
 const events=[];
 for(let i=0;i+1<agents.length;i+=2) {
  const [a,b]=[agents[i],agents[i+1]],effects=[change(a.agentId,a,'energy',a.energy-5),change(b.agentId,b,'energy',b.energy-5)];
  for(const [x,y] of [[a,b],[b,a]]) for(const [field,delta] of [['trust',1],['affinity',2]]) {
   const before=x.relationships[y.agentId][field],after=clamp(before+delta);x.relationships[y.agentId][field]=after;
   effects.push({entityId:x.agentId,field:`relationships.${y.agentId}.${field}`,before,after});
  }
  events.push(draft('SOCIAL_INTERACTION',[a.agentId,b.agentId],['plaza-01'],'paired_by_stable_id',effects));
 }
 return events;
}
export function settleDay(world) {
 const events=settleLivelihood(world);events.push(...socialize(world),draft('DAY_SUMMARY',[],['town'],'daily_settlement_complete'));
 assertInvariants(world);return events.map(e=>({...e,causedBy:`tick:${world.state.day}`}));
}
