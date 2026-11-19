import {SCENARIO,isObject,requireValue,uint32,metric,nonnegative,canonical} from '../shared/core.mjs';
import {parseSnapshot} from './snapshot.mjs';
const value=condition=>requireValue(condition,'SNAPSHOT_VALUE_INVALID');
const reference=condition=>requireValue(condition,'SNAPSHOT_REFERENCE_INVALID');
const sequence=condition=>requireValue(condition,'EVENT_SEQUENCE_INVALID');
function shape(object,required,optional=[]) {
 requireValue(isObject(object),'SNAPSHOT_INVALID');
 requireValue(required.every(k=>Object.hasOwn(object,k)),'SNAPSHOT_FIELD_MISSING');
 requireValue(Object.keys(object).every(k=>[...required,...optional].includes(k)),'SNAPSHOT_INVALID');
}
const array=v=>requireValue(Array.isArray(v),'SNAPSHOT_INVALID');
const ballotFields=['agentId','waterNeed','communityTrust','affinity','score10','support','ruleVersion'];
const eventTypes=['WORLD_CREATED','NEEDS_GREW','WORKED','RESTED','WAGE_SHORTFALL','FOOD_PURCHASED','FOOD_OUT_OF_STOCK','INSUFFICIENT_PERSONAL_FUNDS','WATER_CONSUMED','WATER_OUT_OF_STOCK','SOCIAL_INTERACTION','SOCIAL_SKIPPED','FACILITY_UNAVAILABLE','DAY_SUMMARY','DIGITAL_PROFILE_IMPORTED','PROPOSAL_VOTED','PROPOSAL_EXECUTED','FOOD_SHORTAGE'];
export function validateWorld(w) {
 shape(w,['schemaVersion','ruleVersion','scenarioVersion','seed','rngState','state','events']);
 shape(w.state,['day','agents','facilities','resources','communityTrust','proposal','shortageApplied','externalSpent','nextEventSequence']);
 const s=w.state;array(s.agents);array(s.facilities);array(w.events);shape(s.resources,['food','water','wood','treasury']);shape(s.proposal,Object.keys(SCENARIO.proposal));array(s.proposal.ballots);
 for(const a of s.agents){shape(a,['agentId','displayName','sourceType','jobCode','homeFacilityId','energy','hunger','waterNeed','cash','relationships'],['profile']);requireValue(isObject(a.relationships),'SNAPSHOT_INVALID');for(const rel of Object.values(a.relationships))shape(rel,['trust','affinity']);if(a.sourceType==='digitalPerson'){requireValue(Object.hasOwn(a,'profile'),'SNAPSHOT_FIELD_MISSING');shape(a.profile,['profileVersion','displayName','authorizationConfirmed'],['jobCode','homeFacilityId','bioSummary']);}}
 for(const f of s.facilities)shape(f,['facilityId','type','open','capacity']);
 for(const b of s.proposal.ballots)shape(b,ballotFields);
 for(const e of w.events){shape(e,['eventId','sequence','day','type','actorIds','targetIds','ruleVersion','reason','effects','causedBy']);array(e.actorIds);array(e.targetIds);array(e.effects);for(const d of e.effects)shape(d,['entityId','field','before','after']);}
 requireValue([w.schemaVersion,w.ruleVersion,w.scenarioVersion].every(v=>v===1),'SNAPSHOT_VERSION_UNSUPPORTED');
 value(uint32(w.seed)&&uint32(w.rngState)&&nonnegative(s.day)&&metric(s.communityTrust)&&typeof s.shortageApplied==='boolean'&&nonnegative(s.externalSpent));
 value([30,31].includes(s.agents.length)&&Object.values(s.resources).every(nonnegative)&&s.facilities.length===5);
 for(const a of s.agents){value(typeof a.agentId==='string'&&typeof a.displayName==='string'&&a.displayName.trim()===a.displayName&&[...a.displayName].length>=1&&[...a.displayName].length<=20&&['generated','digitalPerson'].includes(a.sourceType)&&['farmer','waterWorker','resident'].includes(a.jobCode)&&[a.energy,a.hunger,a.waterNeed].every(metric)&&nonnegative(a.cash));for(const rel of Object.values(a.relationships))value(metric(rel.trust)&&metric(rel.affinity));
  if(a.sourceType==='digitalPerson'){const p=a.profile;value(p.profileVersion===1&&p.authorizationConfirmed===true&&p.displayName===a.displayName&&(!Object.hasOwn(p,'jobCode')||p.jobCode===a.jobCode)&&(!Object.hasOwn(p,'homeFacilityId')||p.homeFacilityId===a.homeFacilityId)&&(!Object.hasOwn(p,'bioSummary')||(typeof p.bioSummary==='string'&&[...p.bioSummary].length<=200)));}else value(!Object.hasOwn(a,'profile'));
 }
 for(const f of s.facilities)value(typeof f.open==='boolean'&&nonnegative(f.capacity)&&f.capacity<=31);
 const p=s.proposal;value(['OPEN','APPROVED','REJECTED','EXECUTED'].includes(p.status));
 value(['proposalId','version','cost','waterEffect','trustEffect','proposerAgentId'].every(k=>p[k]===SCENARIO.proposal[k]));
 for(const b of p.ballots)value([b.waterNeed,b.communityTrust,b.affinity].every(metric)&&nonnegative(b.score10)&&typeof b.support==='boolean'&&b.ruleVersion===1);
 for(const e of w.events)value(nonnegative(e.day)&&e.day<=s.day&&e.ruleVersion===1&&eventTypes.includes(e.type)&&typeof e.reason==='string'&&e.reason.length>0&&typeof e.causedBy==='string');
 const agents=new Map(s.agents.map(a=>[a.agentId,a])),facilities=new Map(s.facilities.map(f=>[f.facilityId,f])),targets=new Set([...agents.keys(),...facilities.keys(),'town',p.proposalId]);
 reference(agents.size===s.agents.length&&facilities.size===5);
 for(let i=1;i<=30;i++){const a=agents.get(`resident-${String(i).padStart(3,'0')}`);reference(!!a);value(a.sourceType==='generated'&&a.jobCode===(i<=10?'farmer':i<=20?'waterWorker':'resident'));}
 value(s.agents.filter(a=>a.sourceType==='digitalPerson').length===s.agents.length-30);
 if(s.agents.length===31)reference(agents.get('digital-001')?.sourceType==='digitalPerson');
 for(const f of SCENARIO.facilities){const actual=facilities.get(f.facilityId);reference(!!actual);value(actual.type===f.type);if(f.type!=='plaza')value(canonical(actual)===canonical(f));}
 for(const a of s.agents){reference(a.homeFacilityId==='home-01'&&Object.keys(a.relationships).length===agents.size&&[...agents.keys()].every(id=>Object.hasOwn(a.relationships,id)));for(const [id,rel] of Object.entries(a.relationships)){reference(agents.has(id));value(canonical(agents.get(id).relationships[a.agentId])===canonical(rel));}}
 for(const b of p.ballots)reference(agents.has(b.agentId));
 const checkEffect=d=>{
  reference(targets.has(d.entityId));value(typeof d.field==='string');
  let valid;
  if(d.entityId==='town') valid=['food','water','wood','treasury','externalSpent','day'].includes(d.field)?nonnegative: d.field==='communityTrust'?metric:d.field==='shortageApplied'?v=>typeof v==='boolean':null;
  else if(d.entityId===p.proposalId)valid=d.field==='status'?v=>['OPEN','APPROVED','REJECTED','EXECUTED'].includes(v):d.field==='ballots'?Array.isArray:null;
  else if(agents.has(d.entityId)){
   valid=d.field==='cash'?nonnegative:['energy','hunger','waterNeed'].includes(d.field)?metric:null;
   if(d.field.startsWith('relationships.')){const match=/^relationships\.([^.]+)\.(trust|affinity)$/.exec(d.field);reference(!!match&&agents.has(match[1]));valid=metric;}
  }
  value(!!valid&&valid(d.before)&&valid(d.after));
  if(d.field==='ballots')for(const ballots of [d.before,d.after])for(const b of ballots){shape(b,ballotFields);reference(agents.has(b.agentId));value([b.waterNeed,b.communityTrust,b.affinity].every(metric)&&b.score10===5*b.waterNeed+3*b.communityTrust+2*b.affinity&&b.support===(b.score10>=500)&&b.ruleVersion===1);}
 };
 for(const e of w.events){reference(e.actorIds.every(id=>agents.has(id))&&e.targetIds.every(id=>targets.has(id)));for(const d of e.effects)checkEffect(d);}
 sequence(nonnegative(s.nextEventSequence)&&s.nextEventSequence===w.events.length+1);
 let lastDay=0;
 w.events.forEach((e,i)=>{sequence(e.sequence===i+1&&e.eventId===`event-${String(i+1).padStart(6,'0')}`&&e.day>=lastDay);lastDay=e.day;});
 value(w.events.length>=1&&w.events[0].type==='WORLD_CREATED'&&w.events[0].day===0);
 value(s.agents.reduce((sum,a)=>sum+a.cash,s.resources.treasury+s.externalSpent)===1600);
 value(s.externalSpent===(p.status==='EXECUTED'?120:0));
 if(p.status==='OPEN')value(p.ballots.length===0);
 else{
  value(p.ballots.length===agents.size&&new Set(p.ballots.map(b=>b.agentId)).size===agents.size);
  for(const b of p.ballots)value(b.score10===5*b.waterNeed+3*b.communityTrust+2*b.affinity&&b.support===(b.score10>=500)&&(b.agentId!==p.proposerAgentId||b.affinity===50));
  const approved=p.ballots.filter(b=>b.support).length>p.ballots.length/2;value(approved?['APPROVED','EXECUTED'].includes(p.status):p.status==='REJECTED');
 }
 for(const e of w.events){
  const expected=e.type==='WORLD_CREATED'?'world:create':e.type==='DIGITAL_PROFILE_IMPORTED'?'profile:digital-001:import':e.type==='FOOD_SHORTAGE'?'shortage:once':e.type==='PROPOSAL_VOTED'?`proposal:${p.proposalId}:vote`:e.type==='PROPOSAL_EXECUTED'?`proposal:${p.proposalId}:execute`:`tick:${e.day}`;value(e.causedBy===expected);
 }
 value(w.events.filter(e=>e.type==='WORLD_CREATED').length===1);
 value(w.events.filter(e=>e.type==='FOOD_SHORTAGE').length===Number(s.shortageApplied));
 value(w.events.filter(e=>e.type==='DIGITAL_PROFILE_IMPORTED').length===s.agents.length-30);
 value(w.events.filter(e=>e.type==='PROPOSAL_VOTED').length===Number(p.status!=='OPEN'));
 value(w.events.filter(e=>e.type==='PROPOSAL_EXECUTED').length===Number(p.status==='EXECUTED'));
 const summaries=w.events.filter(e=>e.type==='DAY_SUMMARY');value(summaries.length===s.day&&summaries.every((e,i)=>e.day===i+1));
 return w;
}
export function importWorld(bytes){return validateWorld(parseSnapshot(bytes));}
