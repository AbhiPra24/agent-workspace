---
name: job-matcher
description: >-
  Extracts, evaluates, and ranks job postings against candidate resumes using an
  intelligent Hybrid Scrape & Cache layer (SQLite + BeautifulSoup + Firecrawl MCP fallback)
  and local or cloud LLM scoring.
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

# Job Matcher Skill (Hybrid Scrape & Cache)

Evaluates job descriptions against a candidate resume with strict, transparent technical scoring and aggressive API budget conservation.

## Features
1. **SQLite Database Caching**: Scraped job descriptions and calculated match scores are persisted in SQLite cache. Subsequent runs on identical URLs return instant results at 0 credit and 0 token cost.
2. **Cheap-First BeautifulSoup Scraper**: Fetches and parses standard career pages (Greenhouse, Lever, Workable, etc.) locally using `requests` + `BeautifulSoup` to avoid burning API credits on basic pages.
3. **Targeted Firecrawl Execution**: Falls back to Firecrawl `/scrape` only when pages require JavaScript rendering or encounter cloud anti-bot challenges.
4. **Credit Budget Guardrail**: Monitors API consumption and warns before exceeding limits.

## Execution

When triggered via `/jobmatch [resume_path]` or `/jobhunt [resume_path]`:

```bash
python3 scripts/job_matcher.py --resume <path_to_resume> [options]
```

### CLI Options
- `--resume <path>`: Path to resume file (`.pdf`, `.txt`, `.md`).
- `--query <text>`: Target job search keywords (e.g., `"Senior Backend Engineer"`, `"SDET Lead"`).
- `--location <text>`: Target location filter (e.g., `"Remote"`, `"New York"`, `"London"`).
- `--limit <int>`: Number of listings to process (default: 5).
- `--dry-run`: Parse resume and print search query without external network requests.
