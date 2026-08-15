# AI Agent Workspace & Hybrid Job Matcher

A comprehensive workspace for AI agents, Model Context Protocol (MCP) servers, CLI tools, and Antigravity custom skills.

## Features & Optimizations

- **Hybrid Scrape & Cache Layer**:
  - **SQLite Database Caching (`jobs_cache.db`)**: Automatically caches raw text and evaluated match scores so repeated runs don't consume network bandwidth or LLM tokens.
  - **Cheap First Scraping (BeautifulSoup)**: Scrapes standard career pages and links locally using `requests` + `BeautifulSoup` to avoid burning Firecrawl credits on basic pages.
  - **Targeted Firecrawl Execution**: Restricts Firecrawl API calls strictly to single, validated job description URLs (no wildcards or root domain crawling).
  - **Credit Budget Guardrail (`.firecrawl_tracker.json`)**: Tracks monthly usage and prompts for confirmation if usage approaches 800 / 1,000 credits.

---

## Directory Structure

```text
agent-workspace/
├── .git/                                # Git repository
├── .gitignore                           # Python, venv, and SQLite cache ignore rules
├── .env / .env.example                  # Environment configuration template
├── .firecrawl_tracker.json              # Monthly credit usage tracker
├── jobs_cache.db                        # SQLite database for scraped content & scores
├── requirements.txt                     # Python dependencies
├── README.md                            # Workspace documentation
│
├── mcp-servers/                         # MCP server configurations
│   └── firecrawl-config.json
│
├── skills/                              # Antigravity CLI skills
│   ├── job_hunt.skill
│   └── job-hunt/
│       └── SKILL.md
│
├── agents/                              # Custom agent configurations & definitions
│
└── scripts/                             # Executable automations
    ├── job_matcher.py                   # Hybrid scrape, SQLite cache & LLM matcher
    └── sample_resume.txt                # Sample QA Lead resume for testing
```

---

## Getting Started

### 1. Setup Virtual Environment & Install Dependencies
```bash
cd agent-workspace
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure API Keys
Edit `.env` and provide your credentials:
```bash
FIRECRAWL_API_KEY=fc-YOUR_FIRECRAWL_API_KEY
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3.2
```

### 3. Run Job Matcher Directly
```bash
# Test with the bundled sample resume
python3 scripts/job_matcher.py --resume scripts/sample_resume.txt
```

### 4. Trigger via Antigravity Skill
In your Antigravity CLI, you can simply type:
```text
/jobhunt scripts/sample_resume.txt
```
