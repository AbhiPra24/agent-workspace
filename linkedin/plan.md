# LinkedIn Official API Suite: Architecture & Implementation Plan

## Executive Summary
This document defines the production-grade architecture and implementation blueprint for the **LinkedIn Official API Suite**, comprising:
1. **Core REST Engine & CLI** (`scripts/linkedin_suite.py`)
2. **LinkedIn Model Context Protocol (MCP) Server** (`scripts/linkedin_mcp.py`)
3. **Multi-Agent Skills & Rules** (`skills/linkedin-official-publisher/`, `.agents/skills/...`, `.cursor/rules/...`)
4. **Comprehensive Mocked Test Suite** (`tests/test_linkedin_suite.py`)

---

## 1. Architectural Guardrails & Core Principles

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           5 PILLARS OF COMPLIANCE                           │
├──────────────────────────┬──────────────────────────────────────────────────┤
│ 1. Modern /rest/posts    │ • Zero legacy endpoints (/v2/ugcPosts, /v2/shares)│
│    Only                  │ • Structured URN payloads (urn:li:person:...)    │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ 2. Mandatory Versioning  │ • Globally inject `LinkedIn-Version: 202401`     │
│    Headers               │ • Globally inject `X-Restli-Protocol-Version:2.0`│
├──────────────────────────┼──────────────────────────────────────────────────┤
│ 3. Automated Idempotency │ • Generate unique UUID for every POST request    │
│    Keys                  │ • Append `X-RestLi-Idempotency-Key: <UUID>`      │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ 4. 365-Day Silent Token  │ • 1-click browser OAuth via local callback server│
│    Refresh               │ • Background renewal using cached `refresh_token`│
├──────────────────────────┼──────────────────────────────────────────────────┤
│ 5. Rich Terminal Preview │ • Rich CLI diff with hook analysis & tags        │
│    (Dry-Run Default)     │ • Explicit [y/N] confirmation before live POST   │
└──────────────────────────┴──────────────────────────────────────────────────┘
```

---

## 2. Component Specifications

### Component 1: Core Engine & CLI (`scripts/linkedin_suite.py`)

#### A. Authentication & Token Vault (`LinkedInAuthManager`)
* **Local OAuth Callback Server**: Spawns a temporary lightweight HTTP listener at `http://localhost:8080/callback` when running `python3 scripts/linkedin_suite.py login`.
* **PKCE & State Validation**: Generates cryptographically secure `state` and `code_verifier` / `code_challenge` parameters.
* **Token Storage**: Persists credentials in `~/.config/linkedin-agent/tokens.json` (or `.env`):
  ```json
  {
    "access_token": "AQX...",
    "expires_at": 1729000000,
    "refresh_token": "AQY...",
    "refresh_expires_at": 1760000000,
    "scope": "openid profile email w_member_social",
    "member_urn": "urn:li:person:AbCdEf1234"
  }
  ```
* **Silent Auto-Refresh**: Before every API invocation, checks `expires_at`. If within 24 hours of expiry, uses `grant_type=refresh_token` to rotate `access_token` seamlessly without user interaction for up to 365 days.

#### B. HTTP Client with Global Headers (`LinkedInRestClient`)
* **Base URL**: `https://api.linkedin.com/rest/`
* **Global Request Interceptors**:
  ```python
  headers = {
      "Authorization": f"Bearer {token}",
      "LinkedIn-Version": "202401",
      "X-Restli-Protocol-Version": "2.0.0",
      "Content-Type": "application/json",
  }
  if method.upper() == "POST":
      headers["X-RestLi-Idempotency-Key"] = str(uuid.uuid4())
  ```

#### C. Post Publishing Pipeline (`/rest/posts`)
* **Endpoints Used**:
  - `POST /rest/posts`: Exclusively used for text, URLs, images, carousels, and videos.
* **Payload Structure**:
  ```json
  {
    "author": "urn:li:person:{MEMBER_ID}",
    "commentary": "Post content with #hashtags and mentions...",
    "visibility": "PUBLIC",
    "distribution": {
      "feedDistribution": "MAIN_FEED",
      "targetEntities": [],
      "thirdPartyDistributionChannels": []
    },
    "lifecycleState": "PUBLISHED",
    "isReshareDisabledByAuthor": false
  }
  ```

#### D. Two-Step Media Upload Pipeline
1. **Initialize**: `POST https://api.linkedin.com/rest/images?action=initializeUpload` with `{"initializeUploadRequest": {"owner": "urn:li:person:..."}}`.
2. **Binary PUT**: Upload binary file bytes directly to the returned `uploadUrl`.
3. **Asset Attachment**: Attach the returned image URN `urn:li:image:{id}` into `/rest/posts` content payload.

#### E. Rich Terminal Preview (Dry-Run by Default)
* Built-in `rich` terminal rendering showing:
  - **Hook Structure**: Line 1-2 preview before fold.
  - **Character Count & Limit**: e.g., `842 / 3,000 chars` with color-coded safety margins.
  - **Extracted Hashtags & Mentions**: Highlighting discovered tags.
  - **Target Entity**: Member profile vs Organization Page.
  - **Media Preview**: File path, dimensions, MIME type.
  - **Interactive Confirmation**: Prompts `[y/N]` before making live network calls (bypassed only with explicit `--yes` flag).

---

### Component 2: LinkedIn MCP Server (`scripts/linkedin_mcp.py`)

Native Model Context Protocol server exposing tools to AI assistants:
* `linkedin_get_profile`: Returns user info (`sub`, `name`, `email`, `picture`, `urn`).
* `linkedin_preview_post`: Renders character count, hook score, and formatted preview without publishing.
* `linkedin_create_post`: Publishes text/link/media post with automatic idempotency key.
* `linkedin_upload_image`: Initializes and uploads local image file, returning media URN.
* `linkedin_list_posts`: Lists recent posts authored by the member or company page.
* `linkedin_get_comments`: Fetches comments on a specific post URN.
* `linkedin_reply_comment`: Posts a reply to a specific comment thread.
* `linkedin_delete_post`: Deletes a post authored by the application.

---

### Component 3: Multi-Agent Skills & IDE Rules

1. **`linkedin-official-publisher` Skill**:
   - Location: `.agents/skills/linkedin-official-publisher/SKILL.md` & `skills/linkedin-official-publisher/SKILL.md`
   - Trigger: `/linkedin-publish [topic_or_draft] [--media path] [--target personal|org]`
   - Behavior: Crafts high-engagement copy using proven 2026 hook formulas, runs character limit validation, displays terminal preview, and executes live publish on confirmation.
2. **`linkedin-auth-manager` Skill**:
   - Location: `.agents/skills/linkedin-auth-manager/SKILL.md` & `skills/linkedin-auth-manager/SKILL.md`
   - Trigger: `/linkedin-auth [login|status|refresh|logout]`
   - Behavior: Launches callback server, displays token health, and manages credential storage.
3. **Cursor Rule**:
   - `.cursor/rules/linkedin-official.mdc`
4. **Universal IDE Docs**:
   - Updates to `CLAUDE.md`, `.windsurfrules`, and `.github/copilot-instructions.md`.

---

### Component 4: Test Suite (`tests/test_linkedin_suite.py`)

100% mocked offline unit tests verifying:
- [x] Global headers (`LinkedIn-Version: 202401`, `X-Restli-Protocol-Version: 2.0.0`) injected on all requests.
- [x] Unique `X-RestLi-Idempotency-Key` UUID generated for every `POST` call.
- [x] OAuth PKCE URL construction and token storage/refresh logic.
- [x] `/rest/posts` JSON serialization for text, link, and image posts.
- [x] 2-step media upload request formatting.
- [x] Rich terminal preview formatting and character count logic.
- [x] MCP tool definitions and tool execution handlers.

---

## 3. Implementation Plan & File Checklist

| File | Purpose |
| :--- | :--- |
| [`scripts/linkedin_suite.py`](file:///Users/abhipra/Developer/Github/agent-workspace/scripts/linkedin_suite.py) | Core OAuth, REST client, idempotency, media uploader, and Rich CLI |
| [`scripts/linkedin_mcp.py`](file:///Users/abhipra/Developer/Github/agent-workspace/scripts/linkedin_mcp.py) | FastMCP server implementation exposing LinkedIn tools |
| [`skills/linkedin-official-publisher/SKILL.md`](file:///Users/abhipra/Developer/Github/agent-workspace/skills/linkedin-official-publisher/SKILL.md) | Agent skill for drafting, previewing, and publishing |
| [`skills/linkedin-auth-manager/SKILL.md`](file:///Users/abhipra/Developer/Github/agent-workspace/skills/linkedin-auth-manager/SKILL.md) | Agent skill for token auth & refresh management |
| [`.agents/skills/...`](file:///Users/abhipra/Developer/Github/agent-workspace/.agents/skills/) | Antigravity multi-agent mirrored skills |
| [`.cursor/rules/linkedin-official.mdc`](file:///Users/abhipra/Developer/Github/agent-workspace/.cursor/rules/linkedin-official.mdc) | Cursor IDE rule |
| [`tests/test_linkedin_suite.py`](file:///Users/abhipra/Developer/Github/agent-workspace/tests/test_linkedin_suite.py) | Comprehensive mock-based unit tests |
| [`CLAUDE.md`](file:///Users/abhipra/Developer/Github/agent-workspace/CLAUDE.md) / [`.windsurfrules`](file:///Users/abhipra/Developer/Github/agent-workspace/.windsurfrules) | Documentation and agent instructions |
