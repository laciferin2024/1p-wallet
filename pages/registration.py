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
col1, col2 = st.columns(2)
with col1:
    category_type = st.selectbox(
        "Category Type",
        options=["Emojis & Symbols", "Languages", "All Categories"],
        index=0,
        help="Filter by type of character categories"
    )

    # Dynamically set options based on category type
    if category_type == "Emojis & Symbols":
        category_options = ['emojis', 'hearts', 'nature', 'food', 'animals', 'travel', 'sports', 'tech', 'music', 'weather', 'zodiac', 'numbers', 'symbols', 'ascii']
    elif category_type == "Languages":
        category_options = ['japanese', 'korean', 'chinese', 'arabic', 'cyrillic', 'ascii']
    else:
        category_options = list(DOMAINS.keys())

    selected_categories = st.multiselect(
        "Character Categories",
        options=category_options,
        default=['emojis'] if category_type == "Emojis & Symbols" else ['ascii'] if category_type == "Languages" else ['emojis'],
        help="Select which types of characters to show"
    )

with col2:
    col2_1, col2_2 = st.columns(2)
    with col2_1:
        chars_per_row = st.slider("Characters per row", 5, 20, 10)
    with col2_2:
        show_unicode = st.checkbox("Show Unicode codes", False)

    search_term = st.text_input("Search (emoji description or character)", "",
                               placeholder="heart, food, smile, etc.",
                               help="Filter characters by description")

# Build character set based on selection
available_chars = ""
for category in selected_categories:
    available_chars += DOMAINS[category]

if not available_chars:
    st.warning("Please select at least one character category")
    st.stop()

# Apply search filter if provided
chars_list = list(set(available_chars))  # Remove duplicates

if search_term:
    # Simple filtering mechanism
    search_term = search_term.lower()

    # Define some common emoji descriptions for better search
    emoji_descriptions = {
        'smile': '😀😃😄😁😆',
        'laugh': '😂🤣',
        'heart': '❤️💖💝💘💗💓💕💞💜🧡💛💚💙',
        'food': '🍎🍌🍇🍓🍈🍉🍊🍋🥭🍑🍒🥝🍍🥥🍅🥑🍆🥔🥕🌽',
        'animal': '🐶🐱🐭🐹🐰🦊🐻🐼🐨🦁🐯🐮🐷🐸🐵🐔',
        'flower': '🌸🌺🌻🌷🌹🌼',
        'star': '⭐🌟💫✨',
        'face': '😀😃😄😁😆😅😂🤣😊😇🙂🙃😉😌😍',
        'hand': '👍👎👌✌️🤞🤟🤘👊✊🤛🤜👏',
        'music': '🎵🎶🎸🎹🎷🎺🎻🥁🎼',
        'sport': '⚽⚾🏀🏐🏈🏉🎾🏓🏸',
        'travel': '✈️🚆🚂🚄🚘🚲',
        'weather': '☀️🌤️⛅🌥️☁️🌦️🌧️⛈️'
    }

    filtered_chars = []
    for char in chars_list:
        # Check if char is in any of the emoji description groups that match the search term
        in_description = False
        for desc, emoji_group in emoji_descriptions.items():
            if desc.lower().find(search_term) >= 0 and char in emoji_group:
                in_description = True
                break

        # Add char if it matches search
        if in_description or char.lower() == search_term.lower():
            filtered_chars.append(char)

    chars_list = filtered_chars if filtered_chars else chars_list

# Sort the characters
chars_list.sort()

# Create a pagination system for large character sets
chars_per_page = chars_per_row * 5  # 5 rows per page
total_chars = len(chars_list)
total_pages = (total_chars + chars_per_page - 1) // chars_per_page  # Ceiling division

# Only show pagination if needed
if total_pages > 1:
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        page_num = st.select_slider("Page", options=list(range(1, total_pages + 1)), value=1)
else:
    page_num = 1

start_idx = (page_num - 1) * chars_per_page
end_idx = min(start_idx + chars_per_page, total_chars)

# Display character selection grid
st.markdown(f"**Available Characters:** ({total_chars} characters found)")
visible_chars = chars_list[start_idx:end_idx]

# Create grid display
rows = [visible_chars[i:i + chars_per_row] for i in range(0, len(visible_chars), chars_per_row)]

selected_secret = None
for row_idx, row in enumerate(rows):
    cols = st.columns(len(row))
    for col_idx, char in enumerate(row):
        with cols[col_idx]:
            unicode_info = f"\\nU+{ord(char):04X}" if show_unicode else ""
            if st.button(f"{char}{unicode_info}",
                      key=f"char_{row_idx}_{col_idx}_p{page_num}",
                      use_container_width=True):
                selected_secret = char
                app.selected_secret = char
                st.session_state.app = app
                st.rerun()

# Show recently used characters for quick selection
if not app.selected_secret and (app.recent_characters or app.favorite_characters):
    st.markdown("---")
    st.subheader("⭐ Quick Selection")

    # Show favorites if available
    if app.favorite_characters:
        st.markdown("**Favorite Characters:**")
        fav_cols = st.columns(min(10, len(app.favorite_characters)))
        for idx, char in enumerate(app.favorite_characters):
            with fav_cols[idx % len(fav_cols)]:
                if st.button(f"{char}",
                          key=f"fav_{idx}",
                          use_container_width=True):
                    app.selected_secret = char
                    st.session_state.app = app
                    st.rerun()

    # Show recent characters if available
    if app.recent_characters:
        st.markdown("**Recently Used:**")
        recent_cols = st.columns(min(10, len(app.recent_characters)))
        for idx, char in enumerate(app.recent_characters):
            with recent_cols[idx % len(recent_cols)]:
                if st.button(f"{char}",
                          key=f"recent_{idx}",
                          use_container_width=True):
                    app.selected_secret = char

                    # Add to favorites
                    with recent_cols[idx % len(recent_cols)]:
                        if st.button("⭐", key=f"fav_add_{idx}", help="Add to favorites"):
                            if char not in app.favorite_characters:
                                app.favorite_characters.append(char)
                                if len(app.favorite_characters) > 10:
                                    app.favorite_characters.pop(0)  # Remove oldest if over limit

                    st.session_state.app = app
                    st.rerun()

# Show selected secret
if app.selected_secret:
    st.success(f"✅ Selected secret: **{app.selected_secret}** (U+{ord(app.selected_secret):04X})")

    # Add selected character to recent list if not already there
    if app.selected_secret not in app.recent_characters:
        app.recent_characters.append(app.selected_secret)
        # Keep only the last 10 characters
        if len(app.recent_characters) > 10:
            app.recent_characters.pop(0)
        st.session_state.app = app

    # Option to add to favorites
    col1, col2 = st.columns([3, 1])
    with col2:
        if app.selected_secret not in app.favorite_characters:
            if st.button("⭐ Add to Favorites"):
                app.favorite_characters.append(app.selected_secret)
                if len(app.favorite_characters) > 10:
                    app.favorite_characters.pop(0)  # Remove oldest if over limit
                st.session_state.app = app
                st.rerun()
        else:
            if st.button("❌ Remove from Favorites"):
                app.favorite_characters.remove(app.selected_secret)
                st.session_state.app = app
                st.rerun()

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
    st.subheader("💰 Step 3: Transfer Funds for Registration")

    st.markdown("**Why transfer funds?**")
    st.markdown("""
    - Transfers 1 APT minimum to register for the 1P system
    - Your funds are held securely in our system wallet
    - Transactions are processed through our secure backend
    - Your private key is never exposed after registration
    """)

    # Check current balance automatically
    with st.spinner("Checking wallet balance..."):
        try:
            # Try to use the sync helper method
            apt_balance = app.get_account_balance_sync(app.wallet.address())

            # Display balance with colorful metric
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Current Wallet Balance", f"{apt_balance} APT")
            with col2:
                if apt_balance >= 1.0:
                    st.success("✅ Sufficient balance for registration")
                else:
                    st.error("❌ Insufficient balance. Need at least 1 APT.")
                    st.warning("Please use the faucet in the wallet setup page.")
                    st.stop()

            # Add refresh button
            if st.button("🔄 Refresh Balance", type="secondary"):
                st.rerun()

        except Exception as e:
            st.error(f"Balance check error: {str(e)}")
            st.warning("Unable to check balance automatically. You can proceed if you know you have sufficient funds (at least 1 APT).")

            # Add manual balance check option
            if st.button("Try Again", type="secondary"):
                st.rerun()

            # Provide option to continue anyway
            st.info("If you're certain you have at least 1 APT, you can continue with the registration.")

            # Option to proceed anyway
            if not st.checkbox("I understand the risks and want to proceed anyway"):
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
    - **From Wallet:** `{app.wallet.address()[:10]}...`
    """)

    st.error("🔒 **Important:** After registration, your wallet's private key will be securely handled by our system. Make sure you're ready to proceed.")

    confirm_registration = st.checkbox("I understand and want to proceed with registration")

    if confirm_registration and st.button("🚀 Complete Registration", type="primary"):
        with st.spinner("Processing registration..."):
            try:
                # Check user wallet balance first
                apt_balance = app.get_account_balance_sync(app.wallet.address())

                if apt_balance < transfer_amount:
                    st.error(f"❌ Insufficient balance: You have {apt_balance} APT but are trying to transfer {transfer_amount} APT")
                    st.warning("Please get more APT from the faucet or reduce the transfer amount.")
                    st.stop()

                # Create transfer transaction
                amount_in_octas = int(transfer_amount * 100000000)  # Convert APT to octas

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
                        [SYSTEM_WALLET_ADDRESS, serialized_amount]
                    )

                    # Create and submit transaction - handling potential async issues
                    from utils.aptos_sync import RestClientSync
                    # Use the sync wrapper to ensure compatibility with streamlit
                    sync_client = RestClientSync("https://testnet.aptoslabs.com/v1")

                    # Create and process the transaction
                    with st.spinner("Creating transaction..."):
                        txn = sync_client.create_transaction(app.wallet.address(), payload)

                    with st.spinner("Signing transaction..."):
                        signed_txn = app.wallet.sign_transaction(txn)

                    with st.spinner("Submitting transaction..."):
                        txn_hash = sync_client.submit_transaction(signed_txn)

                    with st.spinner("Waiting for confirmation..."):
                        sync_client.wait_for_transaction(txn_hash, timeout=30)

                except Exception as e:
                    st.error(f"Transaction failed: {str(e)}")
                    st.warning("Please check your balance and try again.")
                    st.stop()

                # Mark as registered and record the transaction
                app.is_registered = True

                # Record transaction in our history
                app.add_transaction(
                    txn_hash=txn_hash,
                    sender=str(app.wallet.address()),
                    recipient=SYSTEM_WALLET_ADDRESS,
                    amount=transfer_amount,
                    is_credit=False,
                    status="completed",
                    description="1P Wallet Registration"
                )

                st.session_state.app = app

                st.success("🎉 Registration completed successfully!")
                st.success(f"✅ Transaction Hash: `{txn_hash}`")
                st.info("**Next:** Go to 'Authentication' to verify your 1P secret")
                st.markdown("📋 You can view this transaction in your **Transaction History** page")

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