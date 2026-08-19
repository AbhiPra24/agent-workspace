#!/usr/bin/env python3
"""
LinkedIn Official API Suite - Core REST Engine & CLI Utility.

Features:
- Mandatory API versioning headers: `LinkedIn-Version: 202401`, `X-Restli-Protocol-Version: 2.0.0`
- Automatic UUID `X-RestLi-Idempotency-Key` headers on all POST mutations
- Modern `/rest/posts` distribution and 2-step `/rest/images` upload pipeline
- Automatic 401 Unauthorized silent token refresh & retry interceptor
- Pre-signed S3 upload header stripping (prevents signature mismatch)
- Dynamic OAuth port conflict resolution (ports 8080-8089)
- 365-day silent token refresh & local OAuth 2.0 callback listener
- Interactive Rich dry-run terminal previews with character count guardrails
"""

import os
import sys
import re
import json
import time
import uuid
import socket
import logging
import warnings
import argparse

# Suppress all library runtime warnings (e.g. urllib3 LibreSSL warnings)
warnings.filterwarnings("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"
import http.server
import socketserver
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Optional, Dict, Any, List
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LinkedInSuite")

# Rich Terminal UI with fallback
try:
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Confirm
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console = None


class LinkedInAPIError(Exception):
    """Custom exception for LinkedIn official API errors."""
    def __init__(self, status_code: int, message: str, response_body: Optional[str] = None):
        self.status_code = status_code
        self.message = message
        self.response_body = response_body
        super().__init__(f"LinkedIn API Error ({status_code}): {message}")


# ==============================================================================
# Token Vault & Credentials Manager (365-Day Refresh Strategy)
# ==============================================================================

class LinkedInTokenVault:
    """Manages token persistence and automated 365-day background token rotation."""

    CONFIG_DIR = Path.home() / ".config" / "linkedin-agent"
    TOKEN_FILE = CONFIG_DIR / "tokens.json"

    @classmethod
    def load_tokens(cls) -> Dict[str, Any]:
        """Loads stored credentials from config directory or environment variables."""
        tokens = {
            "access_token": os.getenv("LINKEDIN_ACCESS_TOKEN", ""),
            "refresh_token": os.getenv("LINKEDIN_REFRESH_TOKEN", ""),
            "client_id": os.getenv("LINKEDIN_CLIENT_ID", ""),
            "client_secret": os.getenv("LINKEDIN_CLIENT_SECRET", ""),
            "author_urn": os.getenv("LINKEDIN_AUTHOR_URN", ""),
            "expires_at": 0,
            "refresh_expires_at": 0,
        }

        if cls.TOKEN_FILE.exists():
            try:
                with open(cls.TOKEN_FILE, "r") as f:
                    cached = json.load(f)
                    for k, v in cached.items():
                        if v and not tokens.get(k):
                            tokens[k] = v
            except Exception as e:
                logger.warning(f"Could not load cached tokens: {e}")

        return tokens

    @classmethod
    def save_tokens(cls, data: Dict[str, Any]):
        """Persists tokens securely in local user directory."""
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        current = cls.load_tokens()
        current.update(data)
        with open(cls.TOKEN_FILE, "w") as f:
            json.dump(current, f, indent=2)
        logger.info(f"Tokens saved to {cls.TOKEN_FILE}")


# ==============================================================================
# Official LinkedIn REST Client Engine
# ==============================================================================

class LinkedInClient:
    """
    Robust, compliant REST client for official LinkedIn APIs.
    """

    BASE_REST_URL = "https://api.linkedin.com/rest"
    BASE_OIDC_URL = "https://api.linkedin.com/v2"
    OAUTH_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    DEFAULT_API_VERSION = "202401"

    def __init__(
        self,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        api_version: Optional[str] = None,
        session: Optional[requests.Session] = None,
    ):
        vault = LinkedInTokenVault.load_tokens()
        self.access_token = access_token or vault.get("access_token", "")
        self.refresh_token = refresh_token or vault.get("refresh_token", "")
        self.client_id = client_id or vault.get("client_id", "")
        self.client_secret = client_secret or vault.get("client_secret", "")
        self.author_urn = vault.get("author_urn", "")
        self.api_version = api_version or os.getenv("LINKEDIN_API_VERSION", self.DEFAULT_API_VERSION)
        self.session = session or requests.Session()

    def reload_tokens(self):
        """Dynamically reloads latest tokens from vault (for long-running processes like MCP servers)."""
        vault = LinkedInTokenVault.load_tokens()
        if vault.get("access_token"):
            self.access_token = vault["access_token"]
        if vault.get("refresh_token"):
            self.refresh_token = vault["refresh_token"]
        if vault.get("client_id"):
            self.client_id = vault["client_id"]
        if vault.get("client_secret"):
            self.client_secret = vault["client_secret"]
        if vault.get("author_urn"):
            self.author_urn = vault["author_urn"]

    def _get_headers(self, method: str = "GET", extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Constructs mandatory headers with versioning and idempotency keys."""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "LinkedIn-Version": self.api_version,
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

        # Idempotency key for POST mutations
        if method.upper() == "POST":
            headers["X-RestLi-Idempotency-Key"] = str(uuid.uuid4())

        if extra_headers:
            headers.update(extra_headers)

        return headers

    def _request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_on_401: bool = True,
    ) -> requests.Response:
        """Executes HTTP request with global versioning, auto 401 retry, and error handling."""
        req_headers = self._get_headers(method=method, extra_headers=headers)
        
        response = self.session.request(
            method=method,
            url=url,
            params=params,
            json=json_data,
            data=data,
            headers=req_headers,
        )

        # Automatic 401 Silent Token Refresh Interceptor
        if response.status_code == 401 and retry_on_401 and self.refresh_token:
            logger.warning("Received 401 Unauthorized. Attempting automatic silent token refresh...")
            try:
                self.refresh_access_token()
                return self._request(
                    method=method,
                    url=url,
                    params=params,
                    json_data=json_data,
                    data=data,
                    headers=headers,
                    retry_on_401=False,  # Single retry guard
                )
            except Exception as e:
                logger.error(f"Automatic token refresh on 401 failed: {e}")

        if not response.ok:
            error_msg = f"HTTP {response.status_code} - {response.reason}"
            try:
                err_json = response.json()
                error_msg += f": {err_json.get('message', response.text)}"
            except Exception:
                error_msg += f": {response.text}"
            
            logger.error(f"LinkedIn request failed ({response.status_code}): {error_msg}")
            raise LinkedInAPIError(status_code=response.status_code, message=error_msg, response_body=response.text)

        return response

    # --------------------------------------------------------------------------
    # Profile & Identity (/v2/userinfo)
    # --------------------------------------------------------------------------

    def get_profile(self) -> Dict[str, Any]:
        """Fetches the authenticated member profile and person URN."""
        url = f"{self.BASE_OIDC_URL}/userinfo"
        resp = self._request("GET", url)
        data = resp.json()
        sub_id = data.get("sub")
        if sub_id and not data.get("urn"):
            data["urn"] = f"urn:li:person:{sub_id}"
        return data

    # --------------------------------------------------------------------------
    # Post Publishing (/rest/posts)
    # --------------------------------------------------------------------------

    def create_post(
        self,
        text: str,
        author_urn: Optional[str] = None,
        visibility: str = "PUBLIC",
        article_url: Optional[str] = None,
        article_title: Optional[str] = None,
        media_urn: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Publishes a post using the modern `/rest/posts` API.
        """
        target_author = author_urn or self.author_urn
        if not target_author:
            # Attempt to resolve from userinfo
            try:
                prof = self.get_profile()
                target_author = prof.get("urn", "")
            except Exception:
                pass

        if not target_author:
            raise ValueError("Author URN is required. Provide `author_urn` or set LINKEDIN_AUTHOR_URN.")

        url = f"{self.BASE_REST_URL}/posts"
        payload: Dict[str, Any] = {
            "author": target_author,
            "commentary": text,
            "visibility": visibility.upper(),
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False if visibility.upper() == "PUBLIC" else True,
        }

        if article_url:
            payload["content"] = {
                "article": {
                    "source": article_url,
                    "title": article_title or article_url,
                }
            }
        elif media_urn:
            payload["content"] = {
                "media": {
                    "id": media_urn
                }
            }

        resp = self._request("POST", url, json_data=payload)
        post_urn = resp.headers.get("x-restli-id") or resp.headers.get("x-linkedin-id")
        
        try:
            res_json = resp.json()
        except Exception:
            res_json = {}

        if post_urn and "id" not in res_json:
            res_json["id"] = post_urn
            res_json["urn"] = post_urn if post_urn.startswith("urn:li:") else f"urn:li:share:{post_urn}"

        return res_json

    # --------------------------------------------------------------------------
    # Two-Step Media Upload (/rest/images)
    # --------------------------------------------------------------------------

    def initialize_image_upload(self, owner_urn: str) -> Dict[str, str]:
        """Step 1: Initializes image asset creation to obtain upload URL and URN."""
        url = f"{self.BASE_REST_URL}/images?action=initializeUpload"
        payload = {
            "initializeUploadRequest": {
                "owner": owner_urn
            }
        }
        resp = self._request("POST", url, json_data=payload)
        val = resp.json().get("value", {})
        return {
            "upload_url": val.get("uploadUrl", ""),
            "image_urn": val.get("image", ""),
        }

    def upload_image_binary(self, upload_url: str, image_bytes: bytes, mime_type: str = "image/jpeg") -> bool:
        """
        Step 2: PUTs raw binary image data to uploadUrl.
        Strips Authorization headers if the target is a pre-signed S3/blob URL to prevent 400 signature errors.
        """
        headers = {"Content-Type": mime_type}
        # Only attach Authorization if URL is directly on api.linkedin.com (not an external S3/CDN pre-signed URL)
        if "api.linkedin.com" in upload_url:
            headers["Authorization"] = f"Bearer {self.access_token}"

        resp = self.session.put(upload_url, data=image_bytes, headers=headers)
        if not resp.ok:
            raise LinkedInAPIError(resp.status_code, f"Failed uploading image bytes: {resp.text}")
        return True

    def upload_image_file(self, file_path: str, owner_urn: str) -> str:
        """Helper to upload local image file and return LinkedIn media URN."""
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"Media file not found: {file_path}")

        init_data = self.initialize_image_upload(owner_urn)
        mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
        
        with open(p, "rb") as f:
            self.upload_image_binary(init_data["upload_url"], f.read(), mime_type=mime)

        return init_data["image_urn"]

    # --------------------------------------------------------------------------
    # Activity & Community Management (/rest/socialActions)
    # --------------------------------------------------------------------------

    def list_posts(self, author_urn: str, count: int = 10) -> List[Dict[str, Any]]:
        """Retrieves recent posts authored by a member or company page."""
        url = f"{self.BASE_REST_URL}/posts"
        params = {"author": author_urn, "q": "author", "count": count}
        resp = self._request("GET", url, params=params)
        return resp.json().get("elements", [])

    def get_comments(self, target_urn: str, count: int = 20) -> List[Dict[str, Any]]:
        """Fetches comment threads on a specific post or content item."""
        url = f"{self.BASE_REST_URL}/socialActions/{target_urn}/comments"
        params = {"count": count}
        resp = self._request("GET", url, params=params)
        return resp.json().get("elements", [])

    def reply_comment(self, target_urn: str, actor_urn: str, text: str) -> Dict[str, Any]:
        """Posts an official reply to a comment thread."""
        url = f"{self.BASE_REST_URL}/socialActions/{target_urn}/comments"
        payload = {"actor": actor_urn, "message": {"text": text}}
        resp = self._request("POST", url, json_data=payload)
        return resp.json() if resp.text else {"status": "success"}

    # --------------------------------------------------------------------------
    # 365-Day Silent Token Rotation Strategy
    # --------------------------------------------------------------------------

    def refresh_access_token(self) -> Dict[str, Any]:
        """Renews 60-day access token using the cached 365-day refresh token."""
        if not self.refresh_token:
            raise ValueError("No refresh token available. Run `python3 scripts/linkedin_suite.py login` first.")
        if not self.client_id or not self.client_secret:
            raise ValueError("Client ID and Client Secret are required for token rotation.")

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        logger.info("Executing 365-day silent token refresh...")
        resp = self.session.post(self.OAUTH_TOKEN_URL, data=payload, headers=headers)
        if not resp.ok:
            raise LinkedInAPIError(resp.status_code, f"Token refresh failed: {resp.text}")

        token_data = resp.json()
        new_token = token_data.get("access_token", "")
        self.access_token = new_token
        
        save_payload = {
            "access_token": new_token,
            "expires_at": int(time.time()) + token_data.get("expires_in", 5184000),
        }
        if token_data.get("refresh_token"):
            self.refresh_token = token_data["refresh_token"]
            save_payload["refresh_token"] = token_data["refresh_token"]
            save_payload["refresh_expires_at"] = int(time.time()) + token_data.get("refresh_token_expires_in", 31536000)

        LinkedInTokenVault.save_tokens(save_payload)
        logger.info("Access token renewed and vault updated.")
        return token_data


# ==============================================================================
# OAuth 2.0 Local Callback Server with Port Conflict Resolution
# ==============================================================================

class OAuthCallbackHandler(http.server.SimpleHTTPRequestHandler):
    auth_code = None
    state = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            OAuthCallbackHandler.auth_code = params["code"][0]
            OAuthCallbackHandler.state = params.get("state", [""])[0]

            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
                <!DOCTYPE html>
                <html>
                <head><title>Authentication Complete</title></head>
                <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; padding: 60px;">
                    <h2 style="color: #0a66c2;">LinkedIn Authentication Successful!</h2>
                    <p style="color: #555;">Authorization code captured. You may now close this browser window and return to your terminal.</p>
                </body>
                </html>
            """)
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Authentication cancelled or missing code parameter.")

    def log_message(self, format, *args):
        pass


def find_available_port(start_port: int = 8080, max_attempts: int = 10) -> int:
    """Finds an available local port, avoiding port collision errors."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("localhost", port))
                return port
            except OSError:
                continue
    return start_port


def execute_oauth_flow(client_id: str, client_secret: str, preferred_port: int = 8080):
    """Launches local OAuth listener, handles port conflicts, captures code, and exchanges tokens."""
    port = find_available_port(start_port=preferred_port)
    redirect_uri = f"http://localhost:{port}/callback"
    scopes = "openid profile email w_member_social"
    state = f"linkedin_{uuid.uuid4().hex[:12]}"
    
    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization?"
        f"response_type=code&"
        f"client_id={client_id}&"
        f"redirect_uri={urllib.parse.quote(redirect_uri)}&"
        f"state={state}&"
        f"scope={urllib.parse.quote(scopes)}"
    )

    if HAS_RICH and console:
        console.print(Panel(
            f"[bold green]Starting OAuth 2.0 Local Listener on {redirect_uri}...[/bold green]\n"
            f"Opening default browser for 1-click LinkedIn Authorization.\n\n"
            f"[dim]If browser does not open automatically, visit:[/dim]\n[link={auth_url}]{auth_url}[/link]",
            title="🔐 LinkedIn Authentication",
            border_style="green"
        ))
    else:
        print(f"Starting OAuth listener on {redirect_uri}...")
        print(f"Authorize at: {auth_url}")

    webbrowser.open(auth_url)

    try:
        with socketserver.TCPServer(("localhost", port), OAuthCallbackHandler) as httpd:
            httpd.handle_request()
    except OSError as e:
        logger.error(f"Failed binding port {port}: {e}")
        sys.exit(1)

    code = OAuthCallbackHandler.auth_code
    if not code:
        if HAS_RICH and console:
            console.print("[bold red]Failed to capture authorization code.[/bold red]")
        else:
            print("Failed to capture authorization code.")
        sys.exit(1)

    logger.info("Exchanging code for tokens...")
    resp = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        }
    )

    if resp.ok:
        data = resp.json()
        token = data.get("access_token")
        refresh = data.get("refresh_token", "")
        expires_in = data.get("expires_in", 5184000)

        # Retrieve profile URN
        temp_client = LinkedInClient(access_token=token)
        author_urn = ""
        try:
            prof = temp_client.get_profile()
            author_urn = prof.get("urn", "")
        except Exception:
            pass

        LinkedInTokenVault.save_tokens({
            "access_token": token,
            "refresh_token": refresh,
            "client_id": client_id,
            "client_secret": client_secret,
            "author_urn": author_urn,
            "expires_at": int(time.time()) + expires_in,
            "refresh_expires_at": int(time.time()) + data.get("refresh_token_expires_in", 31536000),
        })

        if HAS_RICH and console:
            console.print(Panel(
                f"[bold green]✔ Authentication Complete & Vault Updated![/bold green]\n\n"
                f"[dim]Access Token:[/dim] [cyan]{token[:15]}...{token[-6:]}[/cyan] (Valid for {expires_in // 86400} days)\n"
                f"[dim]Refresh Token:[/dim] [magenta]{refresh[:15] if refresh else 'N/A'}...[/magenta] (Valid for 365 days)\n"
                f"[dim]Author URN:[/dim] [yellow]{author_urn or 'Not resolved'}[/yellow]\n\n"
                f"Saved to: [bold]{LinkedInTokenVault.TOKEN_FILE}[/bold]",
                title="🎉 OAuth Success",
                border_style="green"
            ))
        else:
            print(f"Authenticated successfully! Author URN: {author_urn}")
    else:
        logger.error(f"Token exchange failed: {resp.text}")


# ==============================================================================
# Rich Terminal Dry-Run UI & Guardrails
# ==============================================================================

def render_post_preview(
    text: str,
    author_urn: str,
    visibility: str = "PUBLIC",
    article_url: Optional[str] = None,
    media_path: Optional[str] = None,
) -> bool:
    """Renders visual post diff, calculates character constraints, and checks limits."""
    char_count = len(text)
    max_chars = 3000
    hashtags = re.findall(r'#\w+', text)
    lines = [l for l in text.splitlines() if l.strip()]
    hook = lines[0] if lines else ""

    if HAS_RICH and console:
        if char_count > max_chars:
            count_style = "bold red"
            count_status = f"[bold red]❌ EXCEEDS LIMIT by {char_count - max_chars} chars[/bold red]"
        elif char_count >= 2500:
            count_style = "bold yellow"
            count_status = "[yellow]⚠️ Approaching 3000 limit[/yellow]"
        else:
            count_style = "bold green"
            count_status = "[green]✔ Optimal Length[/green]"

        meta_table = Table(show_header=False, box=None, padding=(0, 1))
        meta_table.add_row("[dim]Target Author:[/dim]", f"[cyan]{author_urn}[/cyan]")
        meta_table.add_row("[dim]Visibility:[/dim]", f"[bold]{visibility}[/bold]")
        meta_table.add_row("[dim]Character Count:[/dim]", f"[{count_style}]{char_count}[/{count_style}] / {max_chars} {count_status}")
        if hashtags:
            meta_table.add_row("[dim]Hashtags:[/dim]", f"[magenta]{', '.join(hashtags)}[/magenta]")
        if article_url:
            meta_table.add_row("[dim]Article Link:[/dim]", f"[link={article_url}]{article_url}[/link]")
        if media_path:
            meta_table.add_row("[dim]Attached Media:[/dim]", f"[yellow]{media_path}[/yellow]")

        console.print(Panel(
            Group(
                f"[bold underline]Hook (Before The Fold):[/bold underline]\n[italic]{hook}[/italic]\n\n"
                f"[bold underline]Post Commentary:[/bold underline]\n{text}\n\n"
                f"────────────────────────────────────────────────────────────",
                meta_table
            ),
            title="🔍 LinkedIn Post Dry-Run Preview",
            border_style="cyan",
            padding=(1, 2)
        ))
    else:
        print("\n=== LinkedIn Post Dry-Run Preview ===")
        print(f"Author: {author_urn} | Visibility: {visibility}")
        print(f"Length: {char_count}/{max_chars} chars")
        if hashtags:
            print(f"Hashtags: {', '.join(hashtags)}")
        print("\nContent:\n" + text)
        print("=====================================\n")

    if char_count > max_chars:
        if HAS_RICH and console:
            console.print("[bold red]Publish blocked: Character count exceeds 3,000 limit.[/bold red]")
        else:
            print("Publish blocked: Exceeds 3,000 characters.")
        return False

    return True


# ==============================================================================
# CLI Commands
# ==============================================================================

def cmd_publish(args, client: LinkedInClient):
    text = args.text
    if not text and args.file:
        p = Path(args.file)
        if p.exists():
            text = p.read_text(encoding="utf-8")
        else:
            logger.error(f"File not found: {args.file}")
            sys.exit(1)

    if not text:
        logger.error("Provide post commentary via --text or --file.")
        sys.exit(1)

    author_urn = args.author or client.author_urn
    if not author_urn:
        try:
            prof = client.get_profile()
            author_urn = prof.get("urn", "")
        except Exception:
            pass

    if not author_urn:
        author_urn = "urn:li:person:YOUR_URN"

    # Validate media file if passed
    if args.media and not Path(args.media).exists():
        logger.error(f"Media file not found: {args.media}")
        sys.exit(1)

    # Dry-Run Preview
    valid = render_post_preview(
        text=text,
        author_urn=author_urn,
        visibility=args.visibility,
        article_url=args.link,
        media_path=args.media,
    )
    if not valid:
        sys.exit(1)

    # Confirmation Prompt Guardrail
    if not args.yes:
        if HAS_RICH and console:
            confirmed = Confirm.ask("🚀 [bold yellow]Publish this post to live LinkedIn feed?[/bold yellow]", default=False)
        else:
            choice = input("Publish this post to live LinkedIn feed? [y/N]: ").strip().lower()
            confirmed = choice in ["y", "yes"]

        if not confirmed:
            if HAS_RICH and console:
                console.print("[dim]Action cancelled by user. No live call made.[/dim]")
            else:
                print("Action cancelled.")
            return

    # Execute Live Publish
    try:
        media_urn = None
        if args.media:
            if HAS_RICH and console:
                console.print("[cyan]Executing 2-step media upload...[/cyan]")
            media_urn = client.upload_image_file(args.media, owner_urn=author_urn)

        if HAS_RICH and console:
            console.print("[bold green]Executing POST /rest/posts with idempotency key...[/bold green]")

        result = client.create_post(
            text=text,
            author_urn=author_urn,
            visibility=args.visibility,
            article_url=args.link,
            media_urn=media_urn,
        )

        post_urn = result.get("urn", result.get("id", "Published"))
        if HAS_RICH and console:
            console.print(Panel(
                f"[bold green]✔ Post published successfully![/bold green]\n\n"
                f"[dim]Post URN:[/dim] [cyan]{post_urn}[/cyan]",
                title="🎉 Live Publication Confirmed",
                border_style="green"
            ))
        else:
            print(f"✔ Post published successfully: {post_urn}")
    except Exception as e:
        logger.error(f"Publication failed: {e}")
        sys.exit(1)


def cmd_profile(args, client: LinkedInClient):
    try:
        data = client.get_profile()
        if HAS_RICH and console:
            table = Table(title="👤 Authenticated LinkedIn Profile", header_style="bold magenta")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            table.add_row("Name", data.get("name", "N/A"))
            table.add_row("Email", data.get("email", "N/A"))
            table.add_row("Member URN", data.get("urn", data.get("sub", "N/A")))
            table.add_row("Picture", (data.get("picture", "N/A")[:50] + "...") if data.get("picture") else "None")
            console.print(table)
        else:
            print("Profile:", json.dumps(data, indent=2))
    except Exception as e:
        logger.error(f"Failed fetching profile: {e}")


def cmd_comments(args, client: LinkedInClient):
    try:
        comments = client.get_comments(target_urn=args.urn, count=args.count)
        if HAS_RICH and console:
            table = Table(title=f"💬 Comments on {args.urn}", header_style="bold cyan")
            table.add_column("Actor URN", style="yellow")
            table.add_column("Comment Text", style="white")
            for c in comments:
                actor = c.get("actor", "Unknown")
                txt = c.get("message", {}).get("text", "")
                table.add_row(actor, txt)
            console.print(table)
        else:
            print(f"Comments on {args.urn}:", json.dumps(comments, indent=2))
    except Exception as e:
        logger.error(f"Failed fetching comments: {e}")


def main():
    parser = argparse.ArgumentParser(description="LinkedIn Official API Suite CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Publish
    pub_p = subparsers.add_parser("publish", help="Draft, preview, and publish a post")
    pub_p.add_argument("-t", "--text", type=str, help="Post content body")
    pub_p.add_argument("-f", "--file", type=str, help="File path containing post content")
    pub_p.add_argument("-a", "--author", type=str, help="Author URN (urn:li:person:... or urn:li:organization:...)")
    pub_p.add_argument("-v", "--visibility", type=str, default="PUBLIC", choices=["PUBLIC", "CONNECTIONS"], help="Visibility scope")
    pub_p.add_argument("-l", "--link", type=str, help="Article URL attachment")
    pub_p.add_argument("-m", "--media", type=str, help="Image file path attachment")
    pub_p.add_argument("-y", "--yes", action="store_true", help="Bypass confirmation prompt")

    # Profile
    subparsers.add_parser("profile", help="Display authenticated profile info")

    # Refresh
    subparsers.add_parser("refresh", help="Rotate access token using 365-day refresh token")

    # Comments
    comm_p = subparsers.add_parser("comments", help="Fetch comments on a post URN")
    comm_p.add_argument("--urn", type=str, required=True, help="Post URN (e.g. urn:li:share:123)")
    comm_p.add_argument("--count", type=int, default=20, help="Number of comments to fetch")

    # Login
    login_p = subparsers.add_parser("login", help="Authenticate with LinkedIn via local OAuth listener")
    login_p.add_argument("--client-id", type=str, default=os.getenv("LINKEDIN_CLIENT_ID", ""))
    login_p.add_argument("--client-secret", type=str, default=os.getenv("LINKEDIN_CLIENT_SECRET", ""))
    login_p.add_argument("--port", type=int, default=8080, help="Preferred callback port (default: 8080)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "login":
        cid = args.client_id or os.getenv("LINKEDIN_CLIENT_ID", "")
        sec = args.client_secret or os.getenv("LINKEDIN_CLIENT_SECRET", "")
        if not cid or not sec:
            logger.error("LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET are required.")
            sys.exit(1)
        execute_oauth_flow(cid, sec, preferred_port=args.port)
        return

    client = LinkedInClient()

    if args.command == "publish":
        cmd_publish(args, client)
    elif args.command == "profile":
        cmd_profile(args, client)
    elif args.command == "refresh":
        client.refresh_access_token()
    elif args.command == "comments":
        cmd_comments(args, client)


if __name__ == "__main__":
    main()
