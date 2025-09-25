import os
from dataclasses import dataclass
import math
import random
import string
import time
from queue import Queue

import streamlit as st
import streamlit.components.v1 as components
from aptos_sdk.async_client import RestClient
from aptos_sdk.account import Account
from aptos_sdk.transactions import EntryFunction
from aptos_sdk.bcs import Serializer
import hashlib
import secrets
import unicodedata
from typing import List, Dict, Any
from ecdsa import SigningKey, VerifyingKey, SECP256k1
from ecdsa.util import sigencode_der, sigdecode_der
from collections import defaultdict
from itertools import islice

# ANSI colors for grid display (for terminal, but not used in Streamlit)
ANSI_COLORS = {
    'red': '#FF0000',
    'green': '#00FF00',
    'blue': '#0000FF',
    'yellow': '#FFFF00',
    'reset': '#000000'
}

# Domains (en/ar)
# keep ASCII + digits + punctuation, but only a small curated set of major emojis
DOMAINS = {
    'en': string.ascii_letters + string.digits + string.punctuation +
          "😀😂❤️👍🙏😍😭😅🎉🔥💯😎🤔🤦😴🤖👀✨✅🚀",
}

ALPHABET = DOMAINS['en']

COLORS = ["red", "green", "blue", "yellow"]
DIRECTIONS = ["Up", "Down", "Left", "Right", "Skip"]
DIRECTION_MAP = {
    "Up": "U", "Down": "D", "Left": "L", "Right": "R", "Skip": "S",
    "\x1b[A": "U", "\x1b[B": "D", "\x1b[D": "L", "\x1b[C": "R", "": "S"
}

# Difficulty parameters
WINDOW = 3600  # 1 hour
TRIGGER_FAILURES = 3
ALPHA = 2
D_MAX = 10
COOLDOWN = 3600  # 1 hour
DELAY_CAP = 60  # seconds
PUZZLE_BASE_BITS = 20

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

def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))

def uniform(a, b):
    return a + secrets.randbelow(int(b - a + 1))

class SessionState:
    def __init__(self):
        self.failure_count = 0
        self.first_failure_ts = None
        self.last_failure_ts = None
        self.d = 1
        self.high_abuse = False

class OnePVerifier:
    def __init__(self, secret: str, public_key: str):
        self.secret = secret
        self.public_key = public_key
        self.session_state = SessionState()
        self.nonce = None
        self.entropy_layers = []
        self.offsets = []
        self.rotateds = []
        self.color_maps = []
        self.expected_solutions = []
        self.skip_rounds = []

    def update_difficulty(self, is_failure: bool, now: float) -> tuple[int, float, int]:
        s = self.session_state
        if s.last_failure_ts is not None and (now - s.last_failure_ts) >= COOLDOWN:
            s.failure_count = 0
            s.first_failure_ts = None
            s.d = 1
            s.high_abuse = False

        if not is_failure:
            s.failure_count = 0
            s.first_failure_ts = None
            s.last_failure_ts = now
            s.d = 1
            s.high_abuse = False
            return s.d, 0, 0

        if s.failure_count == 0:
            s.first_failure_ts = now
        s.failure_count += 1
        s.last_failure_ts = now

        if (now - s.first_failure_ts) > WINDOW:
            s.failure_count = 1
            s.first_failure_ts = now
            s.high_abuse = False

        if s.failure_count >= TRIGGER_FAILURES and (now - s.first_failure_ts) <= WINDOW:
            s.high_abuse = True

        if s.high_abuse:
            s.d = clamp(ALPHA * s.d, 1, D_MAX)
        else:
            s.d = clamp(s.d + 1, 1, D_MAX)


        delay = clamp(s.d, 1, DELAY_CAP)
        jitter = uniform(-0.1 * delay, 0.1 * delay)
        enforced_delay = max(0, delay + jitter)
        k = PUZZLE_BASE_BITS + (s.d // 2)

        return s.d, enforced_delay, k

    def start_session(self) -> tuple[str, List[str], int]:
        self.nonce = generate_nonce()
        difficulty = self.session_state.d
        total_rounds = difficulty + (difficulty // 2)
        self.entropy_layers = generate_entropy_layers(self.nonce, total_rounds)
        rounds_range = list(range(total_rounds))
        self.skip_rounds = sorted(random.sample(rounds_range, k=total_rounds - difficulty))
        self.offsets = []
        self.rotateds = []
        self.color_maps = []
        self.expected_solutions = []
        grids = []
        for idx in range(total_rounds):
            offset = self.entropy_layers[idx] % len(ALPHABET)
            self.offsets.append(offset)
            rotated = ALPHABET[offset:] + ALPHABET[:offset]
            self.rotateds.append(rotated)
            color_map = {rotated[i]: COLORS[i % 4] for i in range(len(rotated))}
            self.color_maps.append(color_map)
            if idx in self.skip_rounds:
                expected = "S"
            else:
                assigned_color = color_map.get(self.secret, None)
                expected = "S" if assigned_color is None else DIRECTION_MAP[DIRECTIONS[COLORS.index(assigned_color)]]
            self.expected_solutions.append(expected)
            grids.append(self.display_grid(idx))
        return self.nonce, grids, total_rounds

    def display_grid(self, idx: int) -> str:
        chars_by_color = defaultdict(list)
        for ch, color in self.color_maps[idx].items():
            chars_by_color[color].append(ch)
        grid = f"<div>--- 1P Grid for Round {idx + 1} (Offset hidden) ---<br>"
        for color in COLORS:
            chars = chars_by_color[color]
            pairs = [' '.join(islice(chars, i, i + 2)) for i in range(0, len(chars), 2)]
            display = '  '.join(pairs)
            lines = [display[i:i + 36] for i in range(0, len(display), 36)]
            for line in lines:
                grid += f'<span style="color:{ANSI_COLORS[color]}">+++</span>  {line.ljust(36)}  <span style="color:{ANSI_COLORS[color]}">+++</span><br>'
        grid += "</div>"
        return grid

    def verify_solution(self, candidates: List[str], proof: str) -> tuple[bool, int]:
        now = time.time()
        allowed_skips = len(self.skip_rounds)
        input_skips = candidates.count('S')
        if input_skips > allowed_skips:
            st.error("Too many skips.")
            is_correct = False
        else:
            is_correct = True
            for idx, expected in enumerate(self.expected_solutions):
                if expected == "S":
                    if candidates[idx] != "S":
                        is_correct = False
                        break
                else:
                    if candidates[idx] == "S":
                        continue
                    if candidates[idx].upper() != expected:
                        is_correct = False
                        break

        aggregator_str = ''.join(candidates)
        hash_digest = bytes.fromhex(keccak256(aggregator_str))
        vk = VerifyingKey.from_string(bytes.fromhex(self.public_key), curve=SECP256k1)
        sig_valid = vk.verify_digest(bytes.fromhex(proof), hash_digest, sigdecode=sigdecode_der)

        d, delay, k = self.update_difficulty(not is_correct or not sig_valid, now)
        if delay > 0:
            st.warning(f"Sleeping for {delay:.2f} seconds due to failure.")
            time.sleep(delay)
        if d >= D_MAX:
            st.error("Max difficulty reached. Potential 1FA compromise detected.")
        return is_correct and sig_valid, d

class OnePSolver:
    def __init__(self, private_key_hex: str):
        self.private_key = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)
        self.inputs = []
        self.proof = None

    def solve(self, grids: List[str], total_rounds: int) -> tuple[List[str], str]:
        self.inputs = []
        for idx in range(total_rounds):
            st.markdown(grids[idx], unsafe_allow_html=True)
            input_val = st.text_input(f"Round {idx+1}: Enter direction (U/D/L/R/S or empty for skip):", key=f"input_{idx}")
            if input_val == '':
                input_val = 'S'
            else:
                input_val = input_val.upper()
            if input_val not in 'UDLRS':
                st.error("Invalid input. Use U/D/L/R/S or empty.")
                st.stop()
            self.inputs.append(input_val)
        aggregator_str = ''.join(self.inputs)
        hash_digest = bytes.fromhex(keccak256(aggregator_str))
        self.proof = self.private_key.sign_digest(hash_digest, sigencode=sigencode_der).hex()
        return self.inputs, self.proof

@dataclass
class App:
    queue: Queue = Queue()
    verifier: OnePVerifier = None
    solver: OnePSolver = None
    wallet: Account = None
    client: RestClient = None

    def __post_init__(self):
        print("creating new app instance")
        self.client = RestClient("https://testnet.aptoslabs.com/v1")

app = st.session_state.get('app', App())

# Wallet Setup
if app.wallet is None:
    st.subheader("Setup Aptos Wallet")
    if st.button("Generate Wallet"):
        app.wallet = Account.generate()
        st.success("Wallet generated!")
        st.write(f"Address: {app.wallet.address()}")
        st.write(f"Private Key (keep secret!): {app.wallet.private_key.hex()}")
        st.session_state['app'] = app

if app.wallet:
    st.subheader("Set 1P Secret for 2FA")
    secret = st.text_input("Enter single letter secret (emoji/symbol ok):", type="password")
    if st.button("Set Secret"):
        if len(secret) != 1 or secret not in ALPHABET:
            st.error("Invalid: Single character from domain required.")
        else:
            app.verifier = OnePVerifier(secret, str(app.wallet.public_key()))
            app.solver = OnePSolver(app.wallet.private_key.hex().lstrip('0x'))
            st.success("1P Secret set!")
            st.session_state['app'] = app

if app.verifier and app.solver:
    st.subheader("Perform Wallet Action with 1P 2FA")
    action = st.selectbox("Action", ["Sign Message", "Send Transaction"])
    if action == "Sign Message":
        message = st.text_input("Message to sign:")
        if st.button("Sign with 2FA"):
            nonce, grids, total_rounds = app.verifier.start_session()
            st.write(f"Session nonce: {nonce[:16]}...")
            solutions, proof = app.solver.solve(grids, total_rounds)
            is_correct, difficulty = app.verifier.verify_solution(solutions, proof)
            if is_correct:
                signature = app.wallet.sign(message.encode())
                st.success(f"Signature: {signature.hex()}")
            else:
                st.error(f"2FA failed. Difficulty now: {difficulty}")

    elif action == "Send Transaction":
        recipient = st.text_input("Recipient Address:")
        amount = st.number_input("Amount (in APT):", min_value=0.00000001)
        if st.button("Send with 2FA"):
            nonce, grids, total_rounds = app.verifier.start_session()
            st.write(f"Session nonce: {nonce[:16]}...")
            solutions, proof = app.solver.solve(grids, total_rounds)
            is_correct, difficulty = app.verifier.verify_solution(solutions, proof)
            if is_correct:
                payload = EntryFunction.natural(
                    "0x1::coin",
                    "transfer",
                    ["0x1::aptos_coin::AptosCoin"],
                    [recipient, Serializer.u64.serialize(int(amount * 10**8))]
                )
                txn = app.client.create_transaction(app.wallet.address(), payload)
                signed_txn = app.wallet.sign_transaction(txn)
                txn_hash = app.client.submit_transaction(signed_txn)
                st.success(f"Transaction hash: {txn_hash}")
            else:
                st.error(f"2FA failed. Difficulty now: {difficulty}")
