# Wallet Setup Page
# Note: This file is executed in the context of app.py, so all imports are available

st.header("💳 Import/Generate Wallet")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🎲 Generate New Wallet")
    st.markdown("Create a brand new Aptos SECP256k1 wallet")

    if st.button("Generate New Wallet", type="primary"):
        with st.spinner("Generating wallet..."):
            try:
                app.wallet = Account.generate_secp256k1_ecdsa()
                st.session_state.app = app
                st.success("✅ Wallet generated successfully!")
                st.info("**⚠️ Important:** Save your private key securely before proceeding!")

                with st.expander("Wallet Details", expanded=True):
                    st.text(f"Address: {app.wallet.address()}")
                    st.text(f"Private Key: {app.wallet.private_key.hex()}")
                    st.warning("🔐 Keep your private key secure and never share it!")

            except Exception as e:
                st.error(f"Failed to generate wallet: {str(e)}")

with col2:
    st.subheader("📥 Import Existing Wallet")
    st.markdown("Import your existing Aptos wallet using private key")

    private_key_input = st.text_input(
        "Private Key (hex format)",
        type="password",
        placeholder="0x1234abcd...",
        help="Enter your Aptos wallet private key in hex format"
    )

    if st.button("Import Wallet", type="secondary"):
        if private_key_input:
            try:
                # Clean the private key input
                clean_private_key = private_key_input.strip()
                if clean_private_key.startswith('0x'):
                    clean_private_key = clean_private_key[2:]

                # Create account from private key hex
                app.wallet = Account.load_key(clean_private_key)
                st.session_state.app = app

                st.success("✅ Wallet imported successfully!")
                st.info(f"**Address:** {app.wallet.address()}")

            except ValueError as e:
                st.error("❌ Invalid private key format. Please check your input.")
            except Exception as e:
                st.error(f"❌ Failed to import wallet: {str(e)}")
        else:
            st.warning("Please enter a private key to import")

# Faucet section (only show if wallet is connected)
if app.wallet:
    st.markdown("---")
    st.subheader("🚰 Testnet Faucet")
    st.markdown("Get free APT tokens for testing on Aptos testnet")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.info(f"**Your Address:** `{app.wallet.address()}`")

    with col2:
        if st.button("Request Testnet APT", type="secondary"):
            st.info("🔄 Requesting tokens from faucet...")
            st.markdown("""
            **Manual Faucet Options:**
            1. Visit [Aptos Testnet Faucet](https://www.aptosfaucet.com/)
            2. Paste your address: `{}`
            3. Click "Submit" to receive test APT
            """.format(app.wallet.address()))

# Balance checker
if app.wallet:
    st.markdown("---")
    st.subheader("💰 Account Balance")

    if st.button("Check Balance", type="secondary"):
        with st.spinner("Checking balance..."):
            try:
                # Get account balance
                account_data = app.client.account(app.wallet.address())
                balance = account_data.get('authentication_key', 'Unknown')

                # Try to get APT balance
                try:
                    resources = app.client.account_resources(app.wallet.address())
                    apt_balance = 0
                    for resource in resources:
                        if resource['type'] == '0x1::coin::CoinStore<0x1::aptos_coin::AptosCoin>':
                            apt_balance = int(resource['data']['coin']['value']) / 100000000  # Convert from octas to APT
                            break

                    st.success(f"💰 Balance: **{apt_balance} APT**")

                    if apt_balance >= 1.0:
                        st.success("✅ Sufficient balance for registration (≥1 APT required)")
                    else:
                        st.warning("⚠️ Insufficient balance for registration. Please use the faucet to get at least 1 APT.")

                except Exception as e:
                    st.warning("⚠️ Could not fetch APT balance. Please ensure your wallet has been funded.")

            except Exception as e:
                st.error(f"❌ Failed to check balance: {str(e)}")
                st.info("This might happen if the account hasn't been funded yet. Try using the faucet first.")

# Next steps
if app.wallet:
    st.markdown("---")
    st.success("🎉 Wallet is ready!")
    st.info("**Next Steps:** Navigate to the Registration page to set up your 1P secret and transfer funds to the secure system.")