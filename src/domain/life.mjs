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
