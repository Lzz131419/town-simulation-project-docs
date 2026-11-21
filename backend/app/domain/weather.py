"""Deterministic daily climate and shared production modifiers for JSON worlds."""

from math import ceil

from ..balance import balance
from .rules import emit, need


WEATHER_NAMES = {"sunny": "晴天", "cloudy": "多云", "rain": "雨天", "storm": "暴雨"}
SEASON_NAMES = {"spring": "春季", "summer": "夏季", "autumn": "秋季", "winter": "冬季"}


def is_dawn(w):
    return (w["tick"] + balance.weather.dawn_offset_ticks) % balance.weather.ticks_per_day == 0


def next_random(w):
    """Advance the saved LCG once and return a reproducible unit draw."""
    rules = balance.weather
    w["rng_seed"] = (
        w.get("rng_seed", rules.initial_seed) * rules.rng_multiplier + rules.rng_increment
    ) % rules.rng_modulus
    return w.get("rng_seed", rules.initial_seed) / rules.rng_modulus


def advance_climate(w, events):
    """Called once at each existing day boundary; RNG state survives JSON saves."""
    rules = balance.weather
    roll = next_random(w)
    previous = w.get("weather", "sunny")
    cumulative = 0.0
    for weather, probability in rules.transitions[previous].items():
        cumulative += probability
        if roll < cumulative:
            w["weather"] = weather
            break
    emit(
        events,
        w,
        "town",
        "weather",
        f"今日天气：{WEATHER_NAMES[w.get('weather', 'sunny')]}",
        **{"from": previous, "to": w.get("weather", "sunny")},
    )

    season_ticks = rules.ticks_per_day * balance.season.days_per_season
    if (w["tick"] + rules.dawn_offset_ticks) % season_ticks == 0:
        previous = w.get("season", "spring")
        cycle = balance.season.cycle
        w["season"] = cycle[(cycle.index(previous) + 1) % len(cycle)]
        emit(
            events,
            w,
            "town",
            "season",
            f"季节更替：{SEASON_NAMES[w.get('season', 'spring')]}",
            **{"from": previous, "to": w.get("season", "spring")},
        )
    return roll


def action_available(w, kind):
    return w.get("season", "spring") != "winter" or kind not in balance.season.winter_blocked_actions


def require_available(w, kind):
    need(action_available(w, kind), "冬季农场休耕，请安排其他工作")


def energy_cost(w, kind, base):
    if w.get("weather", "sunny") == "rain" and kind in balance.weather.rain_actions:
        return base + balance.weather.rain_energy_extra
    return base


def production_outputs(w, kind, outputs):
    """Round each output after weather, then after season, in that order."""
    outputs = dict(outputs)
    hints = []
    modifiers = []
    if w.get("weather", "sunny") == "rain" and kind in balance.weather.rain_actions:
        modifiers.append(balance.weather.rain_yield_multiplier)
        hints.append("雨天丰收")
    elif w.get("weather", "sunny") == "storm" and kind == "fish":
        modifiers.append(balance.weather.storm_fish_multiplier)
        hints.append("暴雨渔获增加")
    if w.get("season", "spring") == "summer" and kind in balance.season.farm_actions:
        modifiers.append(balance.season.summer_yield_multiplier)
        hints.append("夏季丰收")
    elif w.get("season", "spring") == "autumn" and kind == "gather":
        modifiers.append(balance.season.autumn_fruit_multiplier)
        hints.append("秋季水果丰收")
    action_modifiers = w.get("action_modifiers", {})
    if w["tick"] < action_modifiers.get("expires_tick", 0) and kind in action_modifiers:
        modifiers.append(action_modifiers[kind])
        hints.append("今日事件增产")
    for multiplier in modifiers:
        outputs = {item: ceil(amount * multiplier) for item, amount in outputs.items()}
    return outputs, hints
