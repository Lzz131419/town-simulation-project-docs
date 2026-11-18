import {parseBytes,requireValue} from '../shared/core.mjs';
export const SNAPSHOT_LIMIT=5*1024*1024;
export function appendEvents(world,drafts) {
 const added=drafts.map(d=>{const sequence=world.state.nextEventSequence++;return {eventId:`event-${String(sequence).padStart(6,'0')}`,sequence,day:world.state.day,...structuredClone(d),ruleVersion:1};});
 world.events.push(...added);return added;
}
export function exportWorld(world) {
 const json=JSON.stringify(world);
 requireValue(new TextEncoder().encode(json).byteLength<=SNAPSHOT_LIMIT,'SNAPSHOT_TOO_LARGE');
 return {json,filename:`mist-river-day-${world.state.day}.json`};
}
export function parseSnapshot(bytes) {return parseBytes(bytes,SNAPSHOT_LIMIT,'SNAPSHOT_TOO_LARGE','SNAPSHOT_INVALID');}
