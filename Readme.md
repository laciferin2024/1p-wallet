# 1P Wallet

A Streamlit app implementing a 2FA-like visual authentication for Aptos wallets.

Quick start (dev/testnet):

1. Create a virtualenv and install deps:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Set required environment variables (for full functionality):

```bash
export APTOS_ACCOUNT=0x...       # system wallet address
export APTOS_PRIVATE_KEY=...     # system wallet private key (hex)
```

3. Run the app:

```bash
streamlit run app.py
```

Notes:
- This project is for demonstration. Do not use the provided scripts in production without proper key management.
- Use `scripts/verify_env.sh` to confirm environment variables are present.
