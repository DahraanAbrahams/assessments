import secrets


def generate_booking_reference(member_id: str) -> str:
    """
    Generates a unique booking reference with the member ID prefix.

    Args:
        member_id (str): Unique member/customer/user ID string.

    Returns:
        str: A booking reference in the format '{member_id}_{suffix}'.
    """
    suffix = secrets.token_urlsafe(6).rstrip("=").upper()
    return f"{member_id}_{suffix}"
