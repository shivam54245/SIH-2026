import pytest

from src.utils.authenticator import hash_password, verify_password


def test_password_hash_verifies():
    hashed_password = hash_password("1234qwerty")

    assert hashed_password != "1234qwerty"
    assert verify_password("1234qwerty", hashed_password)
    assert not verify_password("wrong-password", hashed_password)


def test_password_hash_rejects_passwords_over_bcrypt_limit():
    with pytest.raises(ValueError, match="72 bytes"):
        hash_password("x" * 73)
