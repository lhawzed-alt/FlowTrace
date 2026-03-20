import json
from urllib.parse import urljoin, urlparse

import requests

from .config import ALLOWED_REPLAY_HOSTS, TARGET_BASE_URL, REPLAY_TIMEOUT, logger
from .validation import validate_http_headers


def build_full_url(target_url: str) -> str:
    if target_url.lower().startswith(("http://", "https://")):
        return target_url
    base = TARGET_BASE_URL.rstrip("/") + "/"
    return urljoin(base, target_url.lstrip("/"))


def _ensure_url_allowed(full_url: str):
    parsed = urlparse(full_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Replay target must use http or https")
    if not parsed.netloc:
        raise ValueError("Replay target is missing a host")

    candidates = {parsed.netloc.lower()}
    hostname = parsed.hostname.lower() if parsed.hostname else None
    if hostname:
        candidates.add(hostname)
        if parsed.port:
            candidates.add(f"{hostname}:{parsed.port}")

    if not ALLOWED_REPLAY_HOSTS & candidates:
        target = hostname or parsed.netloc
        raise ValueError(f"Replay target host '{target}' is not in the allow list")


def _extract_custom_headers(payload_dict: dict):
    raw_headers = payload_dict.pop("headers", None)
    if raw_headers is None:
        return {}
    return validate_http_headers(raw_headers)


def prepare_replay_payload(method: str, request_body: str):
    headers = {"Accept": "application/json"}
    params = None
    json_payload = None
    data_payload = None

    if not request_body:
        return headers, params, json_payload, data_payload

    try:
        parsed = json.loads(request_body)
    except json.JSONDecodeError:
        data_payload = request_body
        headers["Content-Type"] = "text/plain"
    else:
        custom_headers = {}
        if isinstance(parsed, dict):
            custom_headers = _extract_custom_headers(parsed)
        if method == "GET":
            params = parsed if isinstance(parsed, dict) else None
        else:
            json_payload = parsed
        if custom_headers:
            headers.update(custom_headers)

    headers = validate_http_headers(headers)
    return headers, params, json_payload, data_payload


def dispatch_replay(method: str, url: str, request_body: str) -> requests.Response:
    full_url = build_full_url(url)
    _ensure_url_allowed(full_url)
    headers, params, json_payload, data_payload = prepare_replay_payload(method, request_body)

    response = requests.request(
        method,
        full_url,
        params=params,
        json=json_payload,
        data=data_payload,
        headers=headers,
        timeout=REPLAY_TIMEOUT,
    )
    if not response.ok:
        logger.warning("Replay request returned %s for %s %s", response.status_code, method, full_url)
    return response
