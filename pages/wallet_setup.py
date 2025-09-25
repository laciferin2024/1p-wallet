# Wallet Setup Page
# Note: This file is executed in the context of app.py, so all imports are available

import streamlit as st

st.header("💳 Import/Generate Wallet")

# Attempt automatic restore from browser localStorage if streamlit_javascript is available
has_streamlit_js = False
try:
    from streamlit_javascript import st_javascript
    has_streamlit_js = True
except Exception:
    has_streamlit_js = False

# Try to restore stored wallet from browser localStorage (opt-in)
if has_streamlit_js and not app.wallet:
    try:
        stored = st_javascript("localStorage.getItem('1p_wallet')")
        if stored:
            import json
            try:
                data = json.loads(stored)
                pk = data.get('private_key')
                if pk:
                    clean_pk = pk[2:] if pk.startswith('0x') else pk
                    app.wallet = Account.load_key(clean_pk)
                    st.session_state['cached_wallet'] = {'address': str(app.wallet.address()), 'private_key': app.wallet.private_key.hex()}
                    st.session_state.app = app
                    st.success('✅ Wallet restored from browser localStorage')
                    st.experimental_rerun()
            except Exception:
                # ignore malformed JSON
                pass
    except Exception:
        # If JS bridge fails, ignore and continue
        pass

col1, col2 = st.columns(2)

with col1:
    st.subheader("🎲 Generate New Wallet")
    st.markdown("Create a brand new Aptos SECP256k1 wallet")

    if st.button("Generate New Wallet", type="primary"):
        with st.spinner("Generating wallet..."):
            try:
                app.wallet = Account.generate_secp256k1_ecdsa()
                # Cache in session_state so the wallet persists during this browser session
                st.session_state['cached_wallet'] = {
                    'address': str(app.wallet.address()),
                    'private_key': app.wallet.private_key.hex()
                }
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
                # Cache imported wallet in session_state for this session
                st.session_state['cached_wallet'] = {
                    'address': str(app.wallet.address()),
                    'private_key': app.wallet.private_key.hex()
                }
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
            with st.spinner("🔄 Requesting tokens from faucet..."):
                try:
                    # Try to request tokens directly from Aptos testnet faucet
                    import requests
                    import json

                    # Default faucet URL for Aptos testnet
                    faucet_url = "https://faucet.testnet.aptoslabs.com/v1/fund"

                    # Prepare the request payload
                    payload = {
                        "address": str(app.wallet.address()),
                        "amount": 100000000,  # 1 APT in octas
                    }

                    # Make the request to the faucet
                    response = requests.post(
                        faucet_url,
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )

                    if response.status_code == 200:
                        result = response.json()
                        txn_hash = result.get('txn_hash', 'Unknown')
                        st.success(f"✅ Successfully requested tokens!")
                        st.info(f"Transaction hash: `{txn_hash}`")

                        # Record the faucet transaction in our history
                        app.add_transaction(
                            txn_hash=txn_hash,
                            sender="Aptos Faucet",
                            recipient=str(app.wallet.address()),
                            amount=1.0,  # Faucet typically sends 1 APT
                            is_credit=True,
                            status="completed",
                            description="Testnet Faucet Claim"
                        )
                        st.session_state.app = app
                        st.markdown("📋 You can view this transaction in your **Transaction History** page")

                        # Add refresh button to check balance
                        if st.button("Check Updated Balance"):
                            st.rerun()
                    else:
                        st.error(f"Failed to request tokens: {response.text}")
                        st.info("Try using the manual faucet option below")

                        # Provide manual instructions as fallback
                        st.markdown("""
                        **Manual Faucet Options:**
                        1. Visit [Aptos Testnet Faucet](https://www.aptosfaucet.com/)
                        2. Paste your address: `{}`
                        3. Click "Submit" to receive test APT
                        """.format(app.wallet.address()))

                except Exception as e:
                    st.error(f"Error requesting tokens: {str(e)}")
                    # Provide manual instructions as fallback
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
                # Get APT balance using the sync helper method
                apt_balance = app.get_account_balance_sync(app.wallet.address())

                st.success(f"💰 Balance: **{apt_balance} APT**")

                if apt_balance >= 1.0:
                    st.success("✅ Sufficient balance for registration (≥1 APT required)")
                else:
                    st.warning("⚠️ Insufficient balance for registration. Please use the faucet to get at least 1 APT.")

            except Exception as e:
                st.error(f"❌ Failed to check balance: {str(e)}")
                st.info("This might happen if the account hasn't been funded yet. Try using the faucet first.")

# Next steps
if app.wallet:
    st.markdown("---")
    st.success("🎉 Wallet is ready!")
    st.info("**Next Steps:** Navigate to the Registration page to set up your 1P secret and transfer funds to the secure system.")

    # Backup and persistence options
    st.markdown("---")
    st.subheader("🔐 Backup & Persistence")
    st.markdown("It's recommended you back up your private key securely. Storing private keys in browser localStorage is insecure — only do this if you understand the risk.")

    cached = st.session_state.get('cached_wallet')
    if cached:
        # Prepare JSON for download
        import json

        backup_json = json.dumps(cached)

        st.download_button(
            label="Download Backup (wallet.json)",
            data=backup_json,
            file_name="wallet_backup.json",
            mime="application/json",
        )

        # Save to browser localStorage via JS bridge if available
        if has_streamlit_js:
            try:
                if st.button("💾 Save to browser localStorage (one-click)"):
                    # Use the JS bridge to set the item
                    st_javascript(f"localStorage.setItem('1p_wallet', JSON.stringify({backup_json})); 'saved';")
                    st.success("Saved to localStorage")
            except Exception:
                st.warning("Unable to access browser localStorage via streamlit_javascript.")
                st.markdown("**Persist in browser localStorage (manual)**")
                st.markdown("Copy the JavaScript snippet below and paste it into your browser console on this site to store the wallet in localStorage.")
                js_snippet = f"localStorage.setItem('1p_wallet', JSON.stringify({backup_json})); console.log('1p_wallet saved to localStorage');"
                st.code(js_snippet)
        else:
            st.markdown("**Persist in browser localStorage (manual)**")
            st.markdown("Copy the JavaScript snippet below and paste it into your browser console on this site to store the wallet in localStorage.")
            js_snippet = f"localStorage.setItem('1p_wallet', JSON.stringify({backup_json})); console.log('1p_wallet saved to localStorage');"
            st.code(js_snippet)

        st.markdown("**Restore from a backup file**")
        uploaded = st.file_uploader("Upload wallet_backup.json to restore", type=["json"])
        if uploaded:
            try:
                data = json.load(uploaded)
                pk = data.get('private_key')
                if pk:
                    # Load wallet and update app state
                    clean_pk = pk
                    if clean_pk.startswith('0x'):
                        clean_pk = clean_pk[2:]
                    app.wallet = Account.load_key(clean_pk)
                    st.session_state.app = app
                    st.success("✅ Wallet restored from backup and loaded into session")
                    st.experimental_rerun()
                else:
                    st.error("Uploaded file doesn't contain a private_key field")
            except Exception as e:
                st.error(f"Failed to restore backup: {str(e)}")