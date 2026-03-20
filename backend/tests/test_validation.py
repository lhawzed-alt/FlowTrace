import unittest

from flowtrace.validation import validate_api_payload


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
