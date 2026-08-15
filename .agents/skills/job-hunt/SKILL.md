---
name: job-hunt
description: >-
  Extracts Senior Software QA Automation Engineer roles (Gurugram/Noida/Remote)
  using a Hybrid Scrape & Cache layer (SQLite + Cheap BS4 + Targeted Firecrawl MCP),
  evaluates resume match via LLM (prioritizing Python + Playwright and Independent
  QA Project Leadership), and presents a ranked terminal table.
  Trigger with `/jobhunt [path_to_resume]`.
---

# Job Hunt Automation Skill (Hybrid Scrape & Cache)

Wraps the upgraded `job_matcher.py` engine to evaluate Senior QA Automation Engineer positions while aggressively protecting your monthly Firecrawl credit budget.

## Hybrid Scrape & Cache Features
1. **SQLite Database Caching (`jobs_cache.db`)**: Scraped listings and evaluation scores are cached locally to prevent duplicate network calls.
2. **Cheap First Scraping (BeautifulSoup)**: Scrapes standard career pages locally using `requests` + `BeautifulSoup` to avoid burning credits on initial crawls.
3. **Targeted Firecrawl Execution**: Restricts Firecrawl `/scrape` calls strictly to individual, verified job description URLs (no wildcards or root crawls).
4. **Credit Budget Guardrail (`.firecrawl_tracker.json`)**: Automatically tracks monthly credit usage and warns when approaching limits (>= 800 / 1000).

## Usage

When triggered via `/jobhunt [path_to_resume]` or when asked to find and score Senior QA automation jobs:

1. Identify the input resume file path (`.pdf` or `.txt`).
2. Run the evaluation script:
   ```bash
   python3 scripts/job_matcher.py --resume <path_to_resume>
   ```
