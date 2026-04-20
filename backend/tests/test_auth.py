import time

from jose import jwt

from auth import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    hash_password,
    verify_password,
)


def test_hash_is_not_plaintext_and_verifies():
    hashed = hash_password("hunter2")
    assert hashed != "hunter2"
    assert verify_password("hunter2", hashed)


def test_wrong_password_fails():
    hashed = hash_password("hunter2")
    assert not verify_password("wrong", hashed)


def test_token_roundtrip_encodes_subject():
    token = create_access_token(subject="42")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "42"
    assert payload["exp"] > time.time()
