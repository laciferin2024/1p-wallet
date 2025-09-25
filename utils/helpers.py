import secrets
import hashlib
import streamlit as st
import logging
import inspect
import os
from typing import List


def generate_nonce() -> str:
    return secrets.token_hex(32)


def keccak256(data: str) -> str:
    return hashlib.sha3_256(data.encode('utf-8')).hexdigest()


def generate_entropy_layers(seed: str, layers: int) -> List[int]:
    arr = []
    cur = seed
    for _ in range(layers):
        h = keccak256(cur)
        val = int(h[:8], 16)
        arr.append(val)
        cur = h
    return arr


def is_direct_page_access():
    """Check if a page is being accessed directly rather than through the main app.

    Returns:
        bool: True if the page is being accessed directly, False otherwise
    """
    try:
        # If app is properly initialized in session state, we're good
        if 'app' in st.session_state and 'app_initialized' in st.session_state:
            return False

        # Check caller's filename to see if it's being called from app.py
        stack = inspect.stack()
        for frame in stack:
            if os.path.basename(frame.filename) == 'app.py':
                return False

        # If we're here, it's likely direct access
        return True
    except Exception as e:
        logging.error(f"Error in is_direct_page_access: {e}")
        # Default to False to avoid disruption
        return False


def redirect_if_direct_access():
    """Check if page is directly accessed, and show helpful message if so.

    Returns:
        bool: True if the page is being directly accessed and execution should stop,
              False if normal execution should continue
    """
    if is_direct_page_access() and 'app' not in st.session_state:
        st.error("⚠️ This page cannot be accessed directly. Please start from the main app.")
        st.info("👈 Go to the home page to access the app properly.")
        st.stop()
        return True
    return False