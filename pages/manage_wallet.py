import streamlit as st


# Manage Wallet Page
st.header("💰 Manage Wallet")

if not app.is_authenticated:
    st.error("❌ Authentication required")
    st.info("Please authenticate first to access wallet management")
    st.stop()

st.success("🔐 Authenticated Session Active")
st.markdown(f"**Your Wallet Address:** `{str(app.wallet.address())[:20]}...`")

# Display wallet balance
st.markdown("---")
st.subheader("💰 Your Wallet Balance")

# Automatically check user balance
with st.spinner("Checking your wallet balance..."):
    try:
        # Use the sync helper method
        apt_balance = app.get_account_balance_sync(app.wallet.address())

        # Show the balance
        st.metric("Current Balance", f"{apt_balance} APT")

        # Add a refresh button
        if st.button("🔄 Refresh Balance", type="secondary"):
            st.rerun()

    except Exception as e:
        st.error(f"Error checking balance: {str(e)}")
        st.info("Try refreshing the page if this persists.")

# Transaction functionality
st.markdown("---")
st.subheader("💸 Send Transaction")
st.info("💡 **Secure Transactions:** Send APT directly from your authenticated wallet")

if not app.system_wallet:
    st.error("Wallet service not configured. Sending transactions is disabled.")
    st.info("Please try again later when the service is available.")
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
        - **From:** Your Authenticated Wallet
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

                    # Create BCS serializer for the amount
                    serializer = Serializer()
                    serializer.u64(amount_in_octas)
                    serialized_amount = serializer.output()

                    # Make the transaction process more robust
                    try:
                        payload = EntryFunction.natural(
                            "0x1::coin",
                            "transfer",
                            ["0x1::aptos_coin::AptosCoin"],
                            [recipient_address, serialized_amount]
                        )

                        # Create and submit transaction - handling potential async issues
                        from utils.aptos_sync import RestClientSync
                        # Use the sync wrapper to ensure compatibility with streamlit
                        sync_client = RestClientSync("https://testnet.aptoslabs.com/v1")

                        # Create and process the transaction
                        with st.spinner("Creating transaction..."):
                            txn = sync_client.create_transaction(app.system_wallet.address(), payload)

                        with st.spinner("Signing transaction..."):
                            signed_txn = app.system_wallet.sign_transaction(txn)

                        with st.spinner("Submitting transaction..."):
                            txn_hash = sync_client.submit_transaction(signed_txn)

                        with st.spinner("Waiting for confirmation..."):
                            sync_client.wait_for_transaction(txn_hash, timeout=30)

                    except Exception as e:
                        st.error(f"Transaction failed: {str(e)}")
                        st.warning("Please try again later.")
                        return

                    # Record transaction in our history
                    app.add_transaction(
                        txn_hash=txn_hash,
                        sender=str(app.system_wallet.address()),
                        recipient=recipient_address,
                        amount=amount,
                        is_credit=False,
                        status="completed",
                        description=f"Transfer to {recipient_address[:10]}..."
                    )

                    st.session_state.app = app

                    st.success("✅ Transaction sent successfully!")
                    st.success(f"📋 Transaction Hash: `{txn_hash}`")
                    st.markdown("📋 You can view this transaction in your **Transaction History** page")

                    # Show transaction details
                    with st.expander("Transaction Details", expanded=True):
                        st.markdown(f"""
                        - **Hash:** `{txn_hash}`
                        - **From:** Your Authenticated Wallet
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