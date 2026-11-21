from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Login(Input):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    username: str = Field(max_length=40)
    password: str = Field(max_length=128)


class Profile(Input):
    bio: str = Field(max_length=500)
    goal: str = Field(min_length=1, max_length=500)


class Policy(Input):
    reserve: int = Field(strict=True, ge=0, le=10000)
    daily_budget: int = Field(strict=True, ge=0, le=500)
    fallback: Literal[
        "work",
        "farm",
        "craft",
        "bake",
        "rest",
        "social",
        "gather",
        "fish",
        "chop",
        "mine",
        "forage",
        "grill",
        "forge",
        "harvest_veg",
        "gather_honey",
        "harvest_flax",
        "weave",
        "assemble",
        "cook",
        "reinforce",
    ] = "work"
    auto_eat: bool = True


class Control(Input):
    mode: Literal["manual", "rules", "plan"]


class Action(Input):
    type: str = Field(min_length=1, max_length=40)
    item: str | None = Field(default=None, min_length=1, max_length=40)
    quantity: int = Field(default=1, strict=True, ge=1, le=10)
    place: str | None = Field(default=None, min_length=1, max_length=40)
    target_id: str | None = Field(default=None, max_length=40)


class Plan(Input):
    actions: list[Action] = Field(max_length=8)


class PlanEdit(Plan):
    expected: list[Action] = Field(max_length=8)


class OrderInput(Input):
    item: Literal[
        "grain",
        "bread",
        "wood",
        "fruit",
        "fish",
        "ore",
        "herb",
        "meal",
        "tool",
        "vegetable",
        "honey",
        "flax",
        "cloth",
        "furniture",
        "soup",
    ]
    quantity: int = Field(strict=True, ge=1, le=10)
    unit_price: int = Field(strict=True, ge=1, le=50)


class MessageInput(Input):
    recipient_id: str = Field(min_length=1, max_length=40)
    text: str = Field(min_length=1, max_length=500)


class ModelInput(Input):
    base_url: str = Field(max_length=300)
    model: str = Field(min_length=1, max_length=160)
    api_key: str = Field(default="", max_length=4000)


class Prompt(Input):
    instruction: str = Field(min_length=1, max_length=1500)


class SaveInput(Input):
    title: str = Field(min_length=1, max_length=80)
