"""Drain synchronous work before propagating cancellation or releasing a world lock."""

import asyncio
from typing import Callable, ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


async def settled_thread(fn: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> tuple[T, bool]:
    task = asyncio.create_task(asyncio.to_thread(fn, *args, **kwargs))
    cancelled = False
    while True:
        try:
            return await asyncio.shield(task), cancelled
        except asyncio.CancelledError:
            cancelled = True
            if task.done():
                return task.result(), cancelled


async def run_blocking(fn: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    result, cancelled = await settled_thread(fn, *args, **kwargs)
    if cancelled:
        raise asyncio.CancelledError
    return result
