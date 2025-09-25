"""
Clean implementation of asyncio with nest_asyncio for Streamlit applications.

This module provides a simple and clean way to run async functions in a Streamlit
environment, where event loops can sometimes cause issues.
"""

import asyncio
import functools
import logging
import nest_asyncio
from typing import Any, Callable, TypeVar, Awaitable, cast

T = TypeVar('T')

# Apply nest_asyncio at module import time to enable nested event loops
_nest_applied = False
try:
    if not _nest_applied:
        nest_asyncio.apply()
        _nest_applied = True
        logging.info("nest_asyncio successfully applied")
except Exception as e:
    logging.warning(f"Failed to apply nest_asyncio: {e}")

def run_async(func):
    """
    A clean decorator to make async functions callable synchronously.

    This decorator properly handles async functions in Streamlit, preventing
    "Event loop is closed" errors by using nest_asyncio.

    Args:
        func: The async function to decorate

    Returns:
        A synchronous wrapper function

    Example:
        @run_async
        async def fetch_data(address):
            # Your async code here
            return result

        # Call it normally:
        result = fetch_data("0x123")
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return run_coroutine(func(*args, **kwargs))
    return wrapper

def run_coroutine(coro: Awaitable[T]) -> T:
    """
    Run a coroutine object safely with nest_asyncio.

    Args:
        coro: A coroutine object to run

    Returns:
        The result of the coroutine
    """
    try:
        # Get the current event loop, or create one if it doesn't exist
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            # "There is no current event loop in thread"
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Run the coroutine and return the result
        return loop.run_until_complete(coro)
    except Exception as e:
        if "cannot reuse already awaited coroutine" in str(e):
            # This is a fatal error, we can't reuse the coroutine
            logging.error(f"Cannot reuse coroutine: {e}")
            raise ValueError("Cannot reuse the same coroutine object. Create a fresh coroutine for each call.")
        else:
            # If all else fails, create a new event loop and try again
            logging.warning(f"Error in run_coroutine, retrying with new event loop: {e}")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)

# Convenience function for one-off coroutine runs
def async_to_sync(coro: Awaitable[T]) -> T:
    """
    Run an async coroutine synchronously and return the result.

    Args:
        coro: The coroutine to run

    Returns:
        The result of the coroutine

    Example:
        result = async_to_sync(client.get_balance("0x123"))
    """
    return run_coroutine(coro)