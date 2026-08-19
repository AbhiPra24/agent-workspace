import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.linkedin_client import LinkedInClient, LinkedInAPIError
from src.cli import render_post_preview

class TestLinkedInClient(unittest.TestCase):

    def setUp(self):
        self.mock_session = MagicMock()
        self.client = LinkedInClient(
            access_token="test_token_123",
            refresh_token="test_refresh_456",
            client_id="test_client_id",
            client_secret="test_client_secret",
            session=self.mock_session,
        )

    def test_global_headers_injection(self):
        """Verify LinkedIn-Version and X-Restli-Protocol-Version are present on all requests."""
        headers = self.client._get_headers(method="GET")
        self.assertEqual(headers["LinkedIn-Version"], "202401")
        self.assertEqual(headers["X-Restli-Protocol-Version"], "2.0.0")
        self.assertEqual(headers["Authorization"], "Bearer test_token_123")
        self.assertNotIn("X-RestLi-Idempotency-Key", headers)

    def test_idempotency_key_on_post_requests(self):
        """Verify unique UUID is injected for POST requests."""
        headers1 = self.client._get_headers(method="POST")
        headers2 = self.client._get_headers(method="POST")
        
        self.assertIn("X-RestLi-Idempotency-Key", headers1)
        self.assertIn("X-RestLi-Idempotency-Key", headers2)
        # Ensure distinct keys per call
        self.assertNotEqual(headers1["X-RestLi-Idempotency-Key"], headers2["X-RestLi-Idempotency-Key"])

    def test_create_post_payload_structure(self):
        """Verify /rest/posts endpoint and standard payload formatting."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 201
        mock_response.headers = {"x-restli-id": "urn:li:share:123456"}
        mock_response.json.return_value = {"id": "urn:li:share:123456"}
        self.mock_session.request.return_value = mock_response

        res = self.client.create_post(
            text="Testing LinkedIn REST API with #ai",
            author_urn="urn:li:person:abcdef",
            visibility="PUBLIC"
        )

        self.mock_session.request.assert_called_once()
        args, kwargs = self.mock_session.request.call_args
        
        self.assertEqual(kwargs["method"], "POST")
        self.assertEqual(kwargs["url"], "https://api.linkedin.com/rest/posts")
        
        payload = kwargs["json"]
        self.assertEqual(payload["author"], "urn:li:person:abcdef")
        self.assertEqual(payload["commentary"], "Testing LinkedIn REST API with #ai")
        self.assertEqual(payload["visibility"], "PUBLIC")
        self.assertEqual(payload["lifecycleState"], "PUBLISHED")
        self.assertIn("distribution", payload)
        self.assertEqual(res["id"], "urn:li:share:123456")

    def test_create_post_with_article_link(self):
        """Verify article link inclusion in payload."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.headers = {"x-restli-id": "urn:li:share:999"}
        mock_response.json.return_value = {}
        self.mock_session.request.return_value = mock_response

        self.client.create_post(
            text="Check out this article",
            author_urn="urn:li:person:abcdef",
            article_url="https://example.com/article",
            article_title="Example Title"
        )

        _, kwargs = self.mock_session.request.call_args
        payload = kwargs["json"]
        self.assertIn("content", payload)
        self.assertEqual(payload["content"]["article"]["source"], "https://example.com/article")
        self.assertEqual(payload["content"]["article"]["title"], "Example Title")

    def test_initialize_image_upload(self):
        """Verify 2-step media upload step 1 endpoint and request."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "value": {
                "uploadUrl": "https://media.licdn.com/upload/xyz",
                "image": "urn:li:image:C4E12345"
            }
        }
        self.mock_session.request.return_value = mock_response

        init_data = self.client.initialize_image_upload("urn:li:person:abcdef")
        
        _, kwargs = self.mock_session.request.call_args
        self.assertEqual(kwargs["url"], "https://api.linkedin.com/rest/images?action=initializeUpload")
        self.assertEqual(init_data["upload_url"], "https://media.licdn.com/upload/xyz")
        self.assertEqual(init_data["image_urn"], "urn:li:image:C4E12345")

    def test_refresh_token_exchange(self):
        """Verify 365-day refresh token rotation request."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "access_token": "new_access_token_789",
            "refresh_token": "new_refresh_token_000",
            "expires_in": 5184000
        }
        self.mock_session.post.return_value = mock_response

        token_data = self.client.refresh_access_token()
        
        self.mock_session.post.assert_called_once()
        _, kwargs = self.mock_session.post.call_args
        self.assertEqual(kwargs["data"]["grant_type"], "refresh_token")
        self.assertEqual(kwargs["data"]["refresh_token"], "test_refresh_456")
        self.assertEqual(self.client.access_token, "new_access_token_789")

    def test_preview_character_limit_guardrail(self):
        """Verify dry-run guardrail catches posts exceeding 3,000 chars."""
        short_post = "Valid short post #tech"
        self.assertTrue(render_post_preview(short_post, "urn:li:person:123"))

        overlength_post = "A" * 3001
        self.assertFalse(render_post_preview(overlength_post, "urn:li:person:123"))


if __name__ == "__main__":
    unittest.main()
