"""Source-independent reputation, with one shared absolute daily change budget."""

from ..balance import balance
from .rules import emit


def reset_reputation_day(w, agent):
    day = (w["tick"] + balance.weather.dawn_offset_ticks) // balance.weather.ticks_per_day
    if agent.get("reputation_day") != day:
        agent["reputation_day"] = day
        agent["reputation_changed_today"] = 0


def change_reputation(w, agent, delta, reason, events):
    reset_reputation_day(w, agent)
    remaining = max(0, balance.reputation.daily_limit - agent["reputation_changed_today"])
    actual = min(abs(delta), remaining) * (1 if delta >= 0 else -1)
    if actual:
        agent["reputation"] = agent.get("reputation", 0) + actual
        agent["reputation_changed_today"] += abs(actual)
        emit(
            events, w, agent, "reputation",
            f"{agent['name']}声望{actual:+d}，当前声望{agent['reputation']}",
            delta=actual, reason=reason, total=agent["reputation"],
        )
    return actual


def reputation_title(score):
    return next(
        (title for threshold, title in sorted(balance.reputation.titles.items(), reverse=True)
         if score >= threshold),
        "",
    )


def project_agent(agent):
    return {**agent, "title": reputation_title(agent.get("reputation", 0))}
