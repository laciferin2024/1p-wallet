# Registration Page
st.header("📝 Registration")

if not app.wallet:
    st.error("❌ Please connect a wallet first")
    st.info("👈 Go to 'Import/Generate Wallet' to get started")
    st.stop()

if app.is_registered:
    st.success("✅ You are already registered!")
    st.info("👈 Go to 'Authentication' to verify your 1P secret")
    st.stop()

st.markdown("""
### Registration Process:
1. **Select your 1P secret** - Choose one UTF-8 character elegantly
2. **Configure direction mapping** - Set your color-to-direction preferences
3. **Transfer minimum 1 APT** - Funds will be held in our secure system wallet
4. **Complete registration** - Your wallet will be registered for 1P authentication
""")

# Step 1: UTF-8 Character Selection
st.markdown("---")
st.subheader("🎨 Step 1: Select Your 1P Secret")
st.markdown("Choose **one character** that will be your secret. No keyboard typing required!")

# Language/Category filters
col1, col2, col3 = st.columns(3)
with col1:
    selected_categories = st.multiselect(
        "Character Categories",
        options=list(DOMAINS.keys()),
        default=['emojis'],
        help="Select which types of characters to show"
    )

with col2:
    chars_per_row = st.slider("Characters per row", 5, 20, 10)

with col3:
    show_unicode = st.checkbox("Show Unicode codes", False)

# Build character set based on selection
available_chars = ""
for category in selected_categories:
    available_chars += DOMAINS[category]

if not available_chars:
    st.warning("Please select at least one character category")
    st.stop()

# Display character selection grid
st.markdown("**Available Characters:**")
chars_list = list(set(available_chars))  # Remove duplicates
chars_list.sort()

# Create grid display
rows = [chars_list[i:i + chars_per_row] for i in range(0, len(chars_list), chars_per_row)]

selected_secret = None
for row_idx, row in enumerate(rows):
    cols = st.columns(len(row))
    for col_idx, char in enumerate(row):
        with cols[col_idx]:
            unicode_info = f"\\nU+{ord(char):04X}" if show_unicode else ""
            if st.button(f"{char}{unicode_info}", key=f"char_{row_idx}_{col_idx}"):
                selected_secret = char
                app.selected_secret = char
                st.session_state.app = app
                st.rerun()

# Show selected secret
if app.selected_secret:
    st.success(f"✅ Selected secret: **{app.selected_secret}** (U+{ord(app.selected_secret):04X})")

# Step 2: Direction Mapping Configuration
if app.selected_secret:
    st.markdown("---")
    st.subheader("🧭 Step 2: Configure Direction Mapping")
    st.markdown("Set your preferred directions for each color. This will be used during authentication.")

    col1, col2 = st.columns(2)

    direction_mapping = {}
    with col1:
        st.markdown("**Color → Direction Mapping:**")
        for color in COLORS:
            direction_mapping[color] = st.selectbox(
                f"{color.title()} →",
                options=DIRECTIONS,
                key=f"direction_{color}",
                index=DIRECTIONS.index(DIRECTIONS[COLORS.index(color)])  # Default mapping
            )

    with col2:
        st.markdown("**Preview:**")
        for color, direction in direction_mapping.items():
            emoji_map = {"Up": "⬆️", "Down": "⬇️", "Left": "⬅️", "Right": "➡️", "Skip": "⏭️"}
            st.text(f"{color.title()}: {direction} {emoji_map[direction]}")

    app.direction_mapping = direction_mapping
    st.session_state.app = app

# Step 3: Balance Transfer
if app.selected_secret and app.direction_mapping:
    st.markdown("---")
    st.subheader("💰 Step 3: Transfer Funds to System")

    st.info(f"**System Wallet Address:** `{SYSTEM_WALLET_ADDRESS}`")
    st.markdown("**Why transfer funds?**")
    st.markdown("""
    - Your funds are held securely in our system wallet
    - Transactions are processed through our secure backend
    - Your private key is never exposed after registration
    - Minimum 1 APT required for registration
    """)

    # Check current balance
    if st.button("Check Current Balance"):
        with st.spinner("Checking balance..."):
            try:
                resources = app.client.account_resources(app.wallet.address())
                apt_balance = 0
                for resource in resources:
                    if resource['type'] == '0x1::coin::CoinStore<0x1::aptos_coin::AptosCoin>':
                        apt_balance = int(resource['data']['coin']['value']) / 100000000
                        break

                st.info(f"Current balance: **{apt_balance} APT**")

                if apt_balance >= 1.0:
                    st.success("✅ Sufficient balance for registration")
                else:
                    st.error("❌ Insufficient balance. Need at least 1 APT.")
                    st.stop()

            except Exception as e:
                st.error(f"Failed to check balance: {str(e)}")
                st.stop()

    # Transfer amount selection
    col1, col2 = st.columns(2)
    with col1:
        transfer_amount = st.number_input(
            "Transfer Amount (APT)",
            min_value=1.0,
            max_value=100.0,
            value=1.0,
            step=0.1,
            help="Minimum 1 APT required"
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        leave_for_gas = st.checkbox("Leave 0.1 APT for gas fees", value=True)

    # Step 4: Complete Registration
    st.markdown("---")
    st.subheader("✅ Step 4: Complete Registration")

    st.warning("⚠️ **Final Check:**")
    st.markdown(f"""
    - **Secret Character:** {app.selected_secret}
    - **Direction Mapping:** {len(app.direction_mapping)} colors configured
    - **Transfer Amount:** {transfer_amount} APT
    - **System Wallet:** `{SYSTEM_WALLET_ADDRESS[:20]}...`
    """)

    st.error("🔒 **Important:** After registration, your wallet's private key will be securely handled by our system. Make sure you're ready to proceed.")

    confirm_registration = st.checkbox("I understand and want to proceed with registration")

    if confirm_registration and st.button("🚀 Complete Registration", type="primary"):
        with st.spinner("Processing registration..."):
            try:
                # Create transfer transaction
                amount_in_octas = int(transfer_amount * 100000000)  # Convert APT to octas

                payload = EntryFunction.natural(
                    "0x1::coin",
                    "transfer",
                    ["0x1::aptos_coin::AptosCoin"],
                    [SYSTEM_WALLET_ADDRESS, Serializer.u64.serialize(amount_in_octas)]
                )

                # Create and submit transaction
                txn = app.client.create_transaction(app.wallet.address(), payload)
                signed_txn = app.wallet.sign_transaction(txn)
                txn_hash = app.client.submit_transaction(signed_txn)

                # Wait for transaction confirmation
                app.client.wait_for_transaction(txn_hash)

                # Mark as registered
                app.is_registered = True
                st.session_state.app = app

                st.success("🎉 Registration completed successfully!")
                st.success(f"✅ Transaction Hash: `{txn_hash}`")
                st.info("**Next:** Go to 'Authentication' to verify your 1P secret")

                # Show registration summary
                with st.expander("Registration Summary", expanded=True):
                    st.markdown(f"""
                    - **Wallet:** `{app.wallet.address()}`
                    - **Secret:** {app.selected_secret} (U+{ord(app.selected_secret):04X})
                    - **Amount Transferred:** {transfer_amount} APT
                    - **Transaction:** `{txn_hash}`
                    - **System Wallet:** `{SYSTEM_WALLET_ADDRESS}`
                    """)

            except Exception as e:
                st.error(f"❌ Registration failed: {str(e)}")
                st.error("Please check your balance and try again")