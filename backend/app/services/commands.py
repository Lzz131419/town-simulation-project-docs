from ..schemas import Action, Control, Policy, Plan, PlanEdit
from ..engine import start_action, validate_action, emit
from .container import runtime
from ..domain.rules import need
from ..domain.plans import append_plan, edit_plan


async def action(uid: str, data: Action):
    runtime.cancel_calls(uid)

    def apply(w, events):
        a = w["agents"][uid]
        a["mode"] = "manual"
        a["path"] = []
        a["task"] = None
        start_action(w, a, data.model_dump(exclude_none=True), events)

    await runtime.mutate(apply)
    return {"ok": True}


async def control(uid: str, data: Control):
    runtime.cancel_calls(uid)

    def apply(w, events):
        a = w["agents"][uid]
        if data.mode == "plan":
            need(bool(a["plan"] or a["task"]), "先向计划加入至少一个行动")
        a["mode"] = data.mode
        if data.mode != "manual":
            a["next_action_tick"] = w["tick"]
        if data.mode == "manual":
            a["path"] = []
            a["task"] = None
            a["activity"] = "等待新安排"
        emit(
            events,
            w,
            a,
            "control",
            a["name"] + {
                "rules": "启用了计划与规则托管",
                "plan": "开始执行本轮计划，完成后停止",
                "manual": "接管了自己的居民",
            }[data.mode],
        )

    await runtime.mutate(apply)
    return {"ok": True}


async def policy(uid: str, data: Policy):
    runtime.cancel_calls(uid)
    await runtime.mutate(lambda w, e: w["agents"][uid].update(policy=data.model_dump()))
    return {"ok": True}


async def plan(uid: str, data: Plan):
    runtime.cancel_calls(uid)
    actions = [validate_action(a.model_dump(exclude_none=True)) for a in data.actions]
    await runtime.mutate(lambda w, e: w["agents"][uid].update(plan=actions))
    return {"ok": True}


async def append(uid: str, data: Plan):
    runtime.cancel_calls(uid)
    actions = [a.model_dump(exclude_none=True) for a in data.actions]
    await runtime.mutate(lambda w, e: append_plan(w["agents"][uid], actions))
    return {"ok": True}


async def edit(uid: str, data: PlanEdit):
    runtime.cancel_calls(uid)
    expected = [a.model_dump(exclude_none=True) for a in data.expected]
    actions = [a.model_dump(exclude_none=True) for a in data.actions]
    await runtime.mutate(lambda w, e: edit_plan(w["agents"][uid], expected, actions))
    return {"ok": True}
