from .perishables import inv_qty, inv_total, inv_take, inv_add
from .rules import need, emit, capacity
from .progression import record_progress
from .memories import remember
from ..catalog import ITEMS
from ..balance import balance
from .reputation import change_reputation


def post_order(w, buyer, item, quantity, unit_price, events, *, private_to=None, total_reward=None):
    need(
        isinstance(item, str)
        and item in ITEMS
        and type(quantity) is int
        and type(unit_price) is int
        and 1 <= quantity <= 10
        and 1 <= unit_price <= 50,
        "订单内容不合法",
    )
    need(
        sum(o["status"] == "open" and o["buyer_id"] == buyer["id"] for o in w["orders"]) < 5,
        "最多同时发布5笔订单",
    )
    total = quantity * unit_price
    if private_to is not None:
        target = w["agents"].get(private_to)
        need(buyer["npc"] and target is not None and not target["npc"], "私人订单对象不合法")
        need(type(total_reward) is int and total_reward >= quantity, "订单报酬不合法")
        total = total_reward
        # The total reward is rounded once, so a private unit quote may be fractional.
        unit_price = total / quantity
    else:
        need(total_reward is None, "公开订单不能指定总报酬")
    need(buyer["cash"] >= total, "余额不足以托管订单资金")
    buyer["cash"] -= total
    o = {
        "id": w["next_order"],
        "buyer_id": buyer["id"],
        "item": item,
        "quantity": quantity,
        "unit_price": unit_price,
        "escrow": total,
        "status": "open",
        "created_tick": w["tick"],
        "expires_tick": w["tick"] + 144,
        "seller_id": None,
    }
    w["next_order"] += 1
    if private_to is not None:
        o["private_to"] = private_to
    w["orders"].append(o)
    text = f"{buyer['name']}发布采购：{quantity}份{ITEMS[item]['name']}"
    if private_to is not None:
        text = f"{buyer['name']}想要{quantity}份{ITEMS[item]['name']}，出{total}镇币"
        remember(w, buyer, f"向{target['name']}发出了私人采购：{quantity}份{ITEMS[item]['name']}")
        remember(w, target, f"收到了{buyer['name']}的私人采购邀请：{quantity}份{ITEMS[item]['name']}")
    emit(
        events,
        w,
        buyer,
        "order",
        text,
        order_id=o["id"],
        escrow=total,
        transaction_type="posted",
        item=item,
        quantity=quantity,
        unit_price=unit_price,
        amount=total,
        **({"private_to": private_to} if private_to is not None else {}),
    )
    return o


def fill_order(w, seller, order_id, events):
    o = next((o for o in w["orders"] if o["id"] == order_id), None)
    need(o is not None, "订单不存在")
    need(o["status"] == "open", "订单已结束")
    need(o["buyer_id"] != seller["id"], "不能交付自己的订单")
    need(o.get("private_to") in (None, seller["id"]), "这笔私人订单只邀请了指定居民")
    buyer = w["agents"][o["buyer_id"]]
    need(inv_qty(seller["inventory"], o["item"]) >= o["quantity"], "没有足够的物资")
    need(inv_total(buyer["inventory"]) + o["quantity"] <= capacity(w, buyer), "买家背包已满，请联系对方")
    batches = inv_take(seller["inventory"], o["item"], o["quantity"])
    for batch in batches:
        inv_add(buyer["inventory"], o["item"], batch["qty"], batch["fresh"])
    seller["cash"] += o["escrow"]
    seller["earned"] += o["escrow"]
    paid = o["escrow"]
    o["escrow"] = 0
    o["status"] = "filled"
    o["seller_id"] = seller["id"]
    if o.get("private_to") is not None:
        change_reputation(w, seller, balance.reputation.private_order_gain, "private_order", events)
    w["activity_goal"]["trades"] += 1
    goods = f"{o['quantity']}个{ITEMS[o['item']]['name']}"
    remember(w, seller, f"向{buyer['name']}出售了{goods}")
    remember(w, buyer, f"向{seller['name']}购买了{goods}")
    record_progress(w, seller, "delivery", events)
    emit(
        events,
        w,
        seller,
        "order",
        f"{seller['name']}向{buyer['name']}交付订单，获得{paid}镇币",
        order_id=o["id"],
        buyer=buyer["id"],
        amount=paid,
        item=o["item"],
        quantity=o["quantity"],
        unit_price=paid / o["quantity"],
        transaction_type="filled",
    )


def cancel_order(w, a, order_id, events):
    o = next((o for o in w["orders"] if o["id"] == order_id), None)
    need(o is not None, "订单不存在")
    need(o["buyer_id"] == a["id"], "只能取消自己的订单")
    need(o["status"] == "open", "订单已结束")
    refund = o["escrow"]
    a["cash"] += refund
    o["escrow"] = 0
    o["status"] = "cancelled"
    emit(
        events,
        w,
        a,
        "order",
        a["name"] + "取消订单，资金已退回",
        order_id=o["id"],
        refund=refund,
        transaction_type="cancelled",
    )
