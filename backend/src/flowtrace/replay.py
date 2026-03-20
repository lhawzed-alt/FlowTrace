import json
from urllib.parse import urljoin

import requests

from .config import TARGET_BASE_URL, REPLAY_TIMEOUT, logger


def build_full_url(target_url: str) -> str:
    if target_url.lower().startswith(("http://", "https://")):
        return target_url
    base = TARGET_BASE_URL.rstrip("/") + "/"
    return urljoin(base, target_url.lstrip("/"))


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
        return headers, params, json_payload, data_payload

    if method == "GET":
        params = parsed if isinstance(parsed, dict) else None
    else:
        json_payload = parsed

    return headers, params, json_payload, data_payload


def dispatch_replay(method: str, url: str, request_body: str) -> requests.Response:
    full_url = build_full_url(url)
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
