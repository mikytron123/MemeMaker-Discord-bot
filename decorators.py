import time
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def timer_function(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs):
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        print(f"Function {func.__name__} took {end_time - start_time} seconds to run")
        return result

    return wrapper


def log_arguments(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs):
        print(f"Calling {func.__name__} with {kwargs}")
        return await func(*args, **kwargs)

    return wrapper
