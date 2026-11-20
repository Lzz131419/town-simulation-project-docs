"""Public simulation API. Domain implementations are separated by responsibility."""

from .domain.rules import need, emit, capacity, check_invariants
from .domain.actions import validate_action, start_action, execute
from .domain.scheduler import fallback_action, tick_world
from .domain.orders import post_order, fill_order, cancel_order

__all__ = [
    "need",
    "emit",
    "capacity",
    "check_invariants",
    "validate_action",
    "start_action",
    "execute",
    "fallback_action",
    "tick_world",
    "post_order",
    "fill_order",
    "cancel_order",
]
