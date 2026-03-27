import pytest


from motormatch.vin_rules import vin_is_valid


def test_vin_rejects_wrong_length():
    assert vin_is_valid("123") is False
    assert vin_is_valid("1HGCM82633A0043520") is False  # 18 chars


@pytest.mark.parametrize("bad", ["IOQ12345678901234", "1HGCM82633A00I352"])
def test_vin_rejects_disallowed_letters(bad):
    assert vin_is_valid(bad) is False

