import json
import unittest
from unittest import mock

from flowtrace import replay


class ReplayTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch("flowtrace.replay.requests.request")
        self.mock_request = patcher.start()
        self.addCleanup(patcher.stop)

    def test_prepare_replay_payload_includes_custom_headers(self):
        payload = json.dumps(
            {
                "headers": {"X-Custom": "value"},
                "body": {"hello": "world"},
            }
        )

        headers, params, json_payload, data_payload = replay.prepare_replay_payload("POST", payload)

        self.assertEqual(headers["X-Custom"], "value")
        self.assertEqual(json_payload, {"body": {"hello": "world"}})
        self.assertIsNone(params)
        self.assertIsNone(data_payload)

    def test_prepare_replay_payload_rejects_header_injection(self):
        payload = json.dumps({"headers": {"X-Injection": "bad\r\n"}}, separators=(",", ":"))
        with self.assertRaises(ValueError):
            replay.prepare_replay_payload("GET", payload)

    def test_dispatch_replay_blocks_unlisted_host(self):
        with mock.patch.object(replay, "ALLOWED_REPLAY_HOSTS", {"allowed.host"}):
            with self.assertRaises(ValueError):
                replay.dispatch_replay("GET", "http://unlisted.host/path", "")

    def test_dispatch_replay_allows_listed_host(self):
        self.mock_request.return_value = mock.Mock(status_code=200, ok=True, text="ok")
        with mock.patch.object(replay, "ALLOWED_REPLAY_HOSTS", {"allowed.host"}):
            response = replay.dispatch_replay("GET", "http://allowed.host/path", "")

        self.assertEqual(response.status_code, 200)
        self.mock_request.assert_called_once()
