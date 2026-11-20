import type { Town, TownEvent, Resident } from "../types";
export interface Snapshot {
  type: "world";
  revision: number;
  world: Town;
  events: TownEvent[];
}
const object = (v: unknown): v is Record<string, any> =>
  !!v && typeof v === "object" && !Array.isArray(v);
const finite = (v: unknown): v is number =>
  typeof v === "number" && Number.isFinite(v);
const safeKey = (key: string) =>
  !["__proto__", "constructor", "prototype"].includes(key);
const integer = (v: unknown) => finite(v) && Number.isInteger(v) && v >= 0;
const numericRecord = (v: unknown) =>
  object(v) && Object.entries(v).every(([k, n]) => safeKey(k) && integer(n));
const action = (a: unknown) => object(a) && typeof a.type === "string";
function resident(a: unknown): a is Resident {
  if (
    !object(a) ||
    typeof a.id !== "string" ||
    !safeKey(a.id) ||
    typeof a.name !== "string" ||
    !finite(a.x) ||
    !finite(a.y) ||
    !finite(a.cash) ||
    !finite(a.energy) ||
    !finite(a.hunger)
  )
    return false;
  return (
    typeof a.npc === "boolean" &&
    typeof a.online === "boolean" &&
    typeof a.mode === "string" &&
    typeof a.last_outcome === "string" &&
    integer(a.completed) &&
    integer(a.earned) &&
    numericRecord(a.inventory) &&
    (a.delivery_log === undefined ||
      (object(a.delivery_log) &&
        Number.isInteger(a.delivery_log.day) &&
        a.delivery_log.day >= -1 &&
        Array.isArray(a.delivery_log.items) &&
        a.delivery_log.items.every(
          (id: unknown) => typeof id === "string" && safeKey(id),
        ))) &&
    (a.task === null || action(a.task)) &&
    (a.plan === undefined || (Array.isArray(a.plan) && a.plan.every(action))) &&
    (a.policy === undefined ||
      (object(a.policy) &&
        integer(a.policy.reserve) &&
        integer(a.policy.daily_budget) &&
        typeof a.policy.fallback === "string" &&
        typeof a.policy.auto_eat === "boolean")) &&
    Array.isArray(a.path) &&
    a.path.every((p) => object(p) && finite(p.x) && finite(p.y)) &&
    numericRecord(a.relations) &&
    typeof a.activity === "string"
  );
}
function validEvents(v: unknown): v is TownEvent[] {
  return (
    Array.isArray(v) &&
    v.every(
      (e) =>
        object(e) &&
        Number.isInteger(e.id) &&
        finite(e.tick) &&
        typeof e.actor_id === "string" &&
        typeof e.type === "string" &&
        typeof e.text === "string",
    )
  );
}
function world(v: unknown): v is Town {
  return (
    object(v) &&
    integer(v.tick) &&
    integer(v.schema_version) &&
    object(v.agents) &&
    Object.entries(v.agents).every(
      ([id, a]) => safeKey(id) && resident(a) && a.id === id,
    ) &&
    numericRecord(v.market) &&
    integer(v.treasury) &&
    (v.supply === undefined ||
      (object(v.supply) &&
        integer(v.supply.completed) &&
        numericRecord(v.supply.goods))) &&
    Array.isArray(v.orders) &&
    v.orders.every(
      (o) =>
        object(o) &&
        integer(o.id) &&
        typeof o.buyer_id === "string" &&
        (o.seller_id === null || typeof o.seller_id === "string") &&
        typeof o.item === "string" &&
        integer(o.quantity) &&
        integer(o.unit_price) &&
        integer(o.escrow) &&
        integer(o.expires_tick) &&
        typeof o.status === "string",
    ) &&
    object(v.project) &&
    typeof v.project.name === "string" &&
    ["wood", "wood_target", "cash", "cash_target"].every((k) =>
      integer(v.project[k]),
    ) &&
    typeof v.project.completed === "boolean" &&
    numericRecord(v.project.contributors) &&
    object(v.activity_goal) &&
    typeof v.activity_goal.name === "string" &&
    integer(v.activity_goal.trades) &&
    integer(v.activity_goal.target)
  );
}
export function applyPacket(
  current: Snapshot | null,
  packet: unknown,
): Snapshot | null {
  if (!object(packet)) throw Error("无效同步消息");
  if (packet.type === "pong") return current;
  if (
    !Number.isInteger(packet.revision) ||
    packet.revision < 0 ||
    !validEvents(packet.events)
  )
    throw Error("无效同步版本");
  if (current && packet.revision < current.revision) return current;
  if (packet.type === "world") {
    if (!world(packet.world)) throw Error("无效世界快照");
    return packet as Snapshot;
  }
  if (
    packet.type !== "patch" ||
    !current ||
    packet.base_revision !== current.revision
  )
    throw Error("世界版本不连续");
  if (
    !object(packet.set) ||
    !object(packet.agents) ||
    !Array.isArray(packet.removed_agents)
  )
    throw Error("无效增量");
  const allowed = [
    "schema_version",
    "map_version",
    "supply",
    "tick",
    "market",
    "treasury",
    "orders",
    "next_order",
    "project",
    "activity_goal",
    "economy_total",
    "weather",
    "season",
  ];
  if (
    !Object.keys(packet.set).every((k) => allowed.includes(k)) ||
    !Object.entries(packet.agents).every(
      ([id, a]) => safeKey(id) && resident(a) && a.id === id,
    ) ||
    !packet.removed_agents.every(
      (id: unknown) => typeof id === "string" && safeKey(id),
    )
  )
    throw Error("无效增量字段");
  const agents = { ...current.world.agents, ...packet.agents };
  for (const id of packet.removed_agents) delete agents[id];
  const next = { ...current.world, ...packet.set, agents };
  if (!world(next)) throw Error("无效增量世界");
  const events = [
    ...new Map(
      [...packet.events, ...current.events].map((e) => [e.id, e]),
    ).values(),
  ]
    .sort((a, b) => b.id - a.id)
    .slice(0, 60);
  return { type: "world", revision: packet.revision, world: next, events };
}
