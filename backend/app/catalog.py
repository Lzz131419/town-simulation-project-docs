from .domain.recipes import RECIPES, CONSUMABLES, TOOL_BONUS
from .world_map import LAYOUT, OBSTACLES as OBSTACLES
from .domain.progression import new_progress

MEMBERS = [
    ("zhangguo", "张果"),
    ("wangjue", "王崛"),
    ("lizhanbo", "李展博"),
    ("sunxiang", "孙祥"),
    ("qianjunhao", "钱俊昊"),
    ("yaofuen", "姚富恩"),
]
ITEMS = {
    "vegetable": {"name": "蔬菜", "buy": 3, "sell": 2},
    "honey": {"name": "蜂蜜", "buy": 5, "sell": 3},
    "flax": {"name": "亚麻", "buy": 3, "sell": 2},
    "cloth": {"name": "布料", "buy": 9, "sell": 6},
    "furniture": {"name": "家具", "buy": 26, "sell": 18},
    "soup": {"name": "田园浓汤", "buy": 7, "sell": 5},
    "meal": {"name": "烤鱼餐", "buy": 9, "sell": 6},
    "tool": {"name": "工具", "buy": 15, "sell": 10},
    "grain": {"name": "谷物", "buy": 2, "sell": 1},
    "bread": {"name": "面包", "buy": 4, "sell": 3},
    "wood": {"name": "木材", "buy": 5, "sell": 3},
    "fruit": {"name": "水果", "buy": 3, "sell": 2},
    "fish": {"name": "鲜鱼", "buy": 4, "sell": 2},
    "ore": {"name": "矿石", "buy": 8, "sell": 5},
    "herb": {"name": "草药", "buy": 6, "sell": 4},
}
PLACES = LAYOUT["places"]
ACTIONS = {
    "harvest_veg": {"name": "采收蔬菜", "place": "garden", "energy": 8},
    "gather_honey": {"name": "采集蜂蜜", "place": "apiary", "energy": 8},
    "harvest_flax": {"name": "收割亚麻", "place": "flax_field", "energy": 8},
    "weave": {"name": "织造布料", "place": "loom", "energy": 8},
    "assemble": {"name": "制作家具", "place": "carpentry", "energy": 10},
    "cook": {"name": "熬制田园浓汤", "place": "kitchen", "energy": 6},
    "eat_soup": {"name": "享用田园浓汤", "place": None, "energy": 0},
    "honey_tea": {"name": "品尝蜂蜜茶", "place": "tea_house", "energy": 0},
    "delivery": {"name": "交付街区物资", "place": "depot", "energy": 2},
    "grill": {"name": "制作烤鱼餐", "place": "fishery", "energy": 4},
    "forge": {"name": "打造工具", "place": "workshop", "energy": 8},
    "eat_fruit": {"name": "吃一份水果", "place": None, "energy": 0},
    "eat_meal": {"name": "享用烤鱼餐", "place": None, "energy": 0},
    "brew": {"name": "冲泡草药茶", "place": "herb_garden", "energy": 0},
    "picnic": {"name": "营地野餐", "place": "meadow", "energy": 0},
    "farm": {"name": "收获谷物", "place": "farm", "energy": 9},
    "craft": {"name": "制作木材", "place": "workshop", "energy": 10},
    "bake": {"name": "烘焙面包", "place": "bakery", "energy": 6},
    "work": {"name": "承接公共工作", "place": "hall", "energy": 8},
    "rest": {"name": "回家休息", "place": "home", "energy": 0},
    "eat": {"name": "吃一份面包", "place": None, "energy": 0},
    "buy": {"name": "购买物资", "place": "market", "energy": 0},
    "sell": {"name": "出售物资", "place": "market", "energy": 0},
    "social": {"name": "参加邻里活动", "place": "plaza", "energy": 4},
    "contribute": {"name": "捐建共享仓库", "place": "hall", "energy": 0},
    "move": {"name": "前往地点", "place": None, "energy": 0},
    "gather": {"name": "采集水果", "place": "orchard", "energy": 7},
    "fish": {"name": "河边钓鱼", "place": "fishery", "energy": 8},
    "chop": {"name": "砍伐木材", "place": "forest", "energy": 11},
    "mine": {"name": "开采矿石", "place": "mine", "energy": 13},
    "forage": {"name": "采集草药", "place": "herb_garden", "energy": 7},
}

for action, recipe in {**RECIPES, **CONSUMABLES}.items():
    ACTIONS[action].update(recipe)
for action, bonus in TOOL_BONUS.items():
    ACTIONS[action]["tool_bonus"] = bonus


def initial_world():
    agents = {}
    for i, (uid, name) in enumerate(MEMBERS):
        agents[uid] = {
            "id": uid,
            "name": name,
            "npc": False,
            "x": 320 + i * 36,
            "y": 520,
            "cash": 80,
            "energy": 85,
            "hunger": 20,
            "inventory": {
                "grain": 0,
                "bread": 3,
                "wood": 0,
                "fruit": 0,
                "fish": 0,
                "ore": 0,
                "herb": 0,
            },
            "mode": "manual",
            "policy": {"reserve": 20, "daily_budget": 20, "fallback": "work", "auto_eat": True},
            "spent_today": 0,
            "plan": [],
            "path": [],
            "task": None,
            "activity": "在河畔安顿下来",
            "completed": 0,
            "earned": 0,
            "relations": {},
            "last_outcome": "欢迎来到雾河镇。",
        }
    for i, name in enumerate(["林溪", "陈禾", "周木", "许宁", "苏晴", "陆川"]):
        uid = f"npc-{i + 1}"
        agents[uid] = {
            "id": uid,
            "name": name,
            "npc": True,
            "x": 360 + i * 45,
            "y": 480,
            "cash": 60,
            "energy": 80,
            "hunger": 20,
            "inventory": {"grain": 3, "bread": 3, "wood": 2},
            "mode": "rules",
            "policy": {
                "reserve": 10,
                "daily_budget": 16,
                "fallback": ["farm", "craft", "bake", "work", "social", "farm"][i],
                "auto_eat": True,
            },
            "spent_today": 0,
            "plan": [],
            "path": [],
            "task": None,
            "activity": "熟悉街坊",
            "completed": 0,
            "earned": 0,
            "relations": {},
            "last_outcome": "",
        }
    for agent in agents.values():
        agent["progress"] = new_progress()
        agent["delivery_log"] = {"day": -1, "items": []}
        for item in ITEMS:
            agent["inventory"].setdefault(item, 0)
    return {
        "schema_version": 2,
        "map_version": LAYOUT["version"],
        "tick": 0,
        "agents": agents,
        "supply": {"completed": 0, "goods": {}},
        "market": {
            **{item: 0 for item in ITEMS},
            "grain": 100,
            "bread": 100,
            "wood": 60,
            "fruit": 40,
            "fish": 30,
            "ore": 20,
            "herb": 25,
            "meal": 0,
            "tool": 0,
        },
        "treasury": 2000,
        "orders": [],
        "next_order": 1,
        "project": {
            "name": "河畔共享仓库",
            "wood": 0,
            "wood_target": 40,
            "cash": 0,
            "cash_target": 400,
            "contributors": {},
            "completed": False,
        },
        "activity_goal": {"name": "第一场河畔集市", "target": 20, "trades": 0},
        "economy_total": 2840,
        "weather": "sunny",
        "season": "spring",
    }
