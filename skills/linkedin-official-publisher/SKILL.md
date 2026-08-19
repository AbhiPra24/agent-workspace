---
name: linkedin-official-publisher
description: >-
  Drafts, formats, and publishes high-impact posts to LinkedIn using the official REST API (/rest/posts)
  with mandatory versioning headers, automatic UUID idempotency keys, and interactive Rich terminal previews
  with dry-run confirmation before live transmission.
  Trigger with `/linkedin-publish [topic_or_draft] [--media path] [--link url]`.
parameters:
  text:
    type: string
    description: Post commentary body text or topic to draft
    required: false
  file:
    type: string
    description: Path to local text/markdown file containing post content
    required: false
  media:
    type: string
    description: Path to local image file to attach via 2-step upload
    required: false
  link:
    type: string
    description: Web URL to attach as an article preview
    required: false
  visibility:
    type: string
    description: Post visibility tier (PUBLIC | CONNECTIONS)
    default: PUBLIC
  yes:
    type: boolean
    description: Bypass interactive [y/N] dry-run confirmation prompt
    default: false
---

# LinkedIn Official Publisher Skill

Executes 100% compliant post publishing via LinkedIn's official `/rest/posts` API with built-in character limit validation, visual previews, and idempotency protection.

## Core Architectural Guardrails
1. **Modern Endpoints Exclusively**: Targets `POST /rest/posts` (never deprecated `/v2/ugcPosts` or `/v2/shares`).
2. **Mandatory Versioning Headers**: Globally injects `LinkedIn-Version: 202401` and `X-Restli-Protocol-Version: 2.0.0`.
3. **Idempotency Protection**: Injects a cryptographically unique UUID into `X-RestLi-Idempotency-Key` on every POST to prevent accidental duplicates.
4. **2-Step Media Upload**: Executes `initializeUpload` -> binary `PUT` for images before attaching to posts.
5. **Dry-Run Default**: Prints a Rich console diff showing character counts, hook structure, and parsed hashtags, requiring `[y/N]` confirmation before live dispatch.

---

## Execution Commands

### 1. Draft & Preview Post with Dry-Run Guardrail
```bash
python3 scripts/linkedin_suite.py publish --text "Exploring new AI agent architectures with official LinkedIn APIs #ai #python"
```

### 2. Publish from Markdown Draft File
```bash
python3 scripts/linkedin_suite.py publish --file path/to/draft.md
```

### 3. Publish with Attached Image
```bash
python3 scripts/linkedin_suite.py publish --text "Architectural blueprint" --media architecture.png
```

### 4. Check Authenticated Identity & Member URN
```bash
python3 scripts/linkedin_suite.py profile
```

### 5. Rotate 365-Day Refresh Token
```bash
python3 scripts/linkedin_suite.py refresh
```

---

## Quality Checklist Before Publishing
- [x] Hook line crafted before the fold (line 1-2).
- [x] Character count <= 3,000 characters.
- [x] Clean spacing with no wall-of-text formatting.
- [x] Verified Member or Organization URN target.
- [x] Reviewed in terminal dry-run preview before confirming `y`.
