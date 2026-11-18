import {SCENARIO,createWorld,requireValue,draft,change} from '../shared/core.mjs';
import {settleDay} from '../domain/life.mjs';
import {importProfile} from '../domain/profile.mjs';
import {closeVote,executeProposal,previewBallots} from '../domain/decision.mjs';
import {appendEvents,exportWorld} from '../evidence/snapshot.mjs';
import {importWorld,validateWorld} from '../evidence/validate.mjs';
export function createSimulation({schedule=setInterval,cancel=clearInterval,beforeCommit=()=>{}}={}) {
 let world=null,paused=true,busy=false,revision=0,timer=null;
 const diagnostics=[],listeners=new Set();
 const success=(data,events=[])=>({ok:true,data:structuredClone(data),events:structuredClone(events)});
 const reject=(code,type,message=code)=>{diagnostics.push({code,type});return {ok:false,error:{code,message},events:[]};};
 const notify=()=>{for(const listener of listeners){try{listener();}catch{diagnostics.push({code:'UI_NOTIFICATION_FAILED',type:'READ'});}}};
 const stop=()=>{if(timer!==null)cancel(timer);timer=null;paused=true;};
 function dispatch(command,automatic=false) {
  const {type,payload={},expectedRevision}=command??{};
  if(busy)return reject('STEP_IN_PROGRESS',type);
  if(expectedRevision!==revision)return reject('STATE_CONFLICT',type);
  if(!world&&!['CREATE_WORLD','IMPORT_SNAPSHOT'].includes(type))return reject('WORLD_NOT_INITIALIZED',type);
  if(!paused&&!automatic)return reject('SIMULATION_RUNNING',type);
  busy=true;let phase='operation',result;
  try {
   let candidate=world?structuredClone(world):null,data={},drafts=[];
   switch(type){
    case 'CREATE_WORLD':candidate=createWorld(payload.config);data={day:0,agentCount:30};drafts=[draft('WORLD_CREATED',[],['town'],'fixed_scenario',[],'world:create')];break;
    case 'STEP':drafts=settleDay(candidate);data={day:candidate.state.day};break;
    case 'IMPORT_PROFILE':({data,events:drafts}=importProfile(candidate,payload.utf8Bytes));break;
    case 'CLOSE_VOTE':({data,events:drafts}=closeVote(candidate,payload));break;
    case 'EXECUTE_PROPOSAL':({data,events:drafts}=executeProposal(candidate,payload));break;
    case 'TRIGGER_SHORTAGE':{
     const s=candidate.state;requireValue(!s.shortageApplied,'SHORTAGE_ALREADY_APPLIED');const before=s.resources.food,after=Math.floor(before*0.8);
     const effects=[change('town',s.resources,'food',after),change('town',s,'shortageApplied',true)];
     drafts=[draft('FOOD_SHORTAGE',[],['town'],`food_lost_${before-after}`,effects,'shortage:once')];data={foodBefore:before,foodAfter:after};break;
    }
    case 'IMPORT_SNAPSHOT':candidate=importWorld(payload.utf8Bytes);data={day:candidate.state.day,agentCount:candidate.state.agents.length};break;
    default:requireValue(false,'COMMAND_INVALID');
   }
   phase='commit';const events=appendEvents(candidate,drafts);
   beforeCommit({type,candidate});validateWorld(candidate);
   world=candidate;revision+=1;
   if(['CREATE_WORLD','IMPORT_SNAPSHOT'].includes(type))stop();
   if(type==='STEP')data.eventIds=events.map(e=>e.eventId);
   result=success({...data,revision},events);
  }catch(error){
   const fallback=type==='EXECUTE_PROPOSAL'?'PROPOSAL_EXECUTION_FAILED':type==='STEP'?'STEP_FAILED':'COMMAND_FAILED';
   result=reject(phase==='operation'&&error.code?error.code:fallback,type,phase==='operation'&&error.code?error.message:fallback);
  }finally{busy=false;}
  notify();return result;
 }
 function read(type,reader){if(!world)return reject('WORLD_NOT_INITIALIZED',type);try{return success(reader());}catch(error){return reject(error.code??'READ_FAILED',type);}}
 const api={
  dispatch:command=>dispatch(command),
  get runtime(){return {paused,busy,runtimeRevision:revision,diagnostics:structuredClone(diagnostics)};},
  get world(){return structuredClone(world);},
  subscribe(listener){listeners.add(listener);return ()=>listeners.delete(listener);},
  pause(){if(!world)return reject('WORLD_NOT_INITIALIZED','PAUSE');stop();notify();return success({paused});},
  resume(){if(!world)return reject('WORLD_NOT_INITIALIZED','RESUME');if(busy)return reject('STEP_IN_PROGRESS','RESUME');if(timer===null){paused=false;timer=schedule(()=>{if(paused||busy)return;const result=dispatch({type:'STEP',expectedRevision:revision},true);if(!result.ok){stop();notify();}},1000);}notify();return success({paused});},
  exportSnapshot(){if(busy)return reject('STEP_IN_PROGRESS','EXPORT_SNAPSHOT');if(!world)return reject('WORLD_NOT_INITIALIZED','EXPORT_SNAPSHOT');if(!paused)return reject('SIMULATION_RUNNING','EXPORT_SNAPSHOT');return read('EXPORT_SNAPSHOT',()=>exportWorld(world));},
  getOverview(){return read('OVERVIEW',()=>{const s=world.state;return {day:s.day,agentCount:s.agents.length,resources:s.resources,communityTrust:s.communityTrust,proposal:s.proposal,shortageApplied:s.shortageApplied,externalSpent:s.externalSpent};});},
  getAgent({agentId}){return read('AGENT',()=>{const agent=world.state.agents.find(a=>a.agentId===agentId);requireValue(agent,'AGENT_NOT_FOUND');return {agent,recentEvents:world.events.filter(e=>e.actorIds.includes(agentId)||e.targetIds.includes(agentId)).slice(-10).reverse()};});},
  listAgents(){return read('AGENTS',()=>({agents:world.state.agents}));},
  listEvents({agentId,type}={}){return read('EVENTS',()=>({events:world.events.filter(e=>(!agentId||e.actorIds.includes(agentId)||e.targetIds.includes(agentId))&&(!type||e.type===type)).toReversed()}));},
  getBallots(){return read('BALLOTS',()=>({ballots:world.state.proposal.status==='OPEN'?previewBallots(world):world.state.proposal.ballots}));},
  dispose(){stop();listeners.clear();}
 };
 return api;
}
export {SCENARIO};
