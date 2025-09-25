import logging
from typing import Tuple, Optional

from aptos_sdk.account import Account
from aptos_sdk.transactions import EntryFunction
from aptos_sdk.bcs import Serializer

async def transfer_apt_async(
    sender_account: Account,
    recipient_address: str,
    amount_apt: float,
    client_url: str = "https://testnet.aptoslabs.com/v1"
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Transfer APT from sender to recipient asynchronously.

    Args:
        sender_account: The sender's Account object
        recipient_address: The recipient's address as a string
        amount_apt: Amount of APT to transfer
        client_url: The Aptos node URL

    Returns:
        Tuple of (success_bool, transaction_hash, error_message)
    """
    try:
        # Convert APT to octas
        amount_in_octas = int(amount_apt * 100000000)

        # Create BCS serializer for the amount
        serializer = Serializer()
        serializer.u64(amount_in_octas)
        serialized_amount = serializer.output()

        # Create transaction payload
        payload = EntryFunction.natural(
            "0x1::coin",
            "transfer",
            ["0x1::aptos_coin::AptosCoin"],
            [recipient_address, serialized_amount]
        )

        # Use async client directly
        from aptos_sdk.async_client import RestClient
        client = RestClient(client_url)

        # Create and sign transaction
        txn = await client.create_transaction(sender_account.address(), payload)
        signed_txn = sender_account.sign_transaction(txn)

        # Submit transaction
        txn_hash = await client.submit_transaction(signed_txn)

        # Wait for confirmation
        await client.wait_for_transaction(txn_hash, timeout=30)

        return True, txn_hash, None

    except Exception as e:
        logging.error(f"Transfer failed: {str(e)}")
        return False, None, str(e)


def transfer_apt_sync(
    sender_account: Account,
    recipient_address: str,
    amount_apt: float,
    client_url: str = "https://testnet.aptoslabs.com/v1"
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Synchronous wrapper using nest_asyncio
    """
    # Use our clean nest_asyncio implementation
    from utils.nest_runner import async_to_sync
    return async_to_sync(transfer_apt_async(
        sender_account, recipient_address, amount_apt, client_url
    ))