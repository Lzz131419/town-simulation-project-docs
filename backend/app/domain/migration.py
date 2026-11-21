"""Additive world upgrades; never replenish or overwrite existing assets."""

from ..catalog import ITEMS, PLACES, ACTIONS, NPC_PERSONALITIES, NPC_FAMILIES
from ..world_map import LAYOUT
from ..pathfinding import nearest_walkable, route
from .progression import new_progress
from ..balance import balance
from .perishables import PERISHABLES, inv_add


def upgrade_world(data):
    from .homes import new_homes, home_destination
    changed = False
    if "homes" not in data:
        data["homes"] = new_homes()
        changed = True
    for default_home in new_homes():
        home = next((h for h in data["homes"] if h["id"] == default_home["id"]), None)
        if home is None:
            data["homes"].append(default_home)
            changed = True
        else:
            for key, value in default_home.items():
                if key not in home:
                    home[key] = value
                    changed = True
    for key, default in (("season", "spring"), ("weather", "sunny"),
                         ("market_day", {}), ("market_modifiers", {}), ("action_modifiers", {}),
                         ("bridge_closed_until", 0), ("flood_effort", None), ("feast_day", -1)):
        if key not in data:
            data[key] = default
            changed = True
    if "rng_seed" not in data:
        data["rng_seed"] = balance.weather.initial_seed
        changed = True
    if "supply" not in data:
        data["supply"] = {"completed": 0, "goods": {}}
        changed = True
    for agent in data["agents"].values():
        for key, default in (("home_id", None), ("reputation", 0), ("reputation_day", -1),
                             ("reputation_changed_today", 0), ("sleeping", None), ("fatigue", 0),
                             ("sleep_history", []), ("sleep_tracking_since", data["tick"])):
            if key not in agent:
                agent[key] = default
                changed = True
        if agent["npc"]:
            for key in ("next_private_order_tick", "next_gift_tick", "next_interaction_tick"):
                if key not in agent:
                    agent[key] = 0
                    changed = True
        if "memories" not in agent:
            agent["memories"] = []
            changed = True
        if agent["npc"] and "personality" not in agent:
            agent["personality"] = NPC_PERSONALITIES.get(agent["id"], "balanced")
            changed = True
        if "delivery_log" not in agent:
            agent["delivery_log"] = {"day": -1, "items": []}
            changed = True
        if "progress" not in agent:
            agent["progress"] = new_progress()
            changed = True
        for item in ITEMS:
            if item not in agent["inventory"]:
                agent["inventory"][item] = 0
                changed = True
        for item in sorted(PERISHABLES):
            if type(agent["inventory"].get(item)) is int:
                inv_add(agent["inventory"], item, 0)
                changed = True
    for item in ITEMS:
        if item not in data["market"]:
            data["market"][item] = 0
            changed = True
    if data.get("map_version", 0) < LAYOUT["version"]:
        for a in data["agents"].values():
            a["x"], a["y"] = nearest_walkable(a["x"], a["y"])
            if a["task"]:
                task = a["task"]
                place = (
                    task.get("place") if task["type"] == "move" else ACTIONS[task["type"]]["place"]
                )
                target = home_destination(data, a) if place == "home" else PLACES.get(place)
                if task.get("target_id"):
                    target = data["agents"].get(task["target_id"])
                if target:
                    tx, ty = nearest_walkable(target["x"], target["y"])
                    a["path"] = route(a["x"], a["y"], tx, ty)
            elif a["path"]:
                target = a["path"][-1]
                a["path"] = route(a["x"], a["y"], *nearest_walkable(target["x"], target["y"]))
        data["map_version"] = LAYOUT["version"]
        changed = True
    from .family import same_family
    family_added = False
    for agent in data['agents'].values():
        defaults = NPC_FAMILIES.get(agent['id'], {'group': None, 'kin': None})
        if not isinstance(agent.get('family'), dict):
            agent['family'] = dict(defaults)
            changed = family_added = True
        for key, value in defaults.items():
            if key not in agent['family']:
                agent['family'][key] = value
                changed = family_added = True
    if 'family_state' not in data:
        data['family_state'] = {'groups': {}, 'invitations': {}}
        changed = family_added = True
    for key in ('groups', 'invitations'):
        if key not in data['family_state']:
            data['family_state'][key] = {}
            changed = True
    for agent in data['agents'].values():
        for other in data['agents'].values():
            if same_family(agent, other):
                before = agent['relations'].get(other['id'])
                value = max(balance.family.relation_floor, before if before is not None else balance.family.baseline)
                if before != value:
                    agent['relations'][other['id']] = value
                    changed = True
    if family_added:
        # Keep the most upgraded existing family home; release the redundant title,
        # retaining that building's level and all personal assets.
        for group in ('a', 'b'):
            people = [a for a in data['agents'].values() if a['family'].get('group') == group]
            ids = {a['id'] for a in people}
            homes = sorted((h for h in data['homes'] if h.get('owner_id') in ids),
                           key=lambda h: (-h['level'], h['id']))
            if homes:
                for agent in people:
                    agent['home_id'] = homes[0]['id']
                for home in homes[1:]:
                    home['owner_id'] = None
    return changed
