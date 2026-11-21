"""JSON-only sleep state, rolling 48-hour history, and additive fatigue costs."""

from ..balance import balance
from .homes import home_destination, claim_home, sleep_multiplier, owned_home
from .rules import emit, need
from .weather import energy_cost


def energy_limit(a):
    return balance.sleep.fatigue_energy_cap if a.get("fatigue") else 100


def action_energy_cost(w, a, kind, base):
    # T1 weather first: base + rain extra; then fatigue +2. No multiplication.
    return energy_cost(w, kind, base) + (
        balance.sleep.fatigue_energy_extra if a.get("fatigue") else 0
    )


def sleep_hours(a):
    bedtime = balance.npc.sleep_hour
    if a.get("personality") == "introvert":
        bedtime -= balance.sleep.introvert_bedtime_advance
    elif a.get("personality") == "sociable":
        bedtime += balance.sleep.sociable_bedtime_delay
    return balance.npc.wake_hour, bedtime


def at_bedtime(w, a):
    hour = ((w["tick"] * 10 + 480) % 1440) / 60
    wake, bed = sleep_hours(a)
    return hour < wake or hour >= bed


def wake_energy(a):
    return (
        balance.sleep.diligent_wake_energy
        if a.get("personality") == "diligent"
        else balance.sleep.wake_energy
    )


def begin_sleep(w, a, events):
    home = home_destination(w, a)
    need(abs(a["x"] - home["x"]) + abs(a["y"] - home["y"]) < 1, "请先回到家中再睡觉")
    claim_home(w, a, events)
    a["sleeping"] = {"since_tick": w["tick"], "phase": "light"}
    a["path"] = []
    a["task"] = None
    a["activity"] = "在家浅睡" if owned_home(w, a) else "在广场长椅浅睡"
    emit(events, w, a, "sleep", f"{a['name']}{'回家躺下' if owned_home(w, a) else '在广场长椅躺下'}，入睡了", phase="light")


def wake(w, a, events, reason, disturber=None):
    duration = w["tick"] - a["sleeping"]["since_tick"]
    a["sleeping"] = None
    a["activity"] = "醒来，准备新的一天"
    # Do not let a later agent iteration immediately send the sleeper back to bed.
    a["next_action_tick"] = w["tick"] + 1
    text = f"{a['name']}醒来了"
    if disturber is not None:
        text = f"{a['name']}被吵醒了"
        for person, other in ((a, disturber), (disturber, a)):
            from .family import change_relation
            change_relation(person, other, -balance.sleep.disturb_relation_loss)
    a["last_outcome"] = text
    emit(
        events,
        w,
        a,
        "wake",
        text,
        reason=reason,
        duration_ticks=duration,
        **(
            {
                "partner_id": disturber["id"],
                "relationship_change": -balance.sleep.disturb_relation_loss,
            }
            if disturber
            else {}
        ),
    )


def disturb(w, target, actor, events):
    if not target.get("sleeping"):
        return False
    wake(w, target, events, "disturbed", actor)
    return True


def advance_sleep(w, a, events):
    """Called once per tick, before movement or decisions (including manual players)."""
    rules = balance.sleep
    tick = w["tick"]
    history = a["sleep_history"]
    history[:] = [t for t in history if t > tick - rules.deprivation_window_ticks]
    sleeping = a.get("sleeping")
    if sleeping:
        history.append(tick)
    if (
        not a.get("fatigue")
        and tick - a["sleep_tracking_since"] >= rules.deprivation_window_ticks
        and len(history) < rules.minimum_sleep_ticks
    ):
        a["fatigue"] = 1
        emit(
            events,
            w,
            a,
            "fatigue",
            f"{a['name']}连续两天睡眠不足，感到疲劳",
            energy_cap=rules.fatigue_energy_cap,
        )
    if not sleeping:
        a["energy"] = min(energy_limit(a), a["energy"])
        return False
    duration = tick - sleeping["since_tick"]
    if a.get("fatigue") and duration >= rules.recovery_ticks:
        a["fatigue"] = 0
        emit(events, w, a, "fatigue_recovered", f"{a['name']}睡足了，疲劳消除了")
    # The first 12 completed intervals receive light gain; interval 13 onward deep.
    gain = rules.light_gain if duration <= rules.light_ticks else rules.deep_gain
    a["energy"] = min(energy_limit(a), round(a["energy"] + gain * sleep_multiplier(w, a), 2))
    if duration >= rules.light_ticks and sleeping["phase"] != "deep":
        sleeping["phase"] = "deep"
        a["activity"] = "在家熟睡" if owned_home(w, a) else "在广场长椅熟睡"
        emit(events, w, a, "sleep_phase", f"{a['name']}进入深睡", phase="deep")
    minute = (tick * 10 + 480) % 1440
    if a["energy"] >= wake_energy(a):
        wake(w, a, events, "restored")
    elif minute == balance.npc.wake_hour * 60:
        wake(w, a, events, "morning")
    elif duration >= rules.max_ticks:
        wake(w, a, events, "maximum_duration")
    return True
