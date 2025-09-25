import logging
import os
from dataclasses import dataclass, field
import time
import string
import secrets
import hashlib
from queue import Queue
from typing import List, Dict, Optional

import streamlit as st
from aptos_sdk.async_client import RestClient
from aptos_sdk.account import Account
from aptos_sdk.transactions import EntryFunction
from aptos_sdk.bcs import Serializer
from ecdsa import SigningKey, VerifyingKey, SECP256k1
from ecdsa.util import sigencode_der, sigdecode_der
from collections import defaultdict
from itertools import islice
import random
from dotenv import load_dotenv

from pages import initApp

# Load environment variables
load_dotenv()

# UTF-8 character domains for elegant password selection
DOMAINS = {
    'ascii': string.ascii_letters + string.digits,
    'symbols': '!@#$%^&*()_+-=[]{}|;:,.<>?',
    'emojis': "😀😂❤️👍🙏😍😭😅🎉🔥💯😎🤔🤦😴🤖👀✨✅🚀💎🌟⭐💫🎯🎨🎪🎸🎵🎶🏆🏅🎊🎈🎁🎀🌈🌸🌺🌻🌷🌹",
    'hearts': "💖💝💘💗💓💕💞💜🧡💛💚💙🤍🖤🤎❣️💋",
    'nature': "🌳🌲🌴🌿🍀🌾🌻🌺🌸🌷🌹🌼🌵🌱🍃🌿🦋🐝🐞🕷️",
    'food': "🍎🍌🍇🍓🍈🍉🍊🍋🥭🍑🍒🥝🍍🥥🍅🥑🍆🥔🥕🌽",
    'animals': "🐶🐱🐭🐹🐰🦊🐻🐼🐨🦁🐯🐮🐷🐸🐵🐔🐧🦆🦉🦅🐺🐗🐴",
    'travel': "✈️🚆🚂🚄🚘🚲🛴🛵🏍️🚕🚖🚁🚀🛸🚢🚤🏝️🏖️🏔️⛰️🏕️🌋",
    'sports': "⚽⚾🏀🏐🏈🏉🎾🏓🏸🥊🥋⛳🏌️‍♂️🏄‍♀️🏊‍♀️🧗‍♂️🚴‍♀️🏆🏅🥇🥈🥉",
    'tech': "📱💻⌨️🖥️🖨️💾💿📷🔌📡🔋🔬🔭📚📝✏️🔍🔑🔒",
    'music': "🎵🎶🎸🎹🎷🎺🎻🥁🎼🎤🎧📻🎙️🎚️🎛️",
    'weather': "☀️🌤️⛅🌥️☁️🌦️🌧️⛈️🌩️🌨️❄️💨☃️⛄🌬️🌀🌈☔⚡",
    'zodiac': "♈♉♊♋♌♍♎♏♐♑♒♓⛎",
    'numbers': "0️⃣1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣8️⃣9️⃣🔟",
    'japanese': "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん",
    'korean': "ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎㅏㅑㅓㅕㅗㅛㅜㅠㅡㅣ",
    'chinese': "的一是不了人我在有他这为之大来以个中上们",
    'arabic': "ابتثجحخدذرزسشصضطظعغفقكلمنهوي",
    'cyrillic': "абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
}

COLORS = ["red", "green", "blue", "yellow"]
DIRECTIONS = ["Up", "Down", "Left", "Right", "Skip"]
DIRECTION_MAP = {
    "Up": "U", "Down": "D", "Left": "L", "Right": "R", "Skip": "S"
}

# System configuration
SYSTEM_WALLET_ADDRESS = os.getenv('APTOS_ACCOUNT') or "0xSYSTEM_WALLET_NOT_SET"
SYSTEM_WALLET_PRIVATE_KEY = os.getenv('APTOS_PRIVATE_KEY')

def generate_nonce() -> str:
    return secrets.token_hex(32)

def keccak256(data: str) -> str:
    return hashlib.sha3_256(data.encode('utf-8')).hexdigest()

def generate_entropy_layers(seed: str, layers: int) -> List[int]:
    arr = []
    cur = seed
    for _ in range(layers):
        random_bytes = secrets.token_bytes(2).hex()
        h = keccak256(cur)
        val = int(h[:8], 16)
        arr.append(val)
        cur = h + random_bytes
    return arr

@dataclass
class SessionState:
    failure_count: int = 0
    first_failure_ts: Optional[float] = None
    last_failure_ts: Optional[float] = None
    d: int = 1
    high_abuse: bool = False

@dataclass
class Transaction:
    """Represents a single transaction in the system"""
    txn_hash: str
    sender: str
    recipient: str
    amount: float  # Amount in APT
    timestamp: float  # Unix timestamp
    is_credit: bool  # True if receiving funds, False if sending
    status: str  # "completed", "pending", "failed"
    description: str = ""  # Optional description

@dataclass
class App:
    queue: Queue = field(default_factory=Queue)
    wallet: Optional[Account] = None
    client: RestClient = field(default_factory=lambda: RestClient("https://testnet.aptoslabs.com/v1"))
    system_wallet: Optional[Account] = None
    is_registered: bool = False
    is_authenticated: bool = False
    selected_secret: Optional[str] = None
    direction_mapping: Dict[str, str] = field(default_factory=dict)
    recent_characters: List[str] = field(default_factory=list)
    favorite_characters: List[str] = field(default_factory=list)
    transactions: List[Transaction] = field(default_factory=list)  # Track all transactions

    async def get_account_balance(self, address):
        """Get account balance in APT"""
        if not self.wallet:
            logging.error("No wallet connected; cannot fetch balance.")
            return 0

        try:
            resources = await self.client.account_resources(address)
            apt_balance = 0
            for resource in resources:
                if resource['type'] == '0x1::coin::CoinStore<0x1::aptos_coin::AptosCoin>':
                    apt_balance = int(resource['data']['coin']['value']) / 100000000  # Convert from octas to APT
                    break
            logging.info("Fetch resources , got resources:", resources)
            logging.info(f"Fetched balance for {address}: {apt_balance} APT")
            return apt_balance
        except Exception as e:
            logging.error(f"Error fetching balance for {address}: {str(e)}")
            raise Exception(f"Failed to check balance: {str(e)}")

    def get_account_balance_sync(self, address):
        """Synchronous wrapper for get_account_balance"""
        try:
            # Use RestClientSync directly instead of relying on async methods
            from utils.aptos_sync import RestClientSync

            # Create a new sync client for each call to avoid event loop issues
            sync_client = RestClientSync("https://testnet.aptoslabs.com/v1")

            # Fetch resources directly with sync client
            resources = sync_client.account_resources(address)
            apt_balance = 0.0

            # Process resources to find APT balance
            for resource in resources:
                if resource['type'] == '0x1::coin::CoinStore<0x1::aptos_coin::AptosCoin>':
                    apt_balance = int(resource['data']['coin']['value']) / 100000000  # Convert from octas to APT
                    break

            logging.info(f"Fetched balance for {address}: {apt_balance} APT")
            return apt_balance
        except Exception as e:
            logging.error(f"Error in get_account_balance_sync: {str(e)}")
            # Return 0 for balance rather than crashing completely
            return 0.0

    def add_transaction(self, txn_hash, sender, recipient, amount, is_credit=None, status="completed", description=""):
        """Add a transaction to the transaction history"""
        if is_credit is None:
            # Determine if this is a credit or debit based on sender/recipient
            if self.wallet:
                is_credit = recipient == str(self.wallet.address())
            else:
                is_credit = False

        # Create new transaction record
        txn = Transaction(
            txn_hash=txn_hash,
            sender=sender,
            recipient=recipient,
            amount=amount,
            timestamp=time.time(),
            is_credit=is_credit,
            status=status,
            description=description
        )

        # Add to transaction list
        self.transactions.append(txn)
        logging.info(f"Added transaction to history: {txn_hash} {'Credit' if is_credit else 'Debit'} {amount} APT")

        return txn

    async def fetch_account_transactions(self, address=None, limit=20):
        """Fetch transaction history for the given address from the blockchain"""
        if not address and self.wallet:
            address = str(self.wallet.address())

        if not address:
            logging.error("No wallet address provided for transaction history")
            return []

        try:
            # Use Aptos SDK to get account transactions
            # We need to handle this differently since AsyncRestClient doesn't have get_account_transactions
            from utils.aptos_sync import RestClientSync

            # Create a sync client with the same URL as our async client
            sync_client = RestClientSync(self.client.base_url)

            # Use the sync client to get transactions
            transactions = sync_client.get_account_transactions(address, limit=limit)

            # Process transactions to identify credits and debits
            processed_txns = []
            for txn in transactions:
                try:
                    # Extract basic transaction data
                    txn_hash = txn.get('hash', '')
                    txn_version = txn.get('version', 0)
                    sender = txn.get('sender', '')
                    timestamp = txn.get('timestamp', 0) / 1000000  # Convert to seconds

                    # Extract payload data to determine transaction type and amount
                    payload = txn.get('payload', {})
                    function = payload.get('function', '')

                    # Only process coin transfers for now
                    if '0x1::coin::transfer' in function:
                        args = payload.get('arguments', [])
                        if len(args) >= 2:
                            recipient = args[0]
                            amount_octas = int(args[1])
                            amount_apt = amount_octas / 100000000  # Convert octas to APT

                            # Determine if credit or debit
                            is_credit = recipient == address

                            # Create transaction object
                            transaction = Transaction(
                                txn_hash=txn_hash,
                                sender=sender,
                                recipient=recipient,
                                amount=amount_apt,
                                timestamp=timestamp,
                                is_credit=is_credit,
                                status="completed",
                                description=f"Transaction {txn_version}"
                            )

                            processed_txns.append(transaction)

                except Exception as e:
                    logging.error(f"Error processing transaction: {str(e)}")
                    continue

            return processed_txns

        except Exception as e:
            logging.error(f"Error fetching transactions for {address}: {str(e)}")
            return []

    def fetch_account_transactions_sync(self, address=None, limit=20):
        """Synchronous wrapper for fetch_account_transactions that avoids asyncio issues"""
        if not address and self.wallet:
            address = str(self.wallet.address())

        if not address:
            logging.error("No wallet address provided for transaction history")
            return []

        try:
            # Use the RestClientSync directly to avoid asyncio issues
            from utils.aptos_sync import RestClientSync
            sync_client = RestClientSync(self.client.base_url)
            transactions = sync_client.get_account_transactions(address, limit=limit)

            # Process transactions to identify credits and debits (copied from async version)
            processed_txns = []
            for txn in transactions:
                try:
                    # Extract basic transaction data
                    txn_hash = txn.get('hash', '')
                    txn_version = txn.get('version', 0)
                    sender = txn.get('sender', '')
                    timestamp = txn.get('timestamp', 0) / 1000000  # Convert to seconds

                    # Extract payload data to determine transaction type and amount
                    payload = txn.get('payload', {})
                    function = payload.get('function', '')

                    # Only process coin transfers for now
                    if '0x1::coin::transfer' in function:
                        args = payload.get('arguments', [])
                        if len(args) >= 2:
                            recipient = args[0]
                            amount_octas = int(args[1])
                            amount_apt = amount_octas / 100000000  # Convert octas to APT

                            # Determine if credit or debit
                            is_credit = recipient == address

                            # Create transaction object
                            transaction = Transaction(
                                txn_hash=txn_hash,
                                sender=sender,
                                recipient=recipient,
                                amount=amount_apt,
                                timestamp=timestamp,
                                is_credit=is_credit,
                                status="completed",
                                description=f"Transaction {txn_version}"
                            )

                            processed_txns.append(transaction)
                except Exception as e:
                    logging.error(f"Error processing transaction: {str(e)}")
                    continue

            return processed_txns
        except Exception as e:
            logging.error(f"Error fetching transactions synchronously: {str(e)}")
            return []

    def update_transaction_history(self):
        """Update the transaction history from the blockchain"""
        if not self.wallet:
            logging.error("No wallet connected; cannot update transaction history")
            return False

        try:
            # Fetch transactions from blockchain
            new_txns = self.fetch_account_transactions_sync(str(self.wallet.address()))

            # Add new transactions that aren't already in our list
            existing_txn_hashes = {txn.txn_hash for txn in self.transactions}

            for txn in new_txns:
                if txn.txn_hash not in existing_txn_hashes:
                    self.transactions.append(txn)

            # Sort by timestamp, most recent first
            self.transactions.sort(key=lambda x: x.timestamp, reverse=True)

            return True
        except Exception as e:
            logging.error(f"Error updating transaction history: {str(e)}")
            return False

    def __post_init__(self):
        # Initialize system wallet
        if SYSTEM_WALLET_PRIVATE_KEY:
            try:
                # Create system wallet from private key hex
                self.system_wallet = Account.load_key(SYSTEM_WALLET_PRIVATE_KEY)
            except Exception as e:
                st.error(f"Failed to initialize system wallet: {str(e)}")
        else:
            # Inform the operator that system wallet isn't configured
            st.warning("System wallet private key not set (APTOS_PRIVATE_KEY). System-send and registration actions will be disabled until configured.")

app = initApp()
# Page configuration
st.set_page_config(
    page_title="1P Wallet - 2FA for Web3",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("🔒 1P Wallet")
st.sidebar.markdown("---")

# Navigation menu
pages = {
    "🏠 Home": "home",
    "💳 Import/Generate Wallet": "wallet_setup",
    "📝 Registration": "registration",
    "🔐 Authentication": "authentication",
    "👤 Account": "account",
}

# Show Transaction History once wallet is connected
if app.wallet:
    pages["📋 Transaction History"] = "transaction_history"

# Only show Manage Wallet if authenticated
if app.is_authenticated:
    pages["💰 Manage Wallet"] = "manage_wallet"

# Page selection
selected_page = st.sidebar.selectbox(
    "Navigate to:",
    options=list(pages.keys()),
    key="page_selector"
)

current_page = pages[selected_page]

# Display current status in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("Status")
if app.wallet:
    st.sidebar.success("✅ Wallet Connected")
    st.sidebar.text(f"Address: {str(app.wallet.address())[:10]}...")
else:
    st.sidebar.error("❌ No Wallet")

if app.is_registered:
    st.sidebar.success("✅ Registered")
else:
    st.sidebar.warning("⚠️ Not Registered")

if app.is_authenticated:
    st.sidebar.success("✅ Authenticated")
else:
    st.sidebar.warning("⚠️ Not Authenticated")

# Main content area
st.title("🔒 1P Wallet - 2FA for Web3")

# Route to appropriate page
if current_page == "home":
    st.markdown("""
    ## Welcome to 1P Wallet

    A secure 2FA system for Web3 wallets using elegant UTF-8 character selection.

    ### How it works:
    1. **Import or Generate** an Aptos wallet
    2. **Register** by selecting a single UTF-8 character as your secret
    3. **Transfer funds** to our secure system wallet
    4. **Authenticate** using the 1P visual grid system
    5. **Manage** your wallet securely through our system

    ### Features:
    - 🎨 Elegant UTF-8 character selection (no keyboard typing!)
    - 🔒 Secure backend wallet system
    - 🌍 Multi-language support
    - 🎯 Visual grid-based authentication
    - 💯 No private key exposure after registration
    """)

    if not app.wallet:
        st.info("👈 Start by setting up your wallet in the sidebar")
    elif not app.is_registered:
        st.info("👈 Next, register your 1P secret")
    elif not app.is_authenticated:
        st.info("👈 Authenticate to access wallet management")

else:
    # Import and execute the page module properly
    import sys
    import importlib.util

    # Define variables that will be available to the page modules
    page_globals = {
        'st': st,
        'app': app,
        'DOMAINS': DOMAINS,
        'COLORS': COLORS,
        'DIRECTIONS': DIRECTIONS,
        'SYSTEM_WALLET_ADDRESS': SYSTEM_WALLET_ADDRESS,
        'DIRECTION_MAP': DIRECTION_MAP,
        'Account': Account,
        'EntryFunction': EntryFunction,
        'Serializer': Serializer,
    }

    # Handle page routing
    if current_page == "wallet_setup":
        spec = importlib.util.spec_from_file_location("wallet_setup", "pages/wallet_setup.py")
        page_module = importlib.util.module_from_spec(spec)
        page_module.__dict__.update(page_globals)
        spec.loader.exec_module(page_module)

    elif current_page == "registration":
        spec = importlib.util.spec_from_file_location("registration", "pages/registration.py")
        page_module = importlib.util.module_from_spec(spec)
        page_module.__dict__.update(page_globals)
        spec.loader.exec_module(page_module)

    elif current_page == "authentication":
        spec = importlib.util.spec_from_file_location("authentication", "pages/authentication.py")
        page_module = importlib.util.module_from_spec(spec)
        page_module.__dict__.update(page_globals)
        spec.loader.exec_module(page_module)

    elif current_page == "manage_wallet":
        if app.is_authenticated:
            spec = importlib.util.spec_from_file_location("manage_wallet", "pages/manage_wallet.py")
            page_module = importlib.util.module_from_spec(spec)
            page_module.__dict__.update(page_globals)
            spec.loader.exec_module(page_module)
        else:
            st.error("Please authenticate first to access wallet management.")
            st.info("👈 Use the Authentication page to verify your 1P secret")

    elif current_page == "account":
        spec = importlib.util.spec_from_file_location("account", "pages/account.py")
        page_module = importlib.util.module_from_spec(spec)
        page_module.__dict__.update(page_globals)
        spec.loader.exec_module(page_module)

    elif current_page == "transaction_history":
        spec = importlib.util.spec_from_file_location("transaction_history", "pages/transaction_history.py")
        page_module = importlib.util.module_from_spec(spec)
        page_module.__dict__.update(page_globals)
        spec.loader.exec_module(page_module)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("Made with ❤️ using Streamlit")