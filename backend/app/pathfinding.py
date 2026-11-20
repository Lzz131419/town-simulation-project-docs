import heapq
import math
from .world_map import LAYOUT, OBSTACLES

MOVEMENT_PER_TICK = 40
CELL = LAYOUT["navigation"]["cell"]
W, H = LAYOUT["navigation"]["width"] // CELL, LAYOUT["navigation"]["height"] // CELL


def blocked(x, y):
    px, py = x * CELL + 8, y * CELL + 8
    river = LAYOUT["river"]
    water = river["x"] <= px < river["x"] + river["width"]
    bridge = any(
        b["x"] <= px <= b["x"] + b["w"] and b["y"] <= py <= b["y"] + b["h"]
        for b in LAYOUT["bridges"]
    )
    return (
        not (1 <= x < W - 1 and 1 <= y < H - 1)
        or (water and not bridge)
        or any(a - 5 <= px <= a + w + 5 and b - 5 <= py <= b + h + 5 for a, b, w, h in OBSTACLES)
    )


def route(x, y, tx, ty):
    if not all(math.isfinite(v) for v in (x, y, tx, ty)):
        raise ValueError("坐标必须为有限数值")
    if not (CELL <= tx < (W - 1) * CELL and CELL <= ty < (H - 1) * CELL):
        raise ValueError("目的地超出地图边界")
    start = (max(1, min(W - 2, int(x // CELL))), max(1, min(H - 2, int(y // CELL))))
    end = (max(1, min(W - 2, int(tx // CELL))), max(1, min(H - 2, int(ty // CELL))))
    if blocked(*end):
        raise ValueError("目的地不可通行")
    q = [(0, start)]
    came = {}
    costs = {start: 0}
    while q:
        _, cur = heapq.heappop(q)
        if cur == end:
            nodes = []
            while cur != start:
                nodes.append({"x": cur[0] * CELL + 8, "y": cur[1] * CELL + 8})
                cur = came[cur]
            nodes.reverse()
            nodes.append({"x": tx, "y": ty})
            return nodes
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nxt = (cur[0] + dx, cur[1] + dy)
            if not (1 <= nxt[0] < W - 1 and 1 <= nxt[1] < H - 1) or blocked(*nxt):
                continue
            cost = costs[cur] + 1
            if cost < costs.get(nxt, 1e9):
                costs[nxt] = cost
                came[nxt] = cur
                heapq.heappush(q, (cost + abs(nxt[0] - end[0]) + abs(nxt[1] - end[1]), nxt))
    raise ValueError("暂时找不到可达路线")


def advance(agent, distance=MOVEMENT_PER_TICK):
    while agent["path"] and distance > 0:
        p = agent["path"][0]
        dx = p["x"] - agent["x"]
        dy = p["y"] - agent["y"]
        d = math.hypot(dx, dy)
        if d <= distance:
            agent["x"], agent["y"] = p["x"], p["y"]
            agent["path"].pop(0)
            distance -= d
        else:
            agent["x"] += dx / d * distance
            agent["y"] += dy / d * distance
            distance = 0


def nearest_walkable(x, y):
    """Relocate old save positions only when new geometry makes them invalid."""
    cell = (max(1, min(W - 2, int(x // CELL))), max(1, min(H - 2, int(y // CELL))))
    if not blocked(*cell):
        return x, y
    from collections import deque

    queue, seen = deque([cell]), {cell}
    while queue:
        current = queue.popleft()
        if not blocked(*current):
            return current[0] * CELL + CELL / 2, current[1] * CELL + CELL / 2
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            n = (current[0] + dx, current[1] + dy)
            if n not in seen and 1 <= n[0] < W - 1 and 1 <= n[1] < H - 1:
                seen.add(n)
                queue.append(n)
    raise ValueError("地图没有可用落脚点")
