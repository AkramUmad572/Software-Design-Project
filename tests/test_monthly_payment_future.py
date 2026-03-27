import pytest


from motormatch.pricing import estimate_monthly_payment


def test_monthly_payment_zero_apr_is_principal_div_months():
    # price 24,000, 0% APR, 60 months => 400/mo
    assert estimate_monthly_payment(24000, apr=0.0, months=60) == pytest.approx(400.0)


def test_monthly_payment_respects_down_payment():
    # 24,000 price with 6,000 down => 18,000 principal; 0% APR, 60 months => 300/mo
    assert estimate_monthly_payment(24000, apr=0.0, months=60, down_payment=6000) == pytest.approx(300.0)

