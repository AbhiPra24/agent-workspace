---
name: job-matcher
description: >-
  Extracts, evaluates, and ranks job postings against candidate resumes using an
  intelligent Hybrid Scrape & Cache layer (SQLite + BeautifulSoup + Firecrawl MCP fallback),
  finds active hiring managers & technical recruiters, and strictly verifies email deliverability
  (DNS/MX validation & anti-bounce catch-all guardrails).
  Trigger with `/jobmatch [resume_path] [optional_keywords]` or `/jobhunt [resume_path]`.
parameters:
  resume:
    type: string
    description: Path to candidate resume file (.pdf, .txt, .md)
    required: true
  keywords:
    type: string
    description: Filter keywords (role, technology, location)
    required: false
  limit:
    type: integer
    description: Maximum job results to evaluate
    default: 5
---

# Job Matcher Skill (Hybrid Scrape & Cache with Email Deliverability Guardrails)

Evaluates job descriptions against a candidate resume with strict, transparent technical scoring, API budget conservation, and **double-checked, deliverable recruiter outreach intelligence**.

## Features
1. **SQLite Database Caching**: Scraped job descriptions and calculated match scores are persisted in SQLite cache. Subsequent runs on identical URLs return instant results at 0 credit and 0 token cost.
2. **Cheap-First BeautifulSoup Scraper**: Fetches and parses standard career pages (Greenhouse, Lever, Workable, etc.) locally using `requests` + `BeautifulSoup` to avoid burning API credits on basic pages.
3. **Targeted Firecrawl Execution**: Falls back to Firecrawl `/scrape` only when pages require JavaScript rendering or encounter cloud anti-bot challenges.
4. **Credit Budget Guardrail**: Monitors API consumption and warns before exceeding limits.
5. **Strict Recruiter & Email Deliverability Engine**:
   - **DNS / MX Record Validation**: Confirms the recipient domain is active and accepts inbound mail before proposing addresses.
   - **Anti-Bounce Catch-All Filter**: Blocks unmonitored generic prefixes (`recruiting@`, `hiring@`, `careers@`, `jobs@`, `info@`) that cause DSN delivery failures.
   - **Active Decision-Maker Sourcing**: Targets named Technical Recruiters, Talent Leads, and Engineering Directors with verified corporate email formats (`first.last@domain` or `flast@domain`).

## Execution

When triggered via `/jobmatch [resume_path]` or `/jobhunt [resume_path]`:

```bash
python3 scripts/job_matcher.py --resume <path_to_resume> [options]
```

### CLI Options
- `--resume <path>`: Path to resume file (`.pdf`, `.txt`, `.md`).
- `--query <text>`: Target job search keywords (e.g., `"Senior Backend Engineer"`, `"SDET Lead"`).
- `--location <text>`: Target location filter (e.g., `"Remote"`, `"Gurugram"`, `"London"`).
- `--limit <int>`: Number of listings to process (default: 5).
- `--dry-run`: Parse resume and print search query without external network requests.

## Outreach Quality Checklist
Before providing contact info or email drafts:
- [x] Syntax validated via RFC 5322 regex.
- [x] Domain MX verified in DNS.
- [x] Targeted individual named mailbox (no unmonitored generic catch-alls).
- [x] Recruiter/Hiring Manager confirmed currently active in role.
- [x] Valid fallback routing provided.
