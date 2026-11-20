from .rules import need, emit, capacity
from .progression import record_progress
from ..catalog import ITEMS


def post_order(w, buyer, item, quantity, unit_price, events):
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
    w["orders"].append(o)
    emit(
        events,
        w,
        buyer,
        "order",
        f"{buyer['name']}发布采购：{quantity}份{ITEMS[item]['name']}",
        order_id=o["id"],
        escrow=total,
    )
    return o


def fill_order(w, seller, order_id, events):
    o = next((o for o in w["orders"] if o["id"] == order_id), None)
    need(o is not None, "订单不存在")
    need(o["status"] == "open", "订单已结束")
    need(o["buyer_id"] != seller["id"], "不能交付自己的订单")
    buyer = w["agents"][o["buyer_id"]]
    need(seller["inventory"][o["item"]] >= o["quantity"], "没有足够的物资")
    need(
        sum(buyer["inventory"].values()) + o["quantity"] <= capacity(w), "买家背包已满，请联系对方"
    )
    seller["inventory"][o["item"]] -= o["quantity"]
    buyer["inventory"][o["item"]] += o["quantity"]
    seller["cash"] += o["escrow"]
    seller["earned"] += o["escrow"]
    paid = o["escrow"]
    o["escrow"] = 0
    o["status"] = "filled"
    o["seller_id"] = seller["id"]
    w["activity_goal"]["trades"] += 1
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
    )


def cancel_order(w, a, order_id, events):
    o = next((o for o in w["orders"] if o["id"] == order_id), None)
    need(o is not None, "订单不存在")
    need(o["buyer_id"] == a["id"], "只能取消自己的订单")
    need(o["status"] == "open", "订单已结束")
    a["cash"] += o["escrow"]
    o["escrow"] = 0
    o["status"] = "cancelled"
    emit(events, w, a, "order", a["name"] + "取消订单，资金已退回", order_id=o["id"])
