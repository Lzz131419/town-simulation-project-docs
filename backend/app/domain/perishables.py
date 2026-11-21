"""Deterministic inventory operations; older integer food stacks remain readable."""

PERISHABLES = frozenset({"fish", "soup", "meal", "vegetable", "fruit"})


def inv_qty(inventory, item):
    value = inventory.get(item, 0)
    return sum(batch["qty"] for batch in value) if isinstance(value, list) else value


def inv_total(inventory):
    return sum(inv_qty(inventory, item) for item in inventory)


def inv_batches(inventory, item):
    """Return independent batches, oldest freshness first; never mutate a quote."""
    value = inventory.get(item, 0)
    if isinstance(value, int):
        return [{"qty": value, "fresh": 100}] if value else []
    return sorted((dict(batch) for batch in value), key=lambda batch: batch["fresh"])


def inv_add(inventory, item, n, fresh=100):
    if type(n) is not int or n < 0 or type(fresh) is not int or not 0 <= fresh <= 100:
        raise ValueError("库存数量或新鲜度不正确")
    if item not in PERISHABLES:
        inventory[item] = inv_qty(inventory, item) + n
        return
    batches = inv_batches(inventory, item)
    if n:
        for batch in batches:
            if batch["fresh"] == fresh:
                batch["qty"] += n
                break
        else:
            batches.append({"qty": n, "fresh": fresh})
    inventory[item] = sorted(batches, key=lambda batch: batch["fresh"])


def inv_take(inventory, item, n):
    """Remove least-fresh units first and return their batches for transfers/effects."""
    if type(n) is not int or n < 0 or inv_qty(inventory, item) < n:
        raise ValueError("物资不足")
    remaining, taken = [], []
    for batch in inv_batches(inventory, item):
        count = min(n, batch["qty"])
        if count:
            taken.append({"qty": count, "fresh": batch["fresh"]})
            batch["qty"] -= count
            n -= count
        if batch["qty"]:
            remaining.append(batch)
    inventory[item] = remaining if item in PERISHABLES else sum(b["qty"] for b in remaining)
    return taken


def sale_total(inventory, item, n, unit_price):
    """Quote the same oldest units inv_take removes; round each unit before summing."""
    if item not in PERISHABLES:
        return n * unit_price
    total = 0
    for batch in inv_batches(inventory, item):
        count = min(n, batch["qty"])
        total += count * max(1, unit_price * (100 + batch["fresh"]) // 200)
        n -= count
        if not n:
            break
    return total


def decay_inventory(inventory):
    spoiled = 0
    # Sort the set to keep world JSON and replay ordering stable across processes.
    for item in sorted(PERISHABLES):
        remaining = []
        for batch in inv_batches(inventory, item):
            batch["fresh"] -= 25
            if batch["fresh"] <= 0:
                spoiled += batch["qty"]
            else:
                remaining.append(batch)
        inventory[item] = remaining
    if spoiled:
        inv_add(inventory, "spoiled", spoiled)
    return spoiled


def valid_inventory(inventory):
    return all(
        (type(value) is int and value >= 0)
        or (
            item in PERISHABLES
            and isinstance(value, list)
            and all(
                isinstance(batch, dict)
                and type(batch.get("qty")) is int
                and batch["qty"] > 0
                and type(batch.get("fresh")) is int
                and 0 <= batch["fresh"] <= 100
                for batch in value
            )
        )
        for item, value in inventory.items()
    )
