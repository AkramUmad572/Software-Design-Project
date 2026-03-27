import pytest


from motormatch.auth_rules import password_is_strong


def test_password_strength_rejects_too_short():
    assert password_is_strong("a1b2c3") is False


def test_password_strength_rejects_missing_number():
    assert password_is_strong("password") is False


def test_password_strength_rejects_missing_letter():
    assert password_is_strong("12345678") is False


def test_password_strength_accepts_letter_and_number():
    assert password_is_strong("passw0rd") is True


@pytest.mark.parametrize(
    "pw",
    [
        "a2345678",
        "Abcdefg1",
        "Z9xxxxxxxx",
    ],
)
def test_password_strength_accepts_multiple_examples(pw):
    assert password_is_strong(pw) is True

