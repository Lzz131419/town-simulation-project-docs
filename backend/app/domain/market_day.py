"""Weekly fair, persisted from dawn to dawn without an additional RNG draw."""

from ..balance import balance


def is_market_day(w):
    return w["tick"] < w.get("market_day", {}).get("until_tick", 0)


def advance_market_day(w, events):
    # Called only at dawn. Day numbering intentionally follows tick // 144.
    from .rules import emit

    rules = balance.market_day
    day = w["tick"] // balance.weather.ticks_per_day
    w["market_day"] = {}
    if day > 0 and day % rules.interval_days == 0:
        w["market_day"] = {"until_tick": w["tick"] + rules.duration_ticks}
        emit(events, w, "town", "fortune", rules.opening_text,
             card="market_day", day=day, until_tick=w["market_day"]["until_tick"])
    elif day % rules.interval_days == rules.interval_days - 1:
        emit(events, w, "town", "fortune", rules.preview_text,
             card="market_day_preview", day=day)
