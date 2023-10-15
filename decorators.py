from functools import wraps
import time


def timer_function(func: callable):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        print(f"Function {func.__name__} took {end_time - start_time} seconds to run")
        return result

    return wrapper


def log_arguments(func: callable):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__} with {kwargs}")
        return await func(*args, **kwargs)

    return wrapper
