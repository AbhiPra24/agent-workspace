# Claude Workspace Guidelines & Active Skills

This repository is equipped with modular AI Agent skills.

## Quickstart & Workflows
- Check environment: `make doctor`
- List skills & MCP servers: `make list`
- Run test validations: `make test`

## Active Skills & Capabilities
### code-reviewer
**Description**: Performs deep, senior-level code reviews focusing on architecture, security vulnerabilities, performance bottlenecks, test coverage, and adherence to clean code principles. Trigger with `/review [path_or_git_diff]`.

# Code Reviewer Skill

Rigorous, production-focused code inspection agent tailored for modern software engineering standards.

## Review Pillars

### 1. Correctness & Logic
- Edge cases (null/empty inputs, boundary conditions, timeout handling, off-by-one errors).
- Concurrency, race conditions, and thread safety.
- Resource cleanup (connections, file handles, memory allocations).

### 2. Security & Safety
- Input validation and sanitization (SQL injection, XSS, SSRF, command injection).
- Authentication and authorization checks.
- Secrets or credentials checked into version control.
- Safe dependency usage and permission boundaries.

### 3. Architecture & Modularity
- Separation of concerns and single responsibility principle.
- API design, backwards compatibility, and schema versioning.
- Scalability and algorithmic complexity (Big-O time and space).

### 4. Quality & Testing
- Unit and integration test coverage for modified code paths.
- Error handling and meaningful log/error messages.
- Readability, self-documenting naming, and maintainability.

## Output Format
- **Summary**: Concise high-level verdict (`Approved`, `Approved with Comments`, `Changes Requested`).
- **Critical / Blocker Issues**: Must-fix security or correctness defects.
- **Suggestions & Improvements**: Non-blocking optimizations, refactors, and test additions.
- **Line-by-line Comments**: Clickable markdown references with code diff blocks.

### job-matcher
**Description**: Extracts, evaluates, and ranks job postings against candidate resumes using an intelligent Hybrid Scrape & Cache layer (SQLite + BeautifulSoup + Firecrawl MCP fallback) and local or cloud LLM scoring. Trigger with `/jobmatch [resume_path] [optional_keywords]` or `/jobhunt [resume_path]`.

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

### mcp-builder
**Description**: Guides the design, implementation, testing, and distribution of Model Context Protocol (MCP) servers in Python or TypeScript according to the official MCP specifications. Trigger with `/new-mcp-server [server_name]`.

# MCP Server Builder Skill

End-to-end guidance for developing production-grade Model Context Protocol (MCP) servers.

## Core Capabilities
- **Architecture**: Define Tools, Resources, and Prompts using standard MCP schemas.
- **Transport Support**: Configure stdio (standard input/output) or SSE (Server-Sent Events) transports.
- **Validation**: Test tool schemas with Pydantic (Python) or Zod (TypeScript).
- **Integration**: Generate ready-to-use configuration JSON for Claude Desktop, Cursor, and Antigravity.

## Standard Project Layout

### Python (FastMCP / MCP SDK)
```text
mcp-server-example/
├── server.py              # Main FastMCP server definitions
├── requirements.txt       # Dependencies (mcp>=1.0.0, etc.)
└── README.md              # Installation & configuration guide
```

### TypeScript (MCP TypeScript SDK)
```text
mcp-server-example/
├── src/
│   └── index.ts           # Server entrypoint with Server instance
├── package.json           # @modelcontextprotocol/sdk dependency
└── tsconfig.json
```

## Best Practices
1. **Clear Tool Descriptions**: Write descriptive docstrings explaining tool intent, input schemas, and expected output.
2. **Error Handling**: Return structured error responses instead of crashing the stdio process.
3. **Environment Security**: Never hardcode API keys; load them from environment variables.

### prompt-engineer
**Description**: Designs, evaluates, and optimizes system prompts, few-shot examples, tool schemas, and agent personas for maximum reasoning accuracy and reliability. Trigger with `/prompt-opt [prompt_or_task]`.

# Prompt Engineer Skill

Systematic methodology for authoring, evaluating, and refining LLM prompts and agent instructions.

## Prompt Architecture Framework

Every robust prompt should include:
1. **Identity & Role Definition**: Precise persona, authority scope, and background context.
2. **Operational Constraints**: Explicit negative constraints (what NOT to do) and positive constraints.
3. **Execution Steps (Algorithm)**: Step-by-step reasoning procedure before taking action.
4. **Tool Use & Format Requirements**: Exact input/output schemas, JSON formatting, or markdown guidelines.
5. **Few-Shot Demonstrations**: High-quality input-output pairs illustrating edge cases and desired formatting.

## Heuristics for High Accuracy
- **Chain of Thought**: Instruct the model to deliberate in `<thinking>` blocks before emitting final answers.
- **XML / Markdown Delimiters**: Use tags like `<user_query>`, `<context>`, `<rules>` to eliminate prompt injection and confusion.
- **Edge-Case Anchoring**: Provide explicit fallback actions when data is missing or ambiguous.

### web-researcher
**Description**: Performs multi-step, autonomous web research, documentation lookup, fact verification, and synthesizes findings into structured technical summaries or comparison tables. Trigger with `/research [query]`.

# Web Researcher Skill

Conducts exhaustive, evidence-based research across official documentation, technical blogs, and public web sources.

## Workflow
1. **Query Decomposition**: Breaks the user's research topic into 3-5 precise search queries.
2. **Multi-Source Gathering**:
   - Queries web search engines (Brave Search / DuckDuckGo).
   - Fetches documentation and technical articles using `fetch` or `firecrawl` MCP tools.
3. **Synthesis & Fact Verification**:
   - Compares statements across multiple independent sources.
   - Discards outdated or conflicting claims.
4. **Structured Delivery**:
   - Produces an executive summary, key findings, comparative tables, and direct source citations.

## Guidelines
- Always prioritize primary official documentation over third-party blog summaries.
- Explicitly note version compatibility and release dates.
- Format results with clear headings, bullet points, and markdown tables.

