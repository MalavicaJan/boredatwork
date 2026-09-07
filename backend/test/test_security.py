from app.security import hash_password, verify_password


def test_password_hash_is_not_plaintext():
    password = "test-password"

    password_hash = hash_password(password)

    assert password_hash != password


def test_password_verification_succeeds_for_correct_password():
    password = "test-password"

    password_hash = hash_password(password)

    assert verify_password(password, password_hash)


def test_password_verification_fails_for_wrong_password():
    password = "test-password"

    password_hash = hash_password(password)

    assert not verify_password("wrong-password", password_hash)