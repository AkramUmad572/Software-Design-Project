"""
Role-related helpers used for unit testing and documentation.

The live app stores roles as strings in the DB: 'customer' and 'admin'.
"""


def can_promote(role: str) -> bool:
    """True if this role can be promoted to admin."""
    return role == "customer"


def can_demote(role: str, admin_count: int) -> bool:
    """True if this role can be demoted to customer given current admin_count."""
    if role != "admin":
        return False
    return admin_count > 1


def normalize_role(role: str) -> str:
    """Normalize role inputs (defensive)."""
    return (role or "").strip().lower()

