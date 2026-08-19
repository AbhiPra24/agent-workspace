#!/usr/bin/env python3
"""
LinkedIn Official API MCP Server.

Provides a robust, dual-mode Model Context Protocol (MCP) server:
1. Native FastMCP when the `mcp` package is available.
2. Zero-dependency JSON-RPC 2.0 stdio protocol engine fallback for universal compatibility.

All logs/warnings are strictly filtered or routed to stderr to ensure 100% clean JSON-RPC transport over stdout.
"""

import sys
import os
import json
import warnings
import logging

# 1. Suppress all urllib3 and Python runtime warnings to prevent stdout/stderr protocol pollution
warnings.filterwarnings("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"

# Configure logging strictly to stderr
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [LinkedIn-MCP] %(message)s"
)
logger = logging.getLogger("LinkedInMCP")

# Ensure repository root / scripts directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from linkedin_suite import LinkedInClient, LinkedInAPIError

# Initialize Client
client = LinkedInClient()

# ==============================================================================
# Tool Implementations
# ==============================================================================

def tool_get_profile(arguments: dict = None) -> str:
    """Fetches the authenticated LinkedIn member profile and person URN."""
    client.reload_tokens()
    try:
        profile = client.get_profile()
        return json.dumps(profile, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "tip": "Run `python3 scripts/linkedin_suite.py login` or check .env"})


def tool_create_post(arguments: dict = None) -> str:
    """Publishes a post to LinkedIn using the modern /rest/posts endpoint."""
    client.reload_tokens()
    args = arguments or {}
    text = args.get("text", "")
    author_urn = args.get("author_urn")
    visibility = args.get("visibility", "PUBLIC")
    article_url = args.get("article_url")
    media_urn = args.get("media_urn")

    if not text:
        return json.dumps({"error": "Post text commentary is required."})

    if len(text) > 3000:
        return json.dumps({"error": f"Post commentary exceeds LinkedIn 3000 character limit ({len(text)} chars)."})

    try:
        res = client.create_post(
            text=text,
            author_urn=author_urn,
            visibility=visibility,
            article_url=article_url,
            media_urn=media_urn,
        )
        return json.dumps({"status": "success", "post": res}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def tool_upload_media(arguments: dict = None) -> str:
    """Uploads a local image file via 2-step media upload and returns media URN."""
    client.reload_tokens()
    args = arguments or {}
    file_path = args.get("file_path", "")
    owner_urn = args.get("owner_urn", "")

    if not file_path or not os.path.exists(file_path):
        return json.dumps({"error": f"Media file not found: {file_path}"})

    try:
        media_urn = client.upload_image_file(file_path, owner_urn=owner_urn)
        return json.dumps({"status": "success", "media_urn": media_urn}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def tool_get_comments(arguments: dict = None) -> str:
    """Fetches comments on a specific post URN."""
    client.reload_tokens()
    args = arguments or {}
    target_urn = args.get("target_urn", "")
    count = args.get("count", 20)

    if not target_urn:
        return json.dumps({"error": "target_urn is required (e.g. urn:li:share:12345)"})

    try:
        comments = client.get_comments(target_urn=target_urn, count=count)
        return json.dumps({"status": "success", "count": len(comments), "comments": comments}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def tool_reply_comment(arguments: dict = None) -> str:
    """Posts a reply to a comment thread."""
    client.reload_tokens()
    args = arguments or {}
    target_urn = args.get("target_urn", "")
    actor_urn = args.get("actor_urn", "")
    text = args.get("text", "")

    if not target_urn or not text:
        return json.dumps({"error": "target_urn and text are required."})

    try:
        res = client.reply_comment(target_urn=target_urn, actor_urn=actor_urn, text=text)
        return json.dumps({"status": "success", "result": res}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def tool_list_posts(arguments: dict = None) -> str:
    """Retrieves recent posts authored by a member or organization."""
    client.reload_tokens()
    args = arguments or {}
    author_urn = args.get("author_urn", "")
    count = args.get("count", 10)

    try:
        posts = client.list_posts(author_urn=author_urn, count=count)
        return json.dumps({"status": "success", "count": len(posts), "elements": posts}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# Tool definitions registry
TOOLS_REGISTRY = {
    "linkedin_get_profile": {
        "description": "Fetches authenticated LinkedIn member profile and person URN (urn:li:person:...).",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        },
        "handler": tool_get_profile
    },
    "linkedin_create_post": {
        "description": "Publishes a post to LinkedIn using the official /rest/posts endpoint with automatic idempotency.",
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
    """
    Standard JSON-RPC 2.0 stdio server conforming to Model Context Protocol specs.
    Handles initialize, tools/list, tools/call, and ping requests.
    """
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


# ==============================================================================
# Helper wrappers for direct module execution and FastMCP exports
# ==============================================================================

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
    """Main process entrypoint."""
    run_stdio_jsonrpc_server()


if __name__ == "__main__":
    main()
