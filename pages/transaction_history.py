# Transaction History Page
# This page displays the user's transaction history, showing credits and debits

import streamlit as st

from pages import app


st.header("📋 Transaction History")

if not app.wallet:
    st.error("❌ Please connect a wallet first")
    st.info("👈 Go to 'Import/Generate Wallet' to get started")
    st.stop()

# Button to refresh transaction history
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("View your transaction history, including credits and debits")
with col2:
    if st.button("🔄 Refresh History", type="secondary"):
        with st.spinner("Updating transaction history..."):
            success = app.update_transaction_history()
            if success:
                st.success("Transaction history updated!")
            else:
                st.error("Failed to update transaction history")
        st.rerun()

# If we don't have any transactions yet, try to fetch them
if not app.transactions:
    with st.spinner("Fetching your transaction history..."):
        app.update_transaction_history()
        st.session_state.app = app

# Show transaction summary
st.markdown("---")
st.subheader("💰 Balance Summary")

# Calculate summary statistics
if app.transactions:
    total_credits = sum(txn.amount for txn in app.transactions if txn.is_credit and txn.status == "completed")
    total_debits = sum(txn.amount for txn in app.transactions if not txn.is_credit and txn.status == "completed")
    net_balance = total_credits - total_debits

    # Display summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Credits", f"{total_credits:.4f} APT", delta=f"{total_credits:.2f}")
    with col2:
        st.metric("Total Debits", f"{total_debits:.4f} APT", delta=f"-{total_debits:.2f}", delta_color="inverse")
    with col3:
        st.metric("Net Balance", f"{net_balance:.4f} APT")

    # Display current blockchain balance
    st.markdown("---")
    with st.spinner("Checking current blockchain balance..."):
        try:
            current_balance = app.get_account_balance_sync(app.wallet.address())
            st.info(f"Current blockchain balance: **{current_balance:.4f} APT**")
        except Exception as e:
            st.warning(f"Could not fetch current balance: {str(e)}")
else:
    st.info("No transactions found. Your transaction history will appear here once you make transfers.")

# Display transaction list
st.markdown("---")
st.subheader("📝 Transaction List")

if app.transactions:
    # Create tabs for all/credits/debits
    tab1, tab2, tab3 = st.tabs(["All Transactions", "Credits (Received)", "Debits (Sent)"])

    with tab1:
        # All transactions
        for idx, txn in enumerate(app.transactions):
            with st.expander(
                f"{'↘️ Received' if txn.is_credit else '↗️ Sent'} {txn.amount:.4f} APT - {time.strftime('%Y-%m-%d %H:%M', time.localtime(txn.timestamp))}",
                expanded=(idx == 0)  # Only expand first one by default
            ):
                st.markdown(f"""
                **Transaction:** `{txn.txn_hash[:10]}...{txn.txn_hash[-6:]}`
                **From:** `{txn.sender[:10]}...{txn.sender[-6:]}`
                **To:** `{txn.recipient[:10]}...{txn.recipient[-6:]}`
                **Amount:** {txn.amount:.8f} APT
                **Status:** {txn.status.title()}
                **Date:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(txn.timestamp))}
                """)

                # Add link to explorer
                st.markdown(f"[View on Explorer](https://explorer.aptoslabs.com/txn/{txn.txn_hash}?network=testnet)")

    with tab2:
        # Credits only
        credits = [txn for txn in app.transactions if txn.is_credit]
        if credits:
            for idx, txn in enumerate(credits):
                with st.expander(
                    f"↘️ Received {txn.amount:.4f} APT - {time.strftime('%Y-%m-%d %H:%M', time.localtime(txn.timestamp))}",
                    expanded=(idx == 0)
                ):
                    st.markdown(f"""
                    **Transaction:** `{txn.txn_hash[:10]}...{txn.txn_hash[-6:]}`
                    **From:** `{txn.sender[:10]}...{txn.sender[-6:]}`
                    **To:** `{txn.recipient[:10]}...{txn.recipient[-6:]}`
                    **Amount:** {txn.amount:.8f} APT
                    **Status:** {txn.status.title()}
                    **Date:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(txn.timestamp))}
                    """)

                    # Add link to explorer
                    st.markdown(f"[View on Explorer](https://explorer.aptoslabs.com/txn/{txn.txn_hash}?network=testnet)")
        else:
            st.info("No credits (received funds) found in transaction history.")

    with tab3:
        # Debits only
        debits = [txn for txn in app.transactions if not txn.is_credit]
        if debits:
            for idx, txn in enumerate(debits):
                with st.expander(
                    f"↗️ Sent {txn.amount:.4f} APT - {time.strftime('%Y-%m-%d %H:%M', time.localtime(txn.timestamp))}",
                    expanded=(idx == 0)
                ):
                    st.markdown(f"""
                    **Transaction:** `{txn.txn_hash[:10]}...{txn.txn_hash[-6:]}`
                    **From:** `{txn.sender[:10]}...{txn.sender[-6:]}`
                    **To:** `{txn.recipient[:10]}...{txn.recipient[-6:]}`
                    **Amount:** {txn.amount:.8f} APT
                    **Status:** {txn.status.title()}
                    **Date:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(txn.timestamp))}
                    """)

                    # Add link to explorer
                    st.markdown(f"[View on Explorer](https://explorer.aptoslabs.com/txn/{txn.txn_hash}?network=testnet)")
        else:
            st.info("No debits (sent funds) found in transaction history.")
else:
    st.info("No transactions found. Your transactions will appear here once you make transfers.")

# Add tips for transaction history
st.markdown("---")
st.markdown("""
### 📊 About Transaction Tracking
- **Credits**: Funds received by your wallet
- **Debits**: Funds sent from your wallet
- **Blockchain Validation**: All transactions are verified and stored on the Aptos blockchain
- **History**: Transaction history is cached locally during your session
""")