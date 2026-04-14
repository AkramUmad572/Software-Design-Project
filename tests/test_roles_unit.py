import pytest

from motormatch.roles import can_demote, can_promote, normalize_role


@pytest.mark.unit
def test_normalize_role_lowercases_and_strips():
    assert normalize_role("  AdMiN ") == "admin"


@pytest.mark.unit
def test_normalize_role_handles_none():
    assert normalize_role(None) == ""


@pytest.mark.unit
def test_can_promote_only_customers():
    assert can_promote("customer") is True
    assert can_promote("admin") is False
    assert can_promote("whatever") is False


@pytest.mark.unit
def test_can_demote_requires_admin_role():
    assert can_demote("customer", admin_count=2) is False
    assert can_demote("unknown", admin_count=2) is False


@pytest.mark.unit
def test_can_demote_blocks_last_admin():
    assert can_demote("admin", admin_count=1) is False
    assert can_demote("admin", admin_count=0) is False


@pytest.mark.unit
def test_can_demote_allows_when_multiple_admins():
    assert can_demote("admin", admin_count=2) is True
    assert can_demote("admin", admin_count=10) is True

