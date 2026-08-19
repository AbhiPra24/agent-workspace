---
name: linkedin-company-manager
description: >-
  Monitors LinkedIn Organization Pages, inspects recent company updates, retrieves inbound comment threads,
  and posts official company replies using LinkedIn's Community Management API (/rest/socialActions).
  Trigger with `/linkedin-company [comments|posts|reply] [--urn target_urn]`.
parameters:
  action:
    type: string
    description: Action to perform (posts | comments | reply)
    default: comments
  urn:
    type: string
    description: Target post or comment URN (urn:li:share:... or urn:li:organization:...)
    required: false
  text:
    type: string
    description: Text content for comment reply
    required: false
  count:
    type: integer
    description: Maximum number of items to retrieve
    default: 20
---

# LinkedIn Company Manager Skill

Manages LinkedIn Organization/Company pages and community discussions using official LinkedIn Community Management endpoints (`/rest/socialActions` and `/rest/posts`).

## Capabilities
1. **Activity Monitoring**: Lists recent posts authored by an organization page.
2. **Comment Moderation**: Pulls live comment threads on company posts.
3. **Official Replies**: Crafts and submits official responses as the company or admin actor.

---

## Execution Commands

### 1. Fetch Inbound Comments on a Company Post
```bash
python3 scripts/linkedin_suite.py comments --urn urn:li:share:123456789 --count 20
```

### 2. Monitor Recent Organization Posts
Via MCP server tool `linkedin_list_posts` or Python engine:
```python
from scripts.linkedin_suite import LinkedInClient
client = LinkedInClient()
posts = client.list_posts("urn:li:organization:987654", count=10)
```

### 3. Post an Official Comment Reply
Via MCP server tool `linkedin_reply_comment` or Python engine:
```python
from scripts.linkedin_suite import LinkedInClient
client = LinkedInClient()
client.reply_comment(target_urn="urn:li:share:123456", actor_urn="urn:li:organization:987654", text="Thank you for sharing your feedback!")
```

---

## Required Permissions
- Requires Organization administrator access with scopes `w_organization_social` and `r_organization_social`.
