# Account Page - basic account details and reset
import streamlit as st
import logging

# Import helper functions
from utils.helpers import redirect_if_direct_access

# Check if accessed directly and redirect if needed
if redirect_if_direct_access():
    st.stop()

st.header("👤 Account")

from pages import app

if not app.wallet:
    st.error("❌ No wallet connected")
    st.info("Go to 'Import/Generate Wallet' to connect a wallet")
    st.stop()

st.markdown("**Wallet Address:**")
st.code(str(app.wallet.address()))

st.markdown("**Selected Secret:**")
if app.selected_secret:
    st.code(f"{app.selected_secret} (U+{ord(app.selected_secret):04X})")
else:
    st.info("No secret selected yet")

st.markdown("---")
if st.button("🔄 Reset App State", type="secondary"):
    # Minimal reset: clear registration/authentication and selected secret
    app.is_registered = False
    app.is_authenticated = False
    app.selected_secret = None
    app.direction_mapping = {}
    st.session_state.app = app
    st.success("App state reset. Please re-register or re-import wallet.")
    st.rerun()
