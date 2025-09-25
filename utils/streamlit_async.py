"""
Utilities for making Streamlit work better with async operations.
This module provides functions to help execute async code in Streamlit.
"""

import asyncio
import concurrent.futures
import functools
import threading
import nest_asyncio
from typing import Any, Callable, TypeVar, cast

T = TypeVar('T')

# Apply nest_asyncio to allow nested event loops
try:
    nest_asyncio.apply()
except ImportError:t
    pass  # If nest_asyncio isn't available, continue without it


def run_async(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to safely run an async function in Streamlit.
    This decorator handles the complexities of running async code in Streamlit,
    which can have issues with event loops.

    Args:
        func: The async function to run

    Returns:
        A wrapper function that can be called synchronously
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return run_in_thread_pool(lambda: run_in_executor(func, *args, **kwargs))
    return wrapper


def run_in_thread_pool(func: Callable[[], T]) -> T:
    """
    Run a function in a thread pool to isolate it from Streamlit's event loop.

    Args:
        func: The function to run

    Returns:
        The result of the function
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func)
        return cast(T, future.result(timeout=60))  # 60 second timeout


def run_in_executor(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """
    Run an async function in a new event loop within the current thread.

    Args:
        func: The async function to run
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The result of the async function
    """
    async_result = None
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        if asyncio.iscoroutinefunction(func):
            # If it's already an async function
            coro = func(*args, **kwargs)
        else:
            # If it's a regular function that returns a coroutine
            coro = func(*args, **kwargs)

        async_result = loop.run_until_complete(coro)
    finally:
        try:
            if loop and not loop.is_closed():
                loop.close()
        except Exception:
            pass  # Ignore errors while closing the loop

    return async_result


# Example usage:
# @run_async
# async def fetch_data_from_blockchain(address):
#     # Your async code here
#     return result
#
# # Then in your Streamlit app:
# data = fetch_data_from_blockchain("0x123...")