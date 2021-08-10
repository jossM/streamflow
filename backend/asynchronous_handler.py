from typing import Type, Callable
import asyncio

def make_async(synchronous_function: Callable[Any, _T]):
    async def wrapper(*args, **kwargs):
        return asyncio.to_thread(synchronous_function, *args, **kwargs)
