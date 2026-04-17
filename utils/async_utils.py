"""
Async utilities module.
Provides safe async execution from synchronous contexts.
"""

import asyncio


class AsyncTimeoutError(Exception):
    """Custom exception for async timeout errors."""
    pass


def run_async(coro, timeout=15):
    """
    Safely run an async coroutine from a synchronous context.
    
    Args:
        coro: The coroutine to run
        timeout: Timeout in seconds (default 15)
    
    Returns:
        The result of the coroutine
    
    Raises:
        AsyncTimeoutError: If the coroutine times out
        Exception: Any exception from the coroutine
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    else:
        # Running loop exists, run in thread
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        try:
            return future.result(timeout=timeout)
        except asyncio.TimeoutError as e:
            raise AsyncTimeoutError(
                f"Coroutine timed out after {timeout} seconds"
            ) from e
