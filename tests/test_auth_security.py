from app.core.security import generate_secure_token, hash_password, hash_token, verify_password


def test_password_hash_does_not_store_plaintext() -> None:
    password = "StrongPassword123!"

    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash)


def test_verify_password_rejects_wrong_password() -> None:
    password_hash = hash_password("StrongPassword123!")

    assert not verify_password("WrongPassword123!", password_hash)


def test_secure_token_generation_returns_different_values() -> None:
    first_token = generate_secure_token()
    second_token = generate_secure_token()

    assert first_token != second_token
    assert len(first_token) >= 64


def test_token_hash_is_deterministic_and_not_plaintext() -> None:
    token = "athr_live_test_token"

    first_hash = hash_token(token)
    second_hash = hash_token(token)

    assert first_hash == second_hash
    assert first_hash != token
