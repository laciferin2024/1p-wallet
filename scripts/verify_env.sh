#!/usr/bin/env bash
# Simple script to check required env vars for 1p-wallet

required=(APTOS_ACCOUNT APTOS_PRIVATE_KEY)
missing=()

for v in "${required[@]}"; do
  if [ -z "${!v}" ]; then
    missing+=("$v")
  fi
done

if [ ${#missing[@]} -eq 0 ]; then
  echo "All required env vars are set"
  exit 0
else
  echo "Missing required env vars: ${missing[*]}"
  echo "Please set them (e.g. export APTOS_ACCOUNT=0x... )"
  exit 1
fi
