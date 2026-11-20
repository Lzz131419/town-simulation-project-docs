export interface Action {
  type: string;
  item?: string;
  quantity?: number;
  place?: string;
  target_id?: string;
}
export interface Policy {
  reserve: number;
  daily_budget: number;
  fallback: string;
  auto_eat: boolean;
}
export interface Progress {
  xp: number;
  metrics: Record<string, number>;
  badges: string[];
}
export interface Milestone {
  id: string;
  name: string;
  metric: string;
  target: number;
  description: string;
  action: string;
  place: string;
}
export interface Resident {
  delivery_log?: { day: number; items: string[] };
  id: string;
  name: string;
  npc: boolean;
  x: number;
  y: number;
  cash: number;
  energy: number;
  hunger: number;
  inventory: Record<string, number>;
  mode: string;
  policy?: Policy;
  plan?: Action[];
  path: { x: number; y: number }[];
  task: Action | null;
  activity: string;
  completed: number;
  earned: number;
  relations: Record<string, number>;
  last_outcome: string;
  online: boolean;
  progress?: Progress;
}
export interface Order {
  id: number;
  buyer_id: string;
  seller_id: string | null;
  item: string;
  quantity: number;
  unit_price: number;
  status: string;
  expires_tick: number;
  escrow: number;
}
export interface TownEvent {
  id: number;
  tick: number;
  actor_id: string;
  type: string;
  text: string;
  details?: Record<string, unknown>;
}
export interface Town {
  supply?: { completed: number; goods: Record<string, number> };
  schema_version: number;
  tick: number;
  agents: Record<string, Resident>;
  market: Record<string, number>;
  treasury: number;
  orders: Order[];
  project: {
    name: string;
    wood: number;
    wood_target: number;
    cash: number;
    cash_target: number;
    completed: boolean;
    contributors: Record<string, number>;
  };
  activity_goal: { name: string; trades: number; target: number };
}
export interface User {
  id: string;
  name: string;
  bio: string;
  goal: string;
}
export interface Catalog {
  deliveries?: Record<
    string,
    { name: string; inputs: Record<string, number>; reward: number }
  >;
  delivery_daily_limit?: number;
  milestones?: Milestone[];
  items: Record<string, { name: string; buy: number; sell: number }>;
  places: Record<
    string,
    { name: string; x: number; y: number; action: string; district?: string }
  >;
  actions: Record<
    string,
    {
      name: string;
      place: string | null;
      energy: number;
      inputs?: Record<string, number>;
      outputs?: Record<string, number>;
      hunger_relief?: number;
      energy_gain?: number;
      tool_bonus?: Record<string, number>;
    }
  >;
  members: { id: string; name: string }[];
  tick_seconds: number;
  movement_per_tick?: number;
}
export const members = [
  { id: "zhangguo", name: "张果" },
  { id: "wangjue", name: "王崛" },
  { id: "lizhanbo", name: "李展博" },
  { id: "sunxiang", name: "孙祥" },
  { id: "qianjunhao", name: "钱俊昊" },
  { id: "yaofuen", name: "姚富恩" },
];
export const itemNames: Record<string, string> = {
  vegetable: "蔬菜",
  honey: "蜂蜜",
  flax: "亚麻",
  cloth: "布料",
  furniture: "家具",
  soup: "田园浓汤",
  meal: "烤鱼餐",
  tool: "工具",
  grain: "谷物",
  bread: "面包",
  wood: "木材",
  cash: "镇币",
  fruit: "水果",
  fish: "鲜鱼",
  ore: "矿石",
  herb: "草药",
};
export const actionNames: Record<string, string> = {
  harvest_veg: "采收蔬菜",
  gather_honey: "采集蜂蜜",
  harvest_flax: "收割亚麻",
  weave: "织造布料",
  assemble: "制作家具",
  cook: "熬制田园浓汤",
  eat_soup: "享用田园浓汤",
  honey_tea: "品尝蜂蜜茶",
  delivery: "交付街区物资",
  grill: "制作烤鱼餐",
  forge: "打造工具",
  eat_fruit: "吃水果",
  eat_meal: "享用烤鱼餐",
  brew: "冲泡草药茶",
  picnic: "营地野餐",
  farm: "收获谷物",
  craft: "制作木材",
  bake: "烘焙面包",
  work: "公共工作",
  rest: "回家休息",
  eat: "吃面包",
  buy: "购买",
  sell: "出售",
  social: "广场交流",
  contribute: "捐建仓库",
  move: "前往",
  gather: "采集水果",
  fish: "河边钓鱼",
  chop: "砍伐木材",
  mine: "开采矿石",
  forage: "采集草药",
};
export const placeNames: Record<string, string> = {
  garden: "南岸菜园",
  apiary: "花田蜂场",
  flax_field: "蓝花亚麻田",
  loom: "蓝线织坊",
  carpentry: "榫卯家具坊",
  kitchen: "南岸公共厨房",
  tea_house: "渡口茶舍",
  depot: "南岸交付站",
  meadow: "南岸营地",
  farm: "晨光农场",
  workshop: "木作工坊",
  bakery: "麦香面包房",
  market: "河畔集市",
  hall: "共建事务所",
  home: "河畔住宅",
  plaza: "邻里广场",
  orchard: "河畔果园",
  fishery: "钓鱼台",
  forest: "迷雾森林",
  mine: "山脚矿洞",
  herb_garden: "草药园",
};
export const gameTime = (tick: number) => {
  const mins = (8 * 60 + tick * 10) % 1440;
  return `第${Math.floor((8 * 60 + tick * 10) / 1440) + 1}天 · ${String(Math.floor(mins / 60)).padStart(2, "0")}:${String(mins % 60).padStart(2, "0")}`;
};
