# AI Agent Workspace

A comprehensive workspace for AI agents, Model Context Protocol (MCP) servers, CLI tools, and Antigravity custom skills.

## Directory Structure

```text
agent-workspace/
├── .git/                 # Git repository
├── .gitignore            # Git exclusion rules
├── .env                  # Local secrets and environment variables
├── .env.example          # Environment template
├── requirements.txt      # Python dependencies
├── README.md             # Documentation
│
├── mcp-servers/          # MCP server configurations
│   └── firecrawl-config.json
│
├── skills/               # Antigravity CLI skills
│   ├── job_hunt.skill
│   └── job-hunt/
│       └── SKILL.md
│
├── agents/               # Custom agent configurations & definitions
│
└── scripts/              # Executable automations
    ├── job_matcher.py    # Firecrawl QA job search & LLM matching engine
    └── sample_resume.txt # Sample QA Lead resume for testing
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

# Test with your own PDF or TXT resume
python3 scripts/job_matcher.py --resume /path/to/my_resume.pdf
```

### 4. Trigger via Antigravity Skill
In your Antigravity CLI, you can simply type:
```text
/jobhunt scripts/sample_resume.txt
```
