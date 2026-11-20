"""Bounded personal queues and finite execution; no model or network access."""

from .actions import validate_action
from .rules import need, emit

MAX_PLAN_STEPS = 8


def normalize(actions):
    need(len(actions) <= MAX_PLAN_STEPS, "计划最多保存8步")
    return [validate_action(action) for action in actions]


def append_plan(a, actions):
    additions = normalize(actions)
    need(bool(additions), "请选择要加入的行动")
    need(len(a["plan"]) + len(additions) <= MAX_PLAN_STEPS, "计划已满，最多保存8步")
    a["plan"] = [*a["plan"], *additions]


def edit_plan(a, expected, actions):
    # Compare within the same world transaction: a running tick/another tab may pop a step.
    expected, actions = normalize(expected), normalize(actions)
    need(normalize(a["plan"]) == expected, "计划已变化，请同步后重试")
    a["plan"] = actions


def finish_plan(w, a, events):
    if a["mode"] == "plan" and not a["plan"] and not a["task"]:
        a["mode"] = "manual"
        a["activity"] = "本轮计划已完成"
        emit(events, w, a, "plan_done", a["name"] + "完成了本轮行动计划")


def pause_failed_plan(w, a, events):
    if a["mode"] == "plan":
        a["mode"] = "manual"
        a["activity"] = "计划已暂停"
        emit(events, w, a, "plan_paused", a["name"] + "的行动失败，剩余计划已暂停")
