import asyncio
import concurrent.futures
from typing import Any

from aptos_sdk.async_client import RestClient as AsyncRestClient


def _run_coro_sync(coro):
    """Run coroutine synchronously, even if an event loop is already running.

    This version is more robust against the "Event loop is closed" error that can
    occur in Streamlit when reusing an event loop.
    """
    try:
        # First try with asyncio.run (simplest approach)
        return asyncio.run(coro)
    except RuntimeError as e:
        # Handle "asyncio.run cannot be called from a running event loop"
        if "cannot be called from a running event loop" in str(e):
            try:
                # Get the current event loop
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    # Create a new loop if the current one is closed
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                # Run the coroutine in the current or new loop
                return loop.run_until_complete(coro)
            except Exception as inner_e:
                # If that also fails, try with a thread
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                    future = ex.submit(lambda: _run_in_new_loop(coro))
                    return future.result()
        else:
            # For other RuntimeErrors, try with a thread
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(lambda: _run_in_new_loop(coro))
                return future.result()

def _run_in_new_loop(coro):
    """Helper function to run a coroutine in a completely new event loop."""
    # Create a new loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Run the coroutine
        return loop.run_until_complete(coro)
    finally:
        # Clean up properly
        loop.close()


class RestClientSync:
    """A tiny sync wrapper around aptos_sdk.async_client.RestClient.

    This runs async calls via a safe sync runner to provide a synchronous API
    suitable for Streamlit scripts. Add more proxy methods as needed.
    """

    def __init__(self, node_url: str):
        self._client = AsyncRestClient(node_url)

    def account(self, address: str) -> Any:
        return _run_coro_sync(self._client.account(address))

    def account_resources(self, address: str) -> Any:
        return _run_coro_sync(self._client.account_resources(address))

    def create_transaction(self, sender: str, payload: Any) -> Any:
        return _run_coro_sync(self._client.create_transaction(sender, payload))

    def submit_transaction(self, signed_txn: Any) -> Any:
        return _run_coro_sync(self._client.submit_transaction(signed_txn))

    def wait_for_transaction(self, txn_hash: str, timeout: int = 30) -> Any:
        return _run_coro_sync(self._client.wait_for_transaction(txn_hash, timeout))

    def get_account_transactions(self, address: str, limit: int = 20) -> Any:
        """Fetch transaction history for an account"""
        return _run_coro_sync(self._client.get_account_transactions(address, limit=limit))

    def __getattr__(self, name: str):
        # Fallback to underlying client attributes if needed
        return getattr(self._client, name)
