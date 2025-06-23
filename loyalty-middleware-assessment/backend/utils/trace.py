import uuid


def generate_trace_id() -> str:
    """Generate a unique trace ID for RFC 7807 errors."""
    return str(uuid.uuid4())
