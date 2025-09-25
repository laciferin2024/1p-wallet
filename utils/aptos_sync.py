import requests
import logging
from typing import Any, Dict, List, Optional

from aptos_sdk.async_client import RestClient as AsyncRestClient
from utils.nest_runner import run_async, run_coroutine, async_to_sync


def _run_coro_sync(coro):
    """Run coroutine synchronously, using the clean nest_asyncio implementation.

    This function is kept for backward compatibility and delegates to the more
    clean and robust nest_runner utilities.
    """
    return async_to_sync(coro)


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
