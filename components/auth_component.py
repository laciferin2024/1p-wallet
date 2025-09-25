import streamlit as st
from typing import Dict, List, Callable, Optional

from utils.auth_utils import run_one_round_authentication

def one_round_auth(
    secret: str,
    direction_mapping: Dict[str, str],
    colors: List[str],
    direction_map: Dict[str, str],
    domains: Dict[str, Dict],
    session_key: str = "one_round_auth",
    on_success: Optional[Callable] = None,
    on_failure: Optional[Callable] = None,
    show_reference: bool = True
) -> bool:
    """
    Streamlit component for one-round 1P authentication.

    Args:
        secret: The user's secret character
        direction_mapping: Mapping of colors to directions
        colors: List of available colors
        direction_map: Mapping of direction names to codes
        domains: Available character domains
        session_key: Unique key for session state
        on_success: Optional callback function when auth succeeds
        on_failure: Optional callback function when auth fails
        show_reference: Whether to show direction mapping reference

    Returns:
        True if authentication is completed successfully, False otherwise
    """
    # Initialize session state for this component
    if session_key not in st.session_state:
        st.session_state[session_key] = {
            'started': False,
            'completed': False,
            'success': False,
            'grid_html': None,
            'expected': None
        }

    sess = st.session_state[session_key]

    # If not started yet, show start button
    if not sess['started']:
        st.info("Click 'Authenticate' to verify your identity")
        if st.button("🔐 Authenticate", type="primary", key=f"{session_key}_start_btn"):
            # Generate challenge
            grid_html, expected = run_one_round_authentication(
                secret, direction_mapping, colors, direction_map, domains
            )

            # Update session state
            sess['started'] = True
            sess['grid_html'] = grid_html
            sess['expected'] = expected
            st.rerun()
        return False

    # If already completed, return result
    if sess['completed']:
        return sess['success']

    # Display the challenge grid
    st.markdown(sess['grid_html'], unsafe_allow_html=True)

    # Show direction mapping as reference if requested
    if show_reference:
        with st.expander("🧭 Your Direction Mapping Reference"):
            col1, col2 = st.columns(2)
            with col1:
                for color in colors[:len(colors)//2]:
                    direction = direction_mapping.get(color, "Skip")
                    emoji_map = {"Up": "⬆️", "Down": "⬇️", "Left": "⬅️", "Right": "➡️", "Skip": "⏭️"}
                    st.markdown(f"**{color.title()}**: {direction} {emoji_map[direction]}")
            with col2:
                for color in colors[len(colors)//2:]:
                    direction = direction_mapping.get(color, "Skip")
                    emoji_map = {"Up": "⬆️", "Down": "⬇️", "Left": "⬅️", "Right": "➡️", "Skip": "⏭️"}
                    st.markdown(f"**{color.title()}**: {direction} {emoji_map[direction]}")

    # Input for the direction
    col1, col2 = st.columns([3, 1])
    with col1:
        user_input = st.radio(
            "What direction do you see?",
            options=["⬆️ Up", "⬇️ Down", "⬅️ Left", "➡️ Right", "⏭️ Skip"],
            key=f"{session_key}_input",
            horizontal=True
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        if st.button("Submit", type="primary", key=f"{session_key}_submit_btn"):
            # Map emoji selection to direction code
            direction_code = {
                "⬆️ Up": "U",
                "⬇️ Down": "D",
                "⬅️ Left": "L",
                "➡️ Right": "R",
                "⏭️ Skip": "S"
            }[user_input]

            # Check if the answer is correct
            success = direction_code == sess['expected']

            # Update session state
            sess['completed'] = True
            sess['success'] = success

            # Call callbacks if provided
            if success and on_success is not None:
                on_success()
            elif not success and on_failure is not None:
                on_failure()

            st.rerun()

    return False