---
name: job-hunt
description: >-
  Extracts Senior Software QA Automation Engineer roles (Gurugram/Noida/Remote)
  using Firecrawl, evaluates resume match via LLM (prioritizing Python + Playwright
  and Independent QA Project Leadership), and presents a ranked terminal table.
  Trigger with `/jobhunt [path_to_resume]`.
---

# Job Hunt Automation Skill

Wraps the `job_matcher.py` engine to parse a candidate's resume, discover matching Senior QA Automation roles across Gurugram, Noida, and Remote locations via Firecrawl, and evaluate the candidate fit using local LLM reasoning.

## Usage

When triggered via `/jobhunt [path_to_resume]` or when asked to find and score Senior QA automation jobs:

1. Identify the input resume file path (`.pdf` or `.txt`).
2. Run the evaluation script:
   ```bash
   python3 scripts/job_matcher.py --resume <path_to_resume>
   ```

## Configuration & Customization
- **Firecrawl API Key**: Configured in `.env` (`FIRECRAWL_API_KEY`)
- **LLM Endpoint**: Configured in `.env` (`LLM_BASE_URL`, `LLM_MODEL`)
- **Script location**: [`scripts/job_matcher.py`](../../scripts/job_matcher.py)
