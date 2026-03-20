import json
from queue import Empty, SimpleQueue
from threading import Lock

from flask_sock import Sock

from .config import logger

sock = Sock()
_clients: list[SimpleQueue] = []
_clients_lock = Lock()


def register_trace_client() -> SimpleQueue:
    queue = SimpleQueue()
    with _clients_lock:
        _clients.append(queue)
    return queue


def unregister_trace_client(queue: SimpleQueue) -> None:
    with _clients_lock:
        if queue in _clients:
            _clients.remove(queue)


def broadcast_trace(payload: dict) -> None:
    if not payload:
        return
    message = json.dumps(payload)
    with _clients_lock:
        clients = list(_clients)
    for client in clients:
        client.put(message)


@sock.route("/ws/traces")
def stream_traces(ws):
    queue = register_trace_client()
    try:
        while not ws.closed:
            try:
                message = queue.get(timeout=1)
            except Empty:
                continue
            ws.send(message)
    except Exception:
        logger.exception("Trace WebSocket disconnected unexpectedly")
    finally:
        unregister_trace_client(queue)
