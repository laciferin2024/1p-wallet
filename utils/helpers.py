import secrets
import hashlib
from typing import List


def generate_nonce() -> str:
    return secrets.token_hex(32)


def keccak256(data: str) -> str:
    return hashlib.sha3_256(data.encode('utf-8')).hexdigest()


def generate_entropy_layers(seed: str, layers: int) -> List[int]:
    arr = []
    cur = seed
    for _ in range(layers):
        h = keccak256(cur)
        val = int(h[:8], 16)
        arr.append(val)
        cur = h
    return arr
