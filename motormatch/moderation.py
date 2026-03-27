def next_listing_status(action: str) -> str:
    """
    Mirrors current moderation behavior in main.py:
    - action == "approve" -> "approved"
    - anything else -> "hidden"
    """
    return "approved" if (action or "").strip() == "approve" else "hidden"

