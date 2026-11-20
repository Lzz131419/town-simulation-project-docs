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


class Needs(BaseModel):
    high_hunger: int = Field(ge=1, le=100)
    rest_gain: int = Field(ge=1, le=100)
    hungry_rest_gain: int = Field(ge=1, le=100)


class Balance(BaseModel):
    fiscal: Fiscal
    simulation: Simulation
    npc: NPC
    needs: Needs


balance = Balance.model_validate(
    json.loads((Path(__file__).resolve().parents[1] / "config/game.json").read_text())
)
