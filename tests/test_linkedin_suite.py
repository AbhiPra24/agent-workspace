#!/usr/bin/env python3
"""
Comprehensive Mocked Test Suite for LinkedIn Official API Suite.

Verifies:
- Global injection of mandatory headers (LinkedIn-Version: 202401, X-Restli-Protocol-Version: 2.0.0)
- Cryptographic UUID idempotency keys on all POST mutations
- Exclusively modern /rest/posts and 2-step /rest/images endpoints
- 365-day token refresh lifecycle and vault caching
- Rich dry-run character count guardrails
- FastMCP tool declarations and response formatting
"""

import unittest
from unittest.mock import MagicMock, patch, mock_open
import json
import os
import sys
from pathlib import Path

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.linkedin_suite import LinkedInClient, LinkedInAPIError, LinkedInTokenVault, render_post_preview
import scripts.linkedin_mcp as mcp_server


class TestLinkedInSuite(unittest.TestCase):

    def setUp(self):
        self.mock_session = MagicMock()
        self.client = LinkedInClient(
            access_token="test_access_token_123",
            refresh_token="test_refresh_token_456",
            client_id="test_client_id",
            client_secret="test_client_secret",
            session=self.mock_session,
        )

    def test_mandatory_global_headers(self):
        """Verifies LinkedIn-Version and X-Restli-Protocol-Version on every request."""
        headers = self.client._get_headers(method="GET")
        self.assertEqual(headers["LinkedIn-Version"], "202401")
        self.assertEqual(headers["X-Restli-Protocol-Version"], "2.0.0")
        self.assertEqual(headers["Authorization"], "Bearer test_access_token_123")
        self.assertNotIn("X-RestLi-Idempotency-Key", headers)

    def test_idempotency_keys_on_post_mutations(self):
        """Verifies unique UUID injection for X-RestLi-Idempotency-Key on POST calls."""
        h1 = self.client._get_headers(method="POST")
        h2 = self.client._get_headers(method="POST")
        
        self.assertIn("X-RestLi-Idempotency-Key", h1)
        self.assertIn("X-RestLi-Idempotency-Key", h2)
        # Ensure UUIDs are unique per request
        self.assertNotEqual(h1["X-RestLi-Idempotency-Key"], h2["X-RestLi-Idempotency-Key"])

    def test_create_post_payload_structure(self):
        """Verifies payload structure strictly targeting modern /rest/posts."""
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 201
        mock_resp.headers = {"x-restli-id": "urn:li:share:987654321"}
        mock_resp.json.return_value = {"id": "urn:li:share:987654321"}
        self.mock_session.request.return_value = mock_resp

        res = self.client.create_post(
            text="Autonomous AI Agent testing #python #ai",
            author_urn="urn:li:person:abcdef",
            visibility="PUBLIC"
        )

        self.mock_session.request.assert_called_once()
        _, kwargs = self.mock_session.request.call_args
        
        self.assertEqual(kwargs["method"], "POST")
        self.assertEqual(kwargs["url"], "https://api.linkedin.com/rest/posts")
        
        payload = kwargs["json"]
        self.assertEqual(payload["author"], "urn:li:person:abcdef")
        self.assertEqual(payload["commentary"], "Autonomous AI Agent testing #python #ai")
        self.assertEqual(payload["visibility"], "PUBLIC")
        self.assertEqual(payload["lifecycleState"], "PUBLISHED")
        self.assertFalse(payload["isReshareDisabledByAuthor"])
        self.assertEqual(res["id"], "urn:li:share:987654321")

    def test_create_post_with_media_urn(self):
        """Verifies attachment of media URN in /rest/posts content dictionary."""
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.headers = {"x-restli-id": "urn:li:share:555"}
        mock_resp.json.return_value = {}
        self.mock_session.request.return_value = mock_resp

        self.client.create_post(
            text="Post with attached infographic",
            author_urn="urn:li:person:abcdef",
            media_urn="urn:li:image:C4E12345"
        )

        _, kwargs = self.mock_session.request.call_args
        payload = kwargs["json"]
        self.assertIn("content", payload)
        self.assertEqual(payload["content"]["media"]["id"], "urn:li:image:C4E12345")

    def test_initialize_and_upload_image(self):
        """Verifies 2-step media upload protocol (initializeUpload -> binary PUT)."""
        # 1. Mock initializeUpload
        mock_init_resp = MagicMock()
        mock_init_resp.ok = True
        mock_init_resp.json.return_value = {
            "value": {
                "uploadUrl": "https://media.licdn.com/upload/target123",
                "image": "urn:li:image:C4E999"
            }
        }
        self.mock_session.request.return_value = mock_init_resp

        # 2. Mock binary PUT
        mock_put_resp = MagicMock()
        mock_put_resp.ok = True
        self.mock_session.put.return_value = mock_put_resp

        init_res = self.client.initialize_image_upload("urn:li:person:abcdef")
        self.assertEqual(init_res["upload_url"], "https://media.licdn.com/upload/target123")
        self.assertEqual(init_res["image_urn"], "urn:li:image:C4E999")

        success = self.client.upload_image_binary(init_res["upload_url"], b"FAKE_PNG_BYTES", mime_type="image/png")
        self.assertTrue(success)
        self.mock_session.put.assert_called_once_with(
            "https://media.licdn.com/upload/target123",
            data=b"FAKE_PNG_BYTES",
            headers={"Content-Type": "image/png"}
        )

    def test_365_day_token_refresh(self):
        """Verifies refresh token rotation request and vault updates."""
        mock_token_resp = MagicMock()
        mock_token_resp.ok = True
        mock_token_resp.json.return_value = {
            "access_token": "refreshed_access_token_999",
            "refresh_token": "refreshed_refresh_token_888",
            "expires_in": 5184000,
            "refresh_token_expires_in": 31536000
        }
        self.mock_session.post.return_value = mock_token_resp

        with patch.object(LinkedInTokenVault, "save_tokens") as mock_save:
            res = self.client.refresh_access_token()
            self.assertEqual(res["access_token"], "refreshed_access_token_999")
            self.assertEqual(self.client.access_token, "refreshed_access_token_999")
            mock_save.assert_called_once()

    def test_dry_run_preview_guardrail(self):
        """Verifies character limit validation (3,000 max limit)."""
        valid_post = "Short compliant post #tech"
        self.assertTrue(render_post_preview(valid_post, "urn:li:person:123"))

        overflow_post = "X" * 3001
        self.assertFalse(render_post_preview(overflow_post, "urn:li:person:123"))

    def test_comments_and_reply(self):
        """Verifies community management endpoints for fetching and posting replies."""
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"elements": [{"actor": "urn:li:person:user1", "message": {"text": "Great post!"}}]}
        self.mock_session.request.return_value = mock_resp

        comments = self.client.get_comments("urn:li:share:123")
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0]["message"]["text"], "Great post!")

        # Test reply
        mock_reply_resp = MagicMock()
        mock_reply_resp.ok = True
        mock_reply_resp.text = '{"status": "ok"}'
        mock_reply_resp.json.return_value = {"status": "ok"}
        self.mock_session.request.return_value = mock_reply_resp

        reply_res = self.client.reply_comment("urn:li:share:123", "urn:li:organization:456", "Thanks!")
        self.assertEqual(reply_res["status"], "ok")

    def test_mcp_tools_execution(self):
        """Verifies FastMCP tool functions."""
        # 1. linkedin_get_profile tool
        with patch.object(mcp_server.client, "get_profile") as mock_prof:
            mock_prof.return_value = {"name": "Test User", "urn": "urn:li:person:test123"}
            res = mcp_server.linkedin_get_profile()
            data = json.loads(res)
            self.assertEqual(data["name"], "Test User")
            self.assertEqual(data["urn"], "urn:li:person:test123")

        # 2. linkedin_create_post tool
        with patch.object(mcp_server.client, "create_post") as mock_create:
            mock_create.return_value = {"id": "urn:li:share:mcp123", "urn": "urn:li:share:mcp123"}
            res = mcp_server.linkedin_create_post(text="Hello from MCP", author_urn="urn:li:person:test123")
            data = json.loads(res)
            self.assertEqual(data["status"], "success")
            self.assertEqual(data["post"]["id"], "urn:li:share:mcp123")

        # 3. linkedin_create_post character limit check in MCP tool
        res_limit = mcp_server.linkedin_create_post(text="Y" * 3001, author_urn="urn:li:person:test123")
        data_limit = json.loads(res_limit)
        self.assertIn("error", data_limit)

    def test_automatic_401_retry_refresh(self):
        """Verifies that catching a 401 triggers automatic token refresh and single retry."""
        mock_401_resp = MagicMock()
        mock_401_resp.ok = False
        mock_401_resp.status_code = 401
        mock_401_resp.text = "Unauthorized"

        mock_200_resp = MagicMock()
        mock_200_resp.ok = True
        mock_200_resp.status_code = 200
        mock_200_resp.json.return_value = {"sub": "user_retry", "urn": "urn:li:person:user_retry"}

        # First call returns 401, second call returns 200
        self.mock_session.request.side_effect = [mock_401_resp, mock_200_resp]

        with patch.object(self.client, "refresh_access_token") as mock_refresh:
            mock_refresh.return_value = {"access_token": "refreshed_tok"}
            profile = self.client.get_profile()
            self.assertEqual(profile["urn"], "urn:li:person:user_retry")
            mock_refresh.assert_called_once()
            self.assertEqual(self.mock_session.request.call_count, 2)

    def test_presigned_s3_upload_headers(self):
        """Verifies Authorization header is stripped for pre-signed S3 / external blob URLs."""
        mock_put_resp = MagicMock()
        mock_put_resp.ok = True
        self.mock_session.put.return_value = mock_put_resp

        # Upload to AWS S3 pre-signed URL (should strip Authorization)
        self.client.upload_image_binary("https://media.licdn.com/dms/upload/s3-blob", b"BYTES", mime_type="image/jpeg")
        _, kwargs = self.mock_session.put.call_args
        self.assertNotIn("Authorization", kwargs["headers"])
        self.assertEqual(kwargs["headers"]["Content-Type"], "image/jpeg")

    def test_dynamic_token_reload(self):
        """Verifies client.reload_tokens() updates cached credentials."""
        with patch.object(LinkedInTokenVault, "load_tokens") as mock_load:
            mock_load.return_value = {
                "access_token": "dynamically_loaded_token",
                "refresh_token": "dynamically_loaded_refresh",
                "author_urn": "urn:li:person:dynamic_urn"
            }
            self.client.reload_tokens()
            self.assertEqual(self.client.access_token, "dynamically_loaded_token")
            self.assertEqual(self.client.author_urn, "urn:li:person:dynamic_urn")


if __name__ == "__main__":
    unittest.main()
