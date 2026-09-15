from app.core.security.passwords import hash_password, verify_password


def test_hash_password_does_not_store_plaintext_and_verifies() -> None:
    encoded = hash_password("secret123")

    assert encoded != "secret123"
    assert encoded.startswith("$argon2")
    assert verify_password("secret123", encoded) is True
    assert verify_password("wrong-password", encoded) is False
