import unittest

from flowtrace.validation import validate_api_payload, validate_http_headers


class ValidatePayloadTests(unittest.TestCase):
    def test_happy_path(self):
        payload = {
            "method": "post",
            "url": "/api/test",
            "status_code": "201",
            "request_body": '{"hi":"world"}',
            "response_body": "",
            "tags": "smoke",
        }
        validated = validate_api_payload(payload)
        self.assertEqual(validated[0], "POST")
        self.assertEqual(validated[1], "/api/test")
        self.assertEqual(validated[2], 201)

    def test_missing_method(self):
        with self.assertRaises(ValueError):
            validate_api_payload({"url": "/api", "status_code": 200})

    def test_bad_status_code(self):
        with self.assertRaises(ValueError):
            validate_api_payload({"method": "GET", "url": "/api", "status_code": "abc"})

    def test_validate_http_headers_accepts_safe_values(self):
        headers = validate_http_headers({"X-Test": "value", "X-Number": 7})
        self.assertEqual(headers["X-Test"], "value")
        self.assertEqual(headers["X-Number"], "7")

    def test_validate_http_headers_rejects_invalid_name(self):
        with self.assertRaises(ValueError):
            validate_http_headers({"Bad Name": "value"})

    def test_validate_http_headers_rejects_control_characters(self):
        with self.assertRaises(ValueError):
            validate_http_headers({"X-Test": "value\nbad"})
