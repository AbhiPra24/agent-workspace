---
name: job-hunt
description: >-
  Extracts and evaluates Senior Software QA Automation Engineer job listings
  (Gurugram, Noida, Remote) against a candidate's resume using Firecrawl MCP
  and Antigravity intelligence. Prioritizes Python + Playwright and independent
  project QA leadership over direct people management. Trigger when the user
  runs `/jobhunt`, provides a resume to match with jobs, or asks for QA roles.
---

# Job Hunt & QA Role Matcher Skill (Antigravity Native)

This skill enables Antigravity (`agy`) to autonomously discover, extract, and rank Senior QA Automation Engineer positions using the built-in **Firecrawl MCP** server, matching them against a candidate's resume.

## Target Profile & Evaluation Criteria

- **Target Roles**: Senior Software QA Automation Engineer, SDET Lead, QA Architect.
- **Locations**: Gurugram, Noida, or Remote (India).
- **Core Stack (45% Weight)**: Python, Playwright, PyTest, E2E UI & API Automation, CI/CD pipelines.
- **Leadership Profile (35% Weight)**: 
  - **High Score**: Independent Project QA Leadership, test framework architecture from scratch, test strategy, developer enablement, code quality gates.
  - **Penalize**: Non-technical direct people management roles (HR appraisals, administrative line management, resource scheduling).
- **Domain & Quality Depth (20% Weight)**: Distributed systems testing, Docker, GitHub Actions, performance testing.

---

## Direct Antigravity Workflow

When the user runs `/jobhunt [path_to_resume]` or asks for job matching:

### Step 1: Read Candidate Resume
Use `view_file` to read and parse the candidate's resume (PDF, TXT, or Markdown):
```
Resume path: [provided by user, e.g., scripts/sample_resume.txt]
```

### Step 2: Search Job Listings via Firecrawl MCP
Call the `firecrawl_search` MCP tool:
- **ServerName**: `firecrawl`
- **ToolName**: `firecrawl_search`
- **Arguments**:
  ```json
  {
    "query": "\"Senior Software QA Automation Engineer\" (Gurugram OR Noida OR Remote) \"Python\" \"Playwright\"",
    "limit": 8,
    "scrapeOptions": {
      "formats": ["markdown"]
    }
  }
  ```

### Step 3: Evaluate Each Listing
Evaluate each discovered job listing against the candidate's resume using the evaluation criteria above. Assign a match score from **0 to 100%**.

### Step 4: Present Ranked Match Table
Render a formatted markdown table in the chat:

| Rank | Match Score | Job Title | Company | Leadership Fit | Job URL |
| :--- | :---: | :--- | :--- | :--- | :--- |
| 1 | **95%** 🌟 | Senior QA Automation Engineer | TechScale | Independent QA Lead | [Apply](https://...) |
| 2 | **88%** 🌟 | Lead SDET (Python + Playwright) | FinTech Labs | Technical Project Lead | [Apply](https://...) |
| 3 | **15%** ⛔ | QA People Manager | Enterprise Corp | People Manager (Penalized) | [Apply](https://...) |

Provide a 2-3 bullet breakdown for top matches explaining key stack strengths and alignment.

---

## Alternative CLI Execution
For standalone command-line usage without interactive chat:
```bash
python3 scripts/job_matcher.py --resume <path_to_resume>
```
