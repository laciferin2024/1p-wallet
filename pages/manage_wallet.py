# Manage Wallet Page
st.header("💰 Manage Wallet")

if not app.is_authenticated:
    st.error("❌ Authentication required")
    st.info("Please authenticate first to access wallet management")
    st.stop()

st.success("🔐 Authenticated Session Active")
st.markdown(f"**Wallet:** `{str(app.wallet.address())[:20]}...`")
st.markdown(f"**System Wallet:** `{SYSTEM_WALLET_ADDRESS[:20]}...`")

# Display current balance from system wallet
st.markdown("---")
st.subheader("💰 Balance Overview")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Your Original Wallet:**")
    if st.button("Check Original Balance", type="secondary"):
        with st.spinner("Checking balance..."):
            try:
                apt_balance = app.get_account_balance_sync(app.wallet.address())
                st.metric("Original Wallet", f"{apt_balance} APT")
            except Exception as e:
                st.error(f"Error: {str(e)}")

with col2:
    st.markdown("**System Wallet (Your Funds):**")
    if st.button("Check System Balance", type="secondary"):
        with st.spinner("Checking system balance..."):
            try:
                apt_balance = app.get_account_balance_sync(SYSTEM_WALLET_ADDRESS)
                st.metric("System Wallet", f"{apt_balance} APT")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Transaction functionality
st.markdown("---")
st.subheader("💸 Send Transaction")
st.info("💡 **How it works:** Transactions are processed through our secure system wallet on your behalf")

if not app.system_wallet:
    st.error("System wallet not configured. Sending transactions is disabled.")
    st.info("Set APTOS_PRIVATE_KEY in environment and restart the app to enable system-send functionality.")
else:
    with st.form("send_transaction"):
        recipient_address = st.text_input(
            "Recipient Address",
            placeholder="0x1234abcd...",
            help="Enter the Aptos address to send funds to"
        )

        amount = st.number_input(
            "Amount (APT)",
            min_value=0.00000001,
            max_value=100.0,
            value=0.1,
            step=0.01,
            format="%.8f"
        )

        st.markdown("**Transaction Preview:**")
        st.markdown(f"""
        - **From:** System Wallet (`{SYSTEM_WALLET_ADDRESS[:20]}...`)
        - **To:** `{recipient_address[:20] + '...' if len(recipient_address) > 20 else recipient_address}`
        - **Amount:** {amount} APT
        - **Fee:** ~0.001 APT (estimated)
        """)

        send_transaction = st.form_submit_button("🚀 Send Transaction", type="primary")

    if send_transaction:
        if not recipient_address:
            st.error("Please enter a recipient address")
        elif len(recipient_address) < 10:
            st.error("Invalid recipient address")
        else:
            with st.spinner("Processing transaction through system wallet..."):
                try:
                    # Create transaction from system wallet
                    amount_in_octas = int(amount * 100000000)

                    payload = EntryFunction.natural(
                        "0x1::coin",
                        "transfer",
                        ["0x1::aptos_coin::AptosCoin"],
                        [recipient_address, Serializer.u64.serialize(amount_in_octas)]
                    )

                    # Create transaction with system wallet
                    txn = app.client.create_transaction(app.system_wallet.address(), payload)
                    signed_txn = app.system_wallet.sign_transaction(txn)
                    txn_hash = app.client.submit_transaction(signed_txn)

                    # Wait for confirmation
                    app.client.wait_for_transaction(txn_hash)

                    st.success("✅ Transaction sent successfully!")
                    st.success(f"📋 Transaction Hash: `{txn_hash}`")

                    # Show transaction details
                    with st.expander("Transaction Details", expanded=True):
                        st.markdown(f"""
                        - **Hash:** `{txn_hash}`
                        - **From:** `{app.system_wallet.address()}`
                        - **To:** `{recipient_address}`
                        - **Amount:** {amount} APT
                        - **Status:** Confirmed ✅
                        """)

                except Exception as e:
                    st.error(f"❌ Transaction failed: {str(e)}")

# Message signing
st.markdown("---")
st.subheader("✍️ Sign Message")
st.info("💡 **Secure signing:** Messages are signed using your authenticated session")

with st.form("sign_message"):
    message_to_sign = st.text_area(
        "Message to Sign",
        placeholder="Enter your message here...",
        height=100
    )

    sign_message = st.form_submit_button("✍️ Sign Message", type="secondary")

    if sign_message:
        if not message_to_sign:
            st.error("Please enter a message to sign")
        else:
            try:
                # Sign with original wallet for authenticity
                signature = app.wallet.sign(message_to_sign.encode())
                signature_hex = signature.hex()

                st.success("✅ Message signed successfully!")

                with st.expander("Signature Details", expanded=True):
                    st.markdown("**Original Message:**")
                    st.code(message_to_sign)
                    st.markdown("**Signature:**")
                    st.code(signature_hex)
                    st.markdown("**Signer Address:**")
                    st.code(str(app.wallet.address()))

            except Exception as e:
                st.error(f"❌ Signing failed: {str(e)}")

# Account management
st.markdown("---")
st.subheader("⚙️ Account Management")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Session Control:**")
    if st.button("🔄 Refresh Authentication", type="secondary"):
        st.info("Session refreshed successfully")
        st.rerun()

    if st.button("🚪 Logout", type="secondary"):
        app.is_authenticated = False
        st.session_state.app = app
        st.success("Logged out successfully")
        st.info("👈 Go to Authentication to login again")
        st.rerun()

with col2:
    st.markdown("**Account Info:**")
    with st.expander("View Account Details"):
        st.markdown(f"""
        **Wallet Address:** `{app.wallet.address()}`

        **System Wallet:** `{SYSTEM_WALLET_ADDRESS}`

        **Selected Secret:** {app.selected_secret} (U+{ord(app.selected_secret):04X})

        **Registration Status:** ✅ Registered

        **Authentication Status:** ✅ Active
        """)

# Recent transactions (placeholder)
st.markdown("---")
st.subheader("📋 Recent Activity")
st.info("Transaction history feature coming soon...")

# Security notice
st.markdown("---")
st.warning("🔒 **Security Notice:** Your private key is securely managed by the 1P system. Never share your secret character or direction mapping with anyone.")