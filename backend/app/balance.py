"""Validated game rules, loaded once at startup and published in the catalog."""

import json
from pathlib import Path
from pydantic import BaseModel, Field


class Fiscal(BaseModel):
    daily_surplus_rate: float = Field(ge=0, le=0.2)
    protected_cash: int = Field(ge=0)


class Simulation(BaseModel):
    sample_interval_ticks: int = Field(ge=1)
    history_limit: int = Field(ge=12, le=10000)
    retry_delay_ticks: int = Field(ge=1, le=144)


class NPC(BaseModel):
    wake_hour: int = Field(ge=0, le=23)
    social_start_hour: int = Field(ge=0, le=23)
    social_end_hour: int = Field(ge=0, le=23)
    sleep_hour: int = Field(ge=0, le=23)
    small_talk: tuple[str, str, str] = (
        "今天镇上的风真舒服。",
        "有空一起去河边走走吧。",
        "希望明天也是个好天气。",
    )


class Leisure(BaseModel):
    probability: float = Field(default=0.4, ge=0, le=1)
    diligent_multiplier: float = Field(default=0.5, ge=0, le=1)
    morning_hours: float = Field(default=1, gt=0, le=3)
    afternoon_start: int = Field(default=15, ge=0, le=23)
    afternoon_end: int = Field(default=17, ge=1, le=24)
    evening_start: int = Field(default=19, ge=0, le=23)
    evening_end: int = Field(default=21, ge=1, le=24)
    stay_ticks: int = Field(default=2, ge=1, le=6)


class Needs(BaseModel):
    high_hunger: int = Field(ge=1, le=100)
    rest_gain: int = Field(ge=1, le=100)
    hungry_rest_gain: int = Field(ge=1, le=100)
    hunger_interval_ticks: int = Field(default=6, ge=1)
    hunger_gain: int = Field(default=3, ge=0)


class Sleep(BaseModel):
    light_ticks: int = Field(default=12, ge=1)
    light_gain: int = Field(default=7, ge=1)
    deep_gain: int = Field(default=10, ge=1)
    wake_energy: int = Field(default=95, ge=1, le=100)
    diligent_wake_energy: int = Field(default=100, ge=1, le=100)
    max_ticks: int = Field(default=36, ge=1)
    deprivation_window_ticks: int = Field(default=288, ge=1)
    minimum_sleep_ticks: int = Field(default=24, ge=1)
    fatigue_energy_cap: int = Field(default=80, ge=1, le=100)
    fatigue_energy_extra: int = Field(default=2, ge=0)
    recovery_ticks: int = Field(default=30, ge=1)
    disturb_relation_loss: int = Field(default=1, ge=0)
    introvert_bedtime_advance: int = Field(default=2, ge=0, le=3)
    sociable_bedtime_delay: int = Field(default=1, ge=0, le=2)
    sociable_social_extension: int = Field(default=1, ge=0, le=3)


class HomeUpgrade(BaseModel):
    wood: int = Field(ge=1)
    cash: int = Field(ge=1)


class Homes(BaseModel):
    upgrades: dict[int, HomeUpgrade] = Field(default_factory=lambda: {
        1: HomeUpgrade(wood=15, cash=60), 2: HomeUpgrade(wood=30, cash=150),
    })
    capacity_per_level: int = Field(default=10, ge=0)
    sleep_multipliers: tuple[float, float, float] = (1.0, 1.3, 1.6)
    bench_sleep_multiplier: float = Field(default=0.5, gt=0, lt=1)
    dawn_hunger_relief: int = Field(default=5, ge=0)


class Family(BaseModel):
    baseline: int = Field(default=80, ge=20, le=100)
    relation_floor: int = Field(default=20, ge=0, le=100)
    meal_radius: float = Field(default=48, gt=0)
    meal_hunger_relief: int = Field(default=15, ge=0)
    meal_relation_gain: int = Field(default=2, ge=0)
    meals_per_week: int = Field(default=5, ge=1, le=7)
    quarrel_threshold: int = Field(default=40, ge=0, le=100)
    quarrel_probability: float = Field(default=0.15, ge=0, le=1)
    quarrel_hunger: int = Field(default=5, ge=0)
    reconciliation_ticks: int = Field(default=288, ge=1)
    reconciliation_gain: int = Field(default=10, ge=0)
    invite_threshold: int = Field(default=60, ge=0, le=100)
    invite_probability: float = Field(default=0.25, ge=0, le=1)
    invite_duration_ticks: int = Field(default=48, ge=1)
    invite_cooldown_ticks: int = Field(default=432, ge=1)
    invite_relation_gain: int = Field(default=8, ge=0)
    invite_hunger_relief: int = Field(default=10, ge=0)
    invite_expiry_loss: int = Field(default=2, ge=0)


class Weather(BaseModel):
    initial_seed: int = Field(default=42, ge=0)
    rng_multiplier: int = Field(default=1103515245, ge=1)
    rng_increment: int = Field(default=12345, ge=0)
    rng_modulus: int = Field(default=2**31, ge=1)
    ticks_per_day: int = Field(default=144, ge=1)
    dawn_offset_ticks: int = Field(default=48, ge=0)
    transitions: dict[str, dict[str, float]] = Field(default_factory=lambda: {
        "sunny": {"sunny": .5, "cloudy": .3, "rain": .15, "storm": .05},
        "cloudy": {"sunny": .35, "cloudy": .3, "rain": .25, "storm": .1},
        "rain": {"sunny": .3, "cloudy": .35, "rain": .25, "storm": .1},
        "storm": {"sunny": .25, "cloudy": .35, "rain": .3, "storm": .1},
    })
    rain_actions: tuple[str, ...] = ("farm", "harvest_veg", "harvest_flax", "gather")
    rain_yield_multiplier: float = Field(default=1.5, ge=1)
    rain_energy_extra: int = Field(default=3, ge=0)
    storm_fish_multiplier: float = Field(default=2, ge=1)


class Season(BaseModel):
    days_per_season: int = Field(default=4, ge=1)
    cycle: tuple[str, ...] = ("spring", "summer", "autumn", "winter")
    farm_actions: tuple[str, ...] = ("farm", "harvest_veg", "harvest_flax")
    summer_yield_multiplier: float = Field(default=1.3, ge=1)
    summer_hunger_gain: int = Field(default=4, ge=0)
    autumn_fruit_multiplier: float = Field(default=2, ge=1)
    winter_blocked_actions: tuple[str, ...] = (
        "farm", "harvest_veg", "harvest_flax", "gather", "gather_honey",
    )


class Pricing(BaseModel):
    basic_target_stock: int = Field(default=20, ge=1)
    processed_target_stock: int = Field(default=8, ge=1)
    basic_items: tuple[str, ...] = ("grain", "bread", "vegetable", "fruit", "fish", "wood")


class Events(BaseModel):
    weights: dict[str, int] = Field(default_factory=lambda: {
        "caravan": 25, "bees": 20, "flood": 15, "dispute": 20, "peaceful": 20,
    })
    caravan_items: tuple[str, ...] = ("tool", "cloth")
    caravan_factor: float = Field(default=0.8, gt=0, le=1)
    honey_factor: float = Field(default=3, ge=1)
    bridge_closed_ticks: int = Field(default=24, ge=1)
    dispute_loss: int = Field(default=20, ge=0, le=100)
    interaction_interval_ticks: int = Field(default=6, ge=1)
    order_relation: int = Field(default=60, ge=0, le=100)
    order_cooldown_ticks: int = Field(default=36, ge=1)
    order_quantity: int = Field(default=2, ge=1, le=10)
    order_reward_factor: float = Field(default=1.2, ge=1)
    order_items: tuple[str, ...] = ("fish", "bread", "fruit", "vegetable", "honey")
    gift_relation: int = Field(default=80, ge=0, le=100)
    gift_cooldown_ticks: int = Field(default=144, ge=1)
    gift_range: float = Field(default=100, gt=0)
    food_items: tuple[str, ...] = ("bread", "fruit", "vegetable", "fish", "honey", "soup", "meal")
    feast_start_hour: int = Field(default=18, ge=0, le=23)
    feast_end_hour: int = Field(default=19, ge=1, le=24)
    feast_radius: float = Field(default=100, gt=0)
    feast_min_agents: int = Field(default=3, ge=2)
    feast_hunger_relief: int = Field(default=20, ge=0, le=100)
    feast_relation_gain: int = Field(default=3, ge=0, le=100)


class MarketDay(BaseModel):
    interval_days: int = Field(default=7, ge=2)
    duration_ticks: int = Field(default=144, ge=1)
    sell_multiplier: float = Field(default=1.1, ge=1)
    delivery_multiplier: int = Field(default=2, ge=1)
    progress_multiplier: int = Field(default=2, ge=1)
    social_radius: float = Field(default=80, gt=0)
    social_bonus: int = Field(default=2, ge=0)
    preview_text: str = "明日是集市日：交易免税，交付酬劳加倍，广场将摆出集市摊位"
    opening_text: str = "集市日开场！本镇无交易税，今日卖价上浮10%，公共交付酬劳与成长加倍，欢迎来广场赶集"


class Reputation(BaseModel):
    delivery_gain: int = Field(default=2, ge=0)
    gift_gain: int = Field(default=5, ge=0)
    private_order_gain: int = Field(default=3, ge=0)
    private_order_expiry_loss: int = Field(default=3, ge=0)
    daily_limit: int = Field(default=10, ge=1)
    titles: dict[int, str] = Field(default_factory=lambda: {
        20: "可靠的", 50: "巧手的", 100: "慷慨的",
    })
    discount_threshold: int = Field(default=50, ge=0)
    buy_multiplier: float = Field(default=0.95, gt=0, le=1)


class Flood(BaseModel):
    """Cooperative flood response rules, kept separate from the card/event rules."""

    goal: int = Field(default=30, ge=1)
    deadline_ticks: int = Field(default=12, ge=1)
    wood_per_contribution: int = Field(default=2, ge=1)
    energy: int = Field(default=4, ge=0)
    failure_bridge_multiplier: int = Field(default=2, ge=1)
    market_loss_rate: float = Field(default=0.2, gt=0, le=1)


class Balance(BaseModel):
    fiscal: Fiscal
    simulation: Simulation
    npc: NPC
    leisure: Leisure = Field(default_factory=Leisure)
    needs: Needs
    sleep: Sleep = Field(default_factory=Sleep)
    homes: Homes = Field(default_factory=Homes)
    family: Family = Field(default_factory=Family)
    weather: Weather = Field(default_factory=Weather)
    season: Season = Field(default_factory=Season)
    pricing: Pricing = Field(default_factory=Pricing)
    events: Events = Field(default_factory=Events)
    market_day: MarketDay = Field(default_factory=MarketDay)
    reputation: Reputation = Field(default_factory=Reputation)
    flood: Flood = Field(default_factory=Flood)


balance = Balance.model_validate(
    json.loads((Path(__file__).resolve().parents[1] / "config/game.json").read_text())
)
