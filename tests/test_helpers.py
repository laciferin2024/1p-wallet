from utils.helpers import generate_nonce, keccak256, generate_entropy_layers


def test_generate_nonce_length():
    n = generate_nonce()
    assert isinstance(n, str)
    assert len(n) == 64  # 32 bytes hex


def test_keccak256_known():
    h = keccak256('abc')
    assert isinstance(h, str)
    assert len(h) == 64


def test_generate_entropy_layers_consistent():
    arr1 = generate_entropy_layers('seed', 3)
    arr2 = generate_entropy_layers('seed', 3)
    assert arr1 == arr2
    assert len(arr1) == 3