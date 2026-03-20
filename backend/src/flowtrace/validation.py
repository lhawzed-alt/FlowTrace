import re

from .config import ALLOWED_METHODS

HEADER_NAME_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")


def validate_http_headers(headers):
    if headers is None:
        return {}
    if not isinstance(headers, dict):
        raise ValueError("Headers must be a dictionary of name/value pairs")

    sanitized = {}
    for raw_name, raw_value in headers.items():
        if not isinstance(raw_name, str):
            raise ValueError("HTTP header names must be strings")
        name = raw_name.strip()
        if not name or HEADER_NAME_RE.fullmatch(name) is None:
            raise ValueError(f"Invalid HTTP header name '{raw_name}'")

        if isinstance(raw_value, bytes):
            value = raw_value.decode("utf-8")
        else:
            value = raw_value

        if isinstance(value, (int, float)):
            value = str(value)

        if not isinstance(value, str):
            raise ValueError(f"HTTP header '{name}' value must be a string")

        if "\r" in value or "\n" in value:
            raise ValueError(f"HTTP header '{name}' contains disallowed control characters")

        sanitized[name] = value

    return sanitized


def validate_api_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("JSON body is required")

    method = payload.get("method")
    if not method or not isinstance(method, str):
        raise ValueError("Field 'method' is required and has to be a string")
    method = method.upper()
    if method not in ALLOWED_METHODS:
        raise ValueError(f"Unsupported HTTP method '{method}'")

    url = payload.get("url")
    if not url or not isinstance(url, str):
        raise ValueError("Field 'url' is required and must be a string")
    url = url.strip()

    status_code = payload.get("status_code")
    if status_code is None:
        raise ValueError("Field 'status_code' is required")
    try:
        status_code = int(status_code)
    except (TypeError, ValueError):
        raise ValueError("Field 'status_code' must be an integer")
    if not 100 <= status_code <= 599:
        raise ValueError("Field 'status_code' must be between 100 and 599")

    request_body = payload.get("request_body") or ""
    response_body = payload.get("response_body") or ""
    tags = payload.get("tags") or ""

    return method, url, status_code, request_body, response_body, tags
