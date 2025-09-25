import asyncio
import concurrent.futures
import requests
import logging
from typing import Any, Dict, List, Optional

from aptos_sdk.async_client import RestClient as AsyncRestClient


def _run_coro_sync(coro):
    """Run coroutine synchronously, even if an event loop is already running.

    This version is completely thread-safe and ensures a fresh event loop for each call,
    preventing "Event loop is closed" errors in Streamlit.
    """
    # Always use a thread to isolate event loop lifecycle
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(lambda: _run_in_new_loop(coro))
        try:
            return future.result(timeout=60)  # 60-second timeout to prevent hangs
        except concurrent.futures.TimeoutError:
            raise TimeoutError("Async operation timed out after 60 seconds")

def sync_wrapper(async_func):
    """A safe decorator for wrapping async functions to be called synchronously.

    This wrapper is safe for Streamlit and other environments where event loops may be
    closed or reused between calls. It ensures each async operation runs in isolation.

    Example:
        @sync_wrapper
        async def fetch_data(param1, param2):
            # async code here

        # Call it synchronously
        result = fetch_data(arg1, arg2)
    """
    def wrapper(*args, **kwargs):
        coro = async_func(*args, **kwargs)
        return _run_coro_sync(coro)
    return wrapper

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
        # Use a completely fresh call each time to avoid event loop issues
        try:
            return _run_coro_sync(self._client.account_resources(address))
        except Exception as e:
            if "Event loop is closed" in str(e):
                # If we get the specific error, recreate client and retry
                self._client = AsyncRestClient(self._client.base_url)
                return _run_coro_sync(self._client.account_resources(address))
            raise

    def create_transaction(self, sender: str, payload: Any) -> Any:
        return _run_coro_sync(self._client.create_transaction(sender, payload))

    def submit_transaction(self, signed_txn: Any) -> Any:
        return _run_coro_sync(self._client.submit_transaction(signed_txn))

    def wait_for_transaction(self, txn_hash: str, timeout: int = 30) -> Any:
        return _run_coro_sync(self._client.wait_for_transaction(txn_hash, timeout))

    def get_account_transactions(self, address: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch transaction history for an account

        This method makes a direct HTTP request since AsyncRestClient doesn't have this method.
        """
        try:
            # Extract base URL from client
            base_url = self._client.base_url
            if base_url.endswith('/'):
                base_url = base_url[:-1]

            # Construct the API endpoint URL
            url = f"{base_url}/accounts/{address}/transactions"

            # Set up query parameters
            params = {
                'limit': limit
            }

            # Make the HTTP request
            response = requests.get(url, params=params)

            # Check if the request was successful
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"Error fetching transactions: HTTP {response.status_code}: {response.text}")
                return []

        except Exception as e:
            logging.error(f"Error in get_account_transactions: {str(e)}")
            return []

    def __getattr__(self, name: str):
        # Fallback to underlying client attributes if needed
        return getattr(self._client, name)
