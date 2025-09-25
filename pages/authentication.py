import streamlit as st
import logging
from collections import defaultdict
import random

# Import helper functions
from utils.helpers import redirect_if_direct_access

# Check if accessed directly and redirect if needed
if redirect_if_direct_access():
    st.stop()

# Authentication Page
st.header("🔐 Authentication")

# Import necessary modules
from pages import app

# Get access to necessary variables
try:
    # Try to get from the main app
    from app import SessionState, generate_nonce, generate_entropy_layers, DOMAINS, COLORS, DIRECTIONS, DIRECTION_MAP
except ImportError:
    # Fallback to session state if direct page access
    logging.info("Direct page access detected, using session state for app variables")
    if 'SessionState' not in globals():
        @st.cache_data
        def get_session_state_class():
            from app import SessionState
            return SessionState
        try:
            SessionState = get_session_state_class()
        except Exception as e:
            logging.error(f"Failed to import SessionState: {e}")
            st.error("⚠️ Application not properly initialized")
            st.info("Please start from the main page")
            st.stop()

    # Use values from session state if available
    if 'DOMAINS' in st.session_state:
        DOMAINS = st.session_state.DOMAINS
        COLORS = st.session_state.COLORS
        DIRECTIONS = st.session_state.DIRECTIONS
        DIRECTION_MAP = st.session_state.DIRECTION_MAP
        generate_nonce = st.session_state.get('generate_nonce')
        generate_entropy_layers = st.session_state.get('generate_entropy_layers')
    else:
        # Provide defaults if not available
        logging.warning("Missing app constants, using defaults")
        DOMAINS = {}
        COLORS = ["red", "green", "blue", "yellow"]
        DIRECTIONS = ["Up", "Down", "Left", "Right", "Skip"]
        DIRECTION_MAP = {"Up": "U", "Down": "D", "Left": "L", "Right": "R", "Skip": "S"}

        # Define fallback functions
        import secrets, hashlib
        def generate_nonce():
            return secrets.token_hex(32)

        def generate_entropy_layers(seed, layers):
            arr = []
            cur = seed
            for _ in range(layers):
                random_bytes = secrets.token_bytes(2).hex()
                h = hashlib.sha3_256(cur.encode('utf-8')).hexdigest()
                val = int(h[:8], 16)
                arr.append(val)
                cur = h + random_bytes
            return arr

if not app.wallet:
    st.error("❌ Please connect a wallet first")
    st.info("👈 Go to 'Import/Generate Wallet' to get started")
    st.stop()

if not app.is_registered:
    st.error("❌ Please register first")
    st.info("👈 Go to 'Registration' to set up your 1P secret")
    st.stop()

if app.is_authenticated:
    st.success("✅ You are already authenticated!")
    st.info("👈 Go to 'Manage Wallet' to access wallet functions")

    if st.button("🔄 Re-authenticate", type="secondary"):
        app.is_authenticated = False
        app.save_to_session()
        st.rerun()
    st.stop()

st.markdown("""
### 1P Authentication Process:
1. **Visual Grid Challenge** - Find your secret character in the colored grid
2. **Direction Input** - Enter the direction based on your character's color
3. **Multiple Rounds** - Complete several rounds for security
4. **Verification** - System verifies your responses
""")

# Initialize 1P verifier and solver components
class OnePVerifier:
    def __init__(self, secret: str, public_key_hex: str):
        self.secret = secret
        self.public_key = public_key_hex
        self.session_state = SessionState()
        self.nonce = None
        self.entropy_layers = []
        self.offsets = []
        self.rotateds = []
        self.color_maps = []
        self.expected_solutions = []
        self.skip_rounds = []

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

        # Build combined alphabet from all selected domains
        alphabet = ""
        for domain_chars in DOMAINS.values():
            alphabet += domain_chars
        alphabet = ''.join(set(alphabet))  # Remove duplicates

        for idx in range(total_rounds):
            offset = self.entropy_layers[idx] % len(alphabet)
            self.offsets.append(offset)
            rotated = alphabet[offset:] + alphabet[:offset]
            self.rotateds.append(rotated)
            color_map = {rotated[i]: COLORS[i % 4] for i in range(len(rotated))}
            self.color_maps.append(color_map)

            if idx in self.skip_rounds:
                expected = "S"
            else:
                assigned_color = color_map.get(self.secret, None)
                if assigned_color is None:
                    expected = "S"
                else:
                    direction = app.direction_mapping.get(assigned_color, "Skip")
                    expected = DIRECTION_MAP[direction]

            self.expected_solutions.append(expected)
            grids.append(self.display_grid(idx))

        return self.nonce, grids, total_rounds

    def display_grid(self, idx: int) -> str:
        chars_by_color = defaultdict(list)
        for ch, color in self.color_maps[idx].items():
            chars_by_color[color].append(ch)

        grid_html = f"""
        <div style="border: 2px solid #333; padding: 15px; margin: 10px; background: #f8f9fa; border-radius: 8px;">
        <h4>🎯 Round {idx + 1}</h4>
        <p><strong>Find your secret character and note its color!</strong></p>
        """

        color_hex_map = {"red": "#FF0000", "green": "#00AA00", "blue": "#0066FF", "yellow": "#FFD700"}

        for color in COLORS:
            chars = chars_by_color[color]
            if chars:
                grid_html += f'<div style="margin: 8px 0;"><strong style="color: {color_hex_map[color]};">{color.upper()}:</strong> '
                for char in chars:
                    grid_html += f'<span style="color: {color_hex_map[color]}; font-size: 18px; margin: 2px; padding: 4px; background: white; border-radius: 4px;">{char}</span> '
                grid_html += '</div>'

        grid_html += '</div>'
        return grid_html

    def verify_solution(self, candidates: List[str]) -> bool:
        allowed_skips = len(self.skip_rounds)
        input_skips = candidates.count('S')

        if input_skips > allowed_skips:
            return False

        for idx, expected in enumerate(self.expected_solutions):
            if expected == "S":
                if candidates[idx] != "S":
                    return False
            else:
                if candidates[idx] == "S":
                    continue
                if candidates[idx].upper() != expected:
                    return False

        return True

# Start authentication session
st.markdown("---")
st.subheader("🎯 1P Challenge")

if app.auth_session is None:
    st.info("Click 'Start Authentication' to begin the challenge")

    if st.button("🚀 Start Authentication", type="primary"):
        try:
            # Create verifier with user's secret and public key
            public_key_hex = app.wallet.public_key().to_bytes()[1:].hex()
            verifier = OnePVerifier(app.selected_secret, public_key_hex)
            nonce, grids, total_rounds = verifier.start_session()

            app.auth_session = {
                'verifier': verifier,
                'grids': grids,
                'total_rounds': total_rounds,
                'current_round': 0,
                'solutions': [],
                'nonce': nonce
            }
            app.save_to_session()
            st.rerun()
        except Exception as e:
            st.error(f"Failed to start authentication: {str(e)}")

else:
    session = app.auth_session
    current_round = session['current_round']
    total_rounds = session['total_rounds']

    if current_round < total_rounds:
        st.progress((current_round) / total_rounds, f"Round {current_round + 1} of {total_rounds}")

        # Display current grid
        st.markdown(session['grids'][current_round], unsafe_allow_html=True)

        # Show direction mapping as reference
        with st.expander("🧭 Your Direction Mapping Reference"):
            col1, col2 = st.columns(2)
            with col1:
                for color in COLORS[:2]:
                    direction = app.direction_mapping.get(color, "Skip")
                    emoji_map = {"Up": "⬆️", "Down": "⬇️", "Left": "⬅️", "Right": "➡️", "Skip": "⏭️"}
                    st.markdown(f"**{color.title()}**: {direction} {emoji_map[direction]}")
            with col2:
                for color in COLORS[2:]:
                    direction = app.direction_mapping.get(color, "Skip")
                    emoji_map = {"Up": "⬆️", "Down": "⬇️", "Left": "⬅️", "Right": "➡️", "Skip": "⏭️"}
                    st.markdown(f"**{color.title()}**: {direction} {emoji_map[direction]}")

        # Input for current round
        col1, col2 = st.columns([3, 1])
        with col1:
            user_input = st.radio(
                f"What direction for Round {current_round + 1}?",
                options=["⬆️ Up", "⬇️ Down", "⬅️ Left", "➡️ Right", "⏭️ Skip"],
                key=f"round_{current_round}",
                horizontal=True
            )

        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
            if st.button("Next Round ▶️", type="primary"):
                # Map emoji selection to direction code
                direction_code = {
                    "⬆️ Up": "U",
                    "⬇️ Down": "D",
                    "⬅️ Left": "L",
                    "➡️ Right": "R",
                    "⏭️ Skip": "S"
                }[user_input]

                session['solutions'].append(direction_code)
                session['current_round'] += 1
                app.auth_session = session
                app.save_to_session()
                st.rerun()

    else:
        # Authentication complete - verify solutions
        st.success("🎉 All rounds completed!")
        st.info("Verifying your responses...")

        verifier = session['verifier']
        solutions = session['solutions']

        if verifier.verify_solution(solutions):
            app.is_authenticated = True
            app.auth_session = None  # Clear session
            app.save_to_session()

            st.success("✅ Authentication successful!")
            st.success("🎉 Welcome to your secure 1P wallet!")
            st.balloons()

            st.info("👈 Go to 'Manage Wallet' to access your wallet functions")
            st.rerun()

        else:
            st.error("❌ Authentication failed!")
            st.error("Your responses don't match the expected pattern.")
            st.warning("Please try again or check your secret character and direction mapping.")

            if st.button("🔄 Try Again", type="secondary"):
                app.auth_session = None
                app.save_to_session()
                st.rerun()