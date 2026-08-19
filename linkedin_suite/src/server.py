#!/usr/bin/env python3
"""
LinkedIn Official API FastMCP Server.

Provides a robust Model Context Protocol (MCP) server for AI assistants:
- Pre-flight token validation & self-healing authentication (silent refresh + auto-OAuth browser login)
- Zero-dependency JSON-RPC 2.0 stdio engine for universal compatibility
- All logging and runtime warnings strictly isolated to stderr to ensure 100% clean stdout protocol frames
"""

import sys
import os
import json
import warnings
import logging

# 1. Suppress all library runtime warnings to keep stdio completely clean
warnings.filterwarnings("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"

# 2. Configure logging strictly to stderr
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [LinkedIn-MCP] %(message)s"
)
logger = logging.getLogger("LinkedInMCP")

# Ensure repository root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from scripts.linkedin_suite import LinkedInClient, LinkedInAPIError, execute_oauth_flow
except ImportError:
    from linkedin_suite import LinkedInClient, LinkedInAPIError, execute_oauth_flow

# Initialize Client
client = LinkedInClient()


def ensure_client_authenticated() -> None:
    """Performs pre-flight verification, silent refresh, or auto-OAuth trigger."""
    client.ensure_authenticated(auto_oauth=True)


# ==============================================================================
# Tool Implementations with Self-Healing Auth
# ==============================================================================

def tool_get_profile(arguments: dict = None) -> str:
    """Fetches the authenticated LinkedIn member profile and person URN."""
    try:
        ensure_client_authenticated()
        profile = client.get_profile(auto_auth=False)
        return json.dumps(profile, indent=2)
    except LinkedInAPIError as e:
        return json.dumps({
            "error": "Authentication Error",
            "message": str(e),
            "status_code": e.status_code,
            "action_required": "Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET in .env or run `python3 scripts/linkedin_suite.py login`"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "error": "Failed fetching profile",
            "details": str(e)
        }, indent=2)


def tool_create_post(arguments: dict = None) -> str:
    """Publishes a post to LinkedIn using the modern /rest/posts endpoint."""
    args = arguments or {}
    text = args.get("text", "")
    author_urn = args.get("author_urn")
    visibility = args.get("visibility", "PUBLIC")
    article_url = args.get("article_url")
    media_urn = args.get("media_urn")

    if not text:
        return json.dumps({"error": "Post commentary text is required."})

    if len(text) > 3000:
        return json.dumps({"error": f"Post commentary exceeds LinkedIn 3,000 character limit ({len(text)} chars)."})

    try:
        ensure_client_authenticated()
        res = client.create_post(
            text=text,
            author_urn=author_urn,
            visibility=visibility,
            article_url=article_url,
            media_urn=media_urn,
            auto_auth=False,
        )
        return json.dumps({"status": "success", "post": res}, indent=2)
    except LinkedInAPIError as e:
        return json.dumps({
            "error": "Authentication Error",
            "message": str(e),
            "status_code": e.status_code,
            "action_required": "Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET in .env or run `python3 scripts/linkedin_suite.py login`"
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def tool_upload_media(arguments: dict = None) -> str:
    """Uploads a local image file via 2-step media upload and returns media URN."""
    args = arguments or {}
    file_path = args.get("file_path", "")
    owner_urn = args.get("owner_urn", "")

    if not file_path or not os.path.exists(file_path):
        return json.dumps({"error": f"Media file not found: {file_path}"})

    try:
        ensure_client_authenticated()
        media_urn = client.upload_image_file(file_path, owner_urn=owner_urn, auto_auth=False)
        return json.dumps({"status": "success", "media_urn": media_urn}, indent=2)
    except LinkedInAPIError as e:
        return json.dumps({
            "error": "Authentication Error",
            "message": str(e),
            "status_code": e.status_code,
            "action_required": "Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET in .env or run `python3 scripts/linkedin_suite.py login`"
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def tool_get_comments(arguments: dict = None) -> str:
    """Fetches comments on a specific post URN."""
    args = arguments or {}
    target_urn = args.get("target_urn", "")
    count = args.get("count", 20)

    if not target_urn:
        return json.dumps({"error": "target_urn is required (e.g. urn:li:share:12345)"})

    try:
        ensure_client_authenticated()
        comments = client.get_comments(target_urn=target_urn, count=count, auto_auth=False)
        return json.dumps({"status": "success", "count": len(comments), "comments": comments}, indent=2)
    except LinkedInAPIError as e:
        return json.dumps({
            "error": "Authentication Error",
            "message": str(e),
            "status_code": e.status_code,
            "action_required": "Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET in .env or run `python3 scripts/linkedin_suite.py login`"
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def tool_reply_comment(arguments: dict = None) -> str:
    """Posts a reply to a comment thread."""
    args = arguments or {}
    target_urn = args.get("target_urn", "")
    actor_urn = args.get("actor_urn", "")
    text = args.get("text", "")

    if not target_urn or not text:
        return json.dumps({"error": "target_urn and text are required."})

    try:
        ensure_client_authenticated()
        res = client.reply_comment(target_urn=target_urn, actor_urn=actor_urn, text=text, auto_auth=False)
        return json.dumps({"status": "success", "result": res}, indent=2)
    except LinkedInAPIError as e:
        return json.dumps({
            "error": "Authentication Error",
            "message": str(e),
            "status_code": e.status_code,
            "action_required": "Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET in .env or run `python3 scripts/linkedin_suite.py login`"
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def tool_list_posts(arguments: dict = None) -> str:
    """Retrieves recent posts authored by a member or organization."""
    args = arguments or {}
    author_urn = args.get("author_urn", "")
    count = args.get("count", 10)

    try:
        ensure_client_authenticated()
        posts = client.list_posts(author_urn=author_urn, count=count, auto_auth=False)
        return json.dumps({"status": "success", "count": len(posts), "elements": posts}, indent=2)
    except LinkedInAPIError as e:
        return json.dumps({
            "error": "Authentication Error",
            "message": str(e),
            "status_code": e.status_code,
            "action_required": "Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET in .env or run `python3 scripts/linkedin_suite.py login`"
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# Tool definitions registry
TOOLS_REGISTRY = {
    "linkedin_get_profile": {
        "description": "Fetches authenticated LinkedIn member profile and person URN (urn:li:person:...). Automatically handles authentication.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        },
        "handler": tool_get_profile
    },
    "linkedin_create_post": {
        "description": "Publishes a post to LinkedIn using the official /rest/posts endpoint with automatic idempotency and authentication.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Post commentary content (max 3000 chars, supports #hashtags)"},
                "author_urn": {"type": "string", "description": "Author URN (urn:li:person:... or urn:li:organization:...)"},
                "visibility": {"type": "string", "enum": ["PUBLIC", "CONNECTIONS"], "default": "PUBLIC"},
                "article_url": {"type": "string", "description": "Optional URL link to attach as an article preview"},
                "media_urn": {"type": "string", "description": "Optional media URN (urn:li:image:...) uploaded via linkedin_upload_media"}
            },
            "required": ["text"]
        },
        "handler": tool_create_post
    },
    "linkedin_upload_media": {
        "description": "Uploads a local image file using LinkedIn's 2-step protocol and returns a media URN.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to local image file (.jpg, .png)"},
                "owner_urn": {"type": "string", "description": "Author URN (urn:li:person:... or urn:li:organization:...)"}
            },
            "required": ["file_path", "owner_urn"]
        },
        "handler": tool_upload_media
    },
    "linkedin_get_comments": {
        "description": "Fetches comments on a specific post URN for moderation and community management.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_urn": {"type": "string", "description": "Target post URN (urn:li:share:...)"},
                "count": {"type": "integer", "default": 20, "description": "Number of comments to fetch"}
            },
            "required": ["target_urn"]
        },
        "handler": tool_get_comments
    },
    "linkedin_reply_comment": {
        "description": "Posts an official reply to a comment thread on LinkedIn.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_urn": {"type": "string", "description": "Parent post or comment URN"},
                "actor_urn": {"type": "string", "description": "Author URN replying (person or organization)"},
                "text": {"type": "string", "description": "Reply text"}
            },
            "required": ["target_urn", "text"]
        },
        "handler": tool_reply_comment
    },
    "linkedin_list_posts": {
        "description": "Retrieves recent posts authored by a member or organization.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "author_urn": {"type": "string", "description": "Author URN (urn:li:person:... or urn:li:organization:...)"},
                "count": {"type": "integer", "default": 10, "description": "Number of posts to retrieve"}
            },
            "required": ["author_urn"]
        },
        "handler": tool_list_posts
    }
}


# ==============================================================================
# Native JSON-RPC 2.0 Stdio MCP Protocol Engine
# ==============================================================================

def run_stdio_jsonrpc_server():
    """Standard JSON-RPC 2.0 stdio server conforming to Model Context Protocol specs."""
    logger.info("LinkedIn Official MCP Stdio Server running...")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except Exception as e:
            logger.error(f"Invalid JSON input: {e}")
            continue

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        # Handle notifications (no id)
        if req_id is None:
            if method == "notifications/initialized":
                logger.info("MCP Client connection initialized.")
            continue

        # 1. Initialize Handshake
        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {
                            "listChanged": False
                        }
                    },
                    "serverInfo": {
                        "name": "linkedin-official",
                        "version": "0.1.0"
                    }
                }
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        # 2. Ping
        elif method == "ping":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {}
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        # 3. List Tools
        elif method == "tools/list":
            tools_list = []
            for name, meta in TOOLS_REGISTRY.items():
                tools_list.append({
                    "name": name,
                    "description": meta["description"],
                    "inputSchema": meta["inputSchema"]
                })

            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": tools_list
                }
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        # 4. Call Tool
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name in TOOLS_REGISTRY:
                try:
                    result_text = TOOLS_REGISTRY[tool_name]["handler"](arguments)
                    resp = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": result_text
                                }
                            ],
                            "isError": False
                        }
                    }
                except Exception as e:
                    logger.error(f"Error executing tool {tool_name}: {e}")
                    resp = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps({"error": str(e)})
                                }
                            ],
                            "isError": True
                        }
                    }
            else:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool '{tool_name}' not found."
                    }
                }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        # 5. Unsupported method
        else:
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not supported."
                }
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


def linkedin_get_profile() -> str:
    return tool_get_profile()

def linkedin_create_post(text: str, author_urn: str = None, visibility: str = "PUBLIC", article_url: str = None, media_urn: str = None) -> str:
    return tool_create_post({"text": text, "author_urn": author_urn, "visibility": visibility, "article_url": article_url, "media_urn": media_urn})

def linkedin_upload_media(file_path: str, owner_urn: str) -> str:
    return tool_upload_media({"file_path": file_path, "owner_urn": owner_urn})

def linkedin_get_comments(target_urn: str, count: int = 20) -> str:
    return tool_get_comments({"target_urn": target_urn, "count": count})

def linkedin_reply_comment(target_urn: str, actor_urn: str, text: str) -> str:
    return tool_reply_comment({"target_urn": target_urn, "actor_urn": actor_urn, "text": text})

def linkedin_list_posts(author_urn: str, count: int = 10) -> str:
    return tool_list_posts({"author_urn": author_urn, "count": count})


def main():
    run_stdio_jsonrpc_server()


if __name__ == "__main__":
    main()
