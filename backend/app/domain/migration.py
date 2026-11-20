"""Additive world upgrades; never replenish or overwrite existing assets."""

from ..catalog import ITEMS, PLACES, ACTIONS
from ..world_map import LAYOUT
from ..pathfinding import nearest_walkable, route
from .progression import new_progress


def upgrade_world(data):
    changed = False
    if "supply" not in data:
        data["supply"] = {"completed": 0, "goods": {}}
        changed = True
    for agent in data["agents"].values():
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
                target = PLACES.get(place)
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
    return changed
