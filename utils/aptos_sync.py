import asyncio
import concurrent.futures
from typing import Any

from aptos_sdk.async_client import RestClient as AsyncRestClient


def _run_coro_sync(coro):
    """Run coroutine synchronously, even if an event loop is already running.

    If called from a thread that has an active event loop (e.g., some Streamlit
    environments), we execute asyncio.run in a new thread so it can create and
    manage its own loop.
    """
    try:
        return asyncio.run(coro)
    except RuntimeError:
        # Likely "asyncio.run() cannot be called from a running event loop"
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(asyncio.run, coro)
            return future.result()


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

    def __getattr__(self, name: str):
        # Fallback to underlying client attributes if needed
        return getattr(self._client, name)
