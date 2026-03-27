def estimate_monthly_payment(price: float, apr: float, months: int, down_payment: float = 0.0) -> float:
    """
    Future Iteration Feature (TDD):
    Estimate monthly payment for a vehicle loan.

    Planned behavior:
    - principal = max(price - down_payment, 0)
    - apr is annual percentage rate (e.g. 6.5 for 6.5%)
    - months is loan term in months
    - use standard amortization formula
    """
    raise NotImplementedError("Planned feature: loan payment estimation not implemented yet.")

