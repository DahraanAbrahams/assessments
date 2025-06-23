from rest_framework.exceptions import APIException
from utils.trace import generate_trace_id


class ProblemDetailException(APIException):
    """
    Raised to produce an RFC 7807-compliant structured error response.
    """
    def __init__(
        self,
        *,
        type_: str,
        title: str,
        status: int,
        detail: str,
        instance: str,
        extra: dict = None,
    ):
        payload = {
            "error": {
                "type": type_,
                "title": title,
                "status": status,
                "detail": detail,
                "instance": instance,
                "trace_id": generate_trace_id(),
            }
        }
        if extra:
            payload["error"].update(extra)

        self.status_code = status
        self.detail = payload
