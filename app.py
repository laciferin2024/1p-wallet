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

# Initialize app in session state
if 'app' not in st.session_state:
    st.session_state.app = App()

app = st.session_state.app

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

elif current_page == "wallet_setup":
    # This will be implemented as a separate page
    exec(open('pages/wallet_setup.py').read())

elif current_page == "registration":
    # This will be implemented as a separate page
    exec(open('pages/registration.py').read())

elif current_page == "authentication":
    # This will be implemented as a separate page
    exec(open('pages/authentication.py').read())

elif current_page == "manage_wallet":
    if app.is_authenticated:
        # This will be implemented as a separate page
        exec(open('pages/manage_wallet.py').read())
    else:
        st.error("Please authenticate first to access wallet management.")
        st.info("👈 Use the Authentication page to verify your 1P secret")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("Made with ❤️ using Streamlit")