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

### github-ci-debugger
**Description**: Inspects GitHub Actions workflow runs, downloads and parses failed job logs, extracts root cause stack traces, and suggests targeted code patches using token-efficient gh CLI bash commands. Trigger with `/ci-debug [run_id_or_branch]`.

# GitHub CI Debugger Skill

Diagnoses failed GitHub Actions CI runs with minimal token consumption by targeting only failed step logs.

> [!TIP]
> **Token Optimization**: Never dump full multi-megabyte CI runner logs. Always use `gh run view --log-failed` and pipe through `grep` or `tail` to isolate exact error stack traces.

## Workflow

### 1. Identify Failed Workflow Run
```bash
# List latest 5 workflow runs in compact tabular format
gh run list --limit 5 --json databaseId,name,status,conclusion,headBranch --jq '.[] | "ID: \(.databaseId) | \(.name) | \(.conclusion) (\(.headBranch))"'

# View specific run summary
gh run view <run_id>
```

### 2. Extract Only Failed Log Lines
```bash
# Download only failed step output (token-optimized)
gh run view <run_id> --log-failed | tail -n 80

# Or search for python/node errors directly
gh run view <run_id> --log-failed | grep -E "(FAIL|Error|Exception|Traceback|AssertionError)" -C 5
```

### 3. Local Reproduction & Code Patch
1. Isolate the failing test name or file from the stack trace.
2. Run the exact test locally:
   ```bash
   pytest tests/test_failed_case.py -v -k "test_name"
   ```
3. Apply the targeted bug fix in the source code.
4. Verify all tests pass locally (`make test`), then commit and push.

### github-issue-triage
**Description**: Analyzes incoming GitHub issues, identifies duplicates, classifies bug vs feature, assigns appropriate labels/milestones, and drafts diagnostic or reproduction responses using token-efficient gh CLI bash commands. Trigger with `/issue-triage [issue_number]`.

# GitHub Issue Triage Skill

Triage bug reports and feature requests efficiently using lightweight `gh` CLI commands.

> [!TIP]
> **Token Optimization**: Use `gh issue view --json title,body,author` and `gh issue list --search` with jq/limit flags to extract only relevant fields.

## Workflow

### 1. Inspect Issue Metadata
```bash
# Retrieve issue details cleanly
gh issue view <issue_number> --json number,title,body,author,labels,createdAt
```

### 2. Search for Duplicate Issues
```bash
# Search open & closed issues matching core keywords (limited to top 5)
gh issue list --search "<keyword1> <keyword2>" --state all --limit 5 --json number,title,state --jq '.[] | "#\(.number) [\(.state)] \(.title)"'
```

### 3. Classification & Label Application
Determine:
- **Type**: `bug`, `enhancement`, `documentation`, `question`
- **Priority**: `p0-urgent`, `p1-high`, `p2-medium`, `p3-low`
- **Area**: `area/cli`, `area/skills`, `area/mcp`, `area/core`

Apply labels via `gh` CLI:
```bash
gh issue edit <issue_number> --add-label "bug,area/cli"
```

### 4. Post Diagnostic or Triage Reply
If reproduction details or logs are missing:
```bash
gh issue comment <issue_number> --body "Thanks for reporting! Could you please share the exact CLI command used and your OS/Node version so we can reproduce?"
```

### github-pr-create
**Description**: Analyzes git diff and commit history, drafts semantic PR title and description with test verification and breaking change notices, and creates the pull request via token-efficient GitHub CLI (gh) bash commands. Trigger with `/pr-create [title_or_target_branch]`.

# GitHub PR Creator Skill

Automates end-to-end Pull Request creation using fast, token-efficient `gh` CLI and `git` bash commands.

> [!TIP]
> **Token Optimization**: Always execute direct `gh` and `git` shell commands instead of invoking heavy MCP tools. Filter outputs to keep context compact.

## Workflow

### 1. Fast Git State Inspection
Run lightweight bash commands:
```bash
# Check current branch
CURRENT_BRANCH=$(git branch --show-current)

# Check staged/unstaged status cleanly
git status --short

# Check commit history since branching from main
git log origin/main..HEAD --oneline

# Inspect targeted diff (compact summary first)
git diff --stat origin/main...HEAD
```

### 2. Title & Description Generation
Adhere to **Conventional Commits**:
- `feat(scope): ...` for new features
- `fix(scope): ...` for bug fixes
- `refactor(scope): ...` for internal structural improvements
- `docs(scope): ...`, `test(scope): ...`, `chore(scope): ...`

Draft a clean, structured PR body:
```markdown
## Summary
Concise 2-3 sentence overview of what this PR introduces and why.

## Proposed Changes
- **<Component>**: Specific bullet points of additions/modifications.
- **Architectural Decisions**: Rationale for design choices.

## Breaking Changes
- [ ] None / Detailed description if breaking.

## Verification & Testing
- [x] Automated tests passing (`make test` / `pytest`)
- [x] Manual verification performed

## Related Issues
Closes #<issue_number>
```

### 3. Push Branch & Create PR via `gh` CLI
```bash
# 1. Push branch to remote with upstream tracking
git push -u origin "$CURRENT_BRANCH"

# 2. Open Pull Request directly via gh CLI
gh pr create \
  --base main \
  --title "<semantic_title>" \
  --body "<structured_body>"

# (Optional: for draft PRs, add --draft)
```

### 4. Output Summary
Provide the user with the direct PR URL, title, and confirmation.

### github-pr-rebase
**Description**: Rebases current branch or PR on top of target base branch, resolves merge conflicts, maintains clean linear history, and safely pushes with lease verification using direct git and gh CLI bash commands. Trigger with `/pr-rebase [base_branch]`.

# GitHub PR Rebase & Conflict Resolver Skill

Maintains clean, linear git histories and synchronizes feature branches with upstream using fast, token-efficient `git` and `gh` shell commands.

> [!TIP]
> **Token Optimization**: Use native `git` commands in shell. Avoid verbose logs; use `git status --short` and `git log --oneline -n 5` to preserve context tokens.

## Safety Principles
1. **Always use `--force-with-lease`**: Never use blind `--force` to prevent overwriting teammates' remote commits.
2. **Linear History**: Rebase rather than creating cluttering merge commits.
3. **Clean Working Tree**: Ensure `git status --short` is clean before rebasing.

## Workflow

### 1. Fetch & Check Branch Status
```bash
# Fetch latest remote state
git fetch origin main --prune

# View incoming commits on main
git log HEAD..origin/main --oneline

# View current branch commits to be replayed
git log origin/main..HEAD --oneline
```

### 2. Execute Git Rebase
```bash
# Rebase feature branch on top of origin/main
git rebase origin/main
```

### 3. Handle Conflicts (if any)
```bash
# 1. Identify conflicted files cleanly
git diff --name-only --diff-filter=U

# 2. Inspect conflict markers in specific files
# (Edit files to resolve conflicts and remove <<<<<<< / ======= / >>>>>>> markers)

# 3. Verify project build & tests
make test # or pytest / npm test

# 4. Stage resolved files and continue rebase
git add <resolved_files>
git rebase --continue

# (Emergency rollback if needed: git rebase --abort)
```

### 4. Push Safely via `git`
```bash
# Safe force push protecting remote changes
git push --force-with-lease origin HEAD
```

### github-pr-review
**Description**: Fetches Pull Request diffs, reviews changes for security, performance, correctness, and architecture, and submits structured PR reviews (Approve, Comment, Request Changes) using token-efficient GitHub CLI (gh) bash commands. Trigger with `/pr-review [pr_number_or_url]`.

# GitHub PR Reviewer Skill

Performs deep, senior-level code reviews on GitHub Pull Requests using lightweight, token-efficient `gh` CLI commands.

> [!TIP]
> **Token Optimization**: Use targeted `gh` JSON filters (`--json`) and diff limiters rather than dumping raw full repository payloads. Never use heavy MCP tool round-trips for PR reviews.

## Workflow

### 1. Fetch PR Metadata & Compact Diff
```bash
# Fetch essential metadata (token-optimized JSON fields)
gh pr view <pr_number> --json number,title,author,baseRefName,headRefName,statusCheckRollup,additions,deletions,changedFiles

# Fetch changed files summary first
gh pr view <pr_number> --json files --jq '.files[] | "\(.path) (+\(.additions) -\(.deletions))"'

# Fetch the exact code diff
gh pr diff <pr_number>
```

### 2. Multi-Dimensional Review Rubric

Inspect changes across 5 senior-level dimensions:
1. **Correctness & Logic**: Null safety, boundary values, error propagation, off-by-one errors, concurrency hazards.
2. **Security & Vulnerabilities**: SQL/Command/XSS injection, unvalidated user inputs, hardcoded secrets/credentials, improper access control.
3. **Performance & Scalability**: Inefficient loops, unindexed DB queries, memory leaks, algorithmic complexity ($O(N)$ vs $O(N^2)$).
4. **Test Coverage**: Presence of unit/integration tests for new code paths, test determinism.
5. **Architectural Cleanliness**: Separation of concerns, backwards compatibility, typing annotations, maintainability.

### 3. Submit Structured Review via `gh` CLI

Format feedback into:
- 🚨 **Blockers (Must-Fix)**: Security issues, critical logic defects.
- 💡 **Suggestions (Non-Blocking)**: Refactors, performance optimizations.
- 👏 **Positive Feedback**: Commending clean abstractions.

Execute the review submission:
```bash
# Submit general review comment:
gh pr review <pr_number> --comment --body "<markdown_review>"

# Submit approval:
gh pr review <pr_number> --approve --body "<markdown_review>"

# Request changes:
gh pr review <pr_number> --request-changes --body "<markdown_review>"
```

### github-release-drafter
**Description**: Extracts merged PRs, commits, and breaking changes since the latest git tag, generates semver release notes, and publishes GitHub releases with changelogs using token-efficient gh CLI and git bash commands. Trigger with `/release-draft [version_tag]`.

# GitHub Release Drafter Skill

Generates semantic versioning changelogs and publishes GitHub Releases using direct, token-efficient `gh` CLI and `git` commands.

> [!TIP]
> **Token Optimization**: Use `gh pr list` and `git log` with targeted format specifiers to pull only commit subjects and PR titles, preventing giant payload dumps.

## Workflow

### 1. Scope Extraction via Git & `gh`
```bash
# Find latest tag
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

# If tag exists, get commits since tag; otherwise get last 30 commits
if [ -n "$LATEST_TAG" ]; then
  git log "${LATEST_TAG}..HEAD" --oneline --no-merges
else
  git log -n 30 --oneline --no-merges
fi

# Fetch recent merged PRs in compact JSON format
gh pr list --state merged --limit 20 --json number,title,author --jq '.[] | "- #\(.number) \(.title) (@\(.author.login))"'
```

### 2. Categorize Changes & SemVer Calculation
Group entries into standard release sections:
- 🚀 **Features**: New additions (`feat: ...`)
- 🐛 **Bug Fixes**: Patches (`fix: ...`)
- ⚡ **Performance & Refactoring**: Optimizations (`perf: ...`, `refactor: ...`)
- 💥 **Breaking Changes**: Non-backwards compatible changes (`feat!: ...`, `BREAKING CHANGE`)
- 📝 **Documentation & Chores**: Maintenance (`docs: ...`, `chore: ...`)

**Version Determination**:
- Breaking Changes $\to$ **Major** (`v2.0.0`)
- Features $\to$ **Minor** (`v1.1.0`)
- Fixes only $\to$ **Patch** (`v1.0.1`)

### 3. Publish Release via `gh` CLI
```bash
gh release create <tag_name> \
  --title "<tag_name> - <Release Title>" \
  --notes "<markdown_changelog>" \
  --draft
```
*(Remove `--draft` flag when publishing live production releases)*

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

### resume-builder
**Description**: Ingests candidate background info from any source (.pdf, .docx, .txt, .md, .tex, or raw notes), applies deep ATS heuristics & Google XYZ metric quantification, generates crystal-clear modern LaTeX resumes, and provides bidirectional conversion to/from LaTeX (Markdown, Text, JSON, PDF). Trigger with `/resume-build [input_path]` or `/resume [input_path]`.

# ATS Resume Architect & Bidirectional LaTeX Converter Skill

Transforms raw candidate documents or unstructured experience notes into high-impact, ATS-optimized, crystal-clear LaTeX resumes with full bidirectional format conversion.

## Core Capabilities
1. **Multi-Format Ingestion**: Extracts text from `.pdf`, `.docx`, `.md`, `.txt`, `.tex`, `.json`, or unformatted input notes.
2. **Bidirectional Format Conversion**:
   - **TO LaTeX**: Converts `.pdf`, `.docx`, `.md`, `.txt`, or `.json` into production-ready `.tex`.
   - **FROM LaTeX**: Converts `.tex` resumes into clean GitHub Markdown (`.md`), plain text (`.txt` for forms), structured JSON (`.json`), or compiled `.pdf`.
3. **ATS Heuristic Audit Engine**: Scores resumes (0–100) across Structure, Metric Quantification, Action Verbs, and Readability.
4. **Google XYZ Formula Transformer**: Restructures weak, passive bullet points into high-impact accomplishments (*"Accomplished [X] as measured by [Y], by doing [Z]"*).
5. **Modern LaTeX Generation**: Emits clean, production-grade LaTeX utilizing `titlesec`, `geometry`, `enumitem`, and legible modern sans-serif typography (`\renewcommand{\familydefault}{\sfdefault}`).
6. **Compilation Bridge**: Automatically builds `.pdf` output when `pdflatex`, `xelatex`, or `tectonic` are present.

---

## The 4 Pillars of High ATS Score & Readability

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ATS OPTIMIZATION MATRIX                         │
├────────────────────────┬───────────────────────────────────────────────┤
│ 1. 100% Parseable      │ • Single-column layout ONLY (no sidebar/grid) │
│    Structure           │ • Standard headers (Summary, Experience, etc.)│
│                        │ • Standard fonts (Computer Modern / Helvetica)│
├────────────────────────┼───────────────────────────────────────────────┤
│ 2. Quantified Impact   │ • Google XYZ formula: Metric in >= 50% bullets│
│    (Metrics)           │ • Quantifiers: %, $, 2x, 100+, latency ms     │
├────────────────────────┼───────────────────────────────────────────────┤
│ 3. Strong Action Verbs │ • Start every bullet with strong active verb  │
│                        │ • Zero passive phrases ("responsible for...") │
├────────────────────────┼───────────────────────────────────────────────┤
│ 4. Keyword Alignment   │ • Clear Categorized Skills (Languages, Infra) │
│                        │ • Exact industry standard tech keywords       │
└────────────────────────┴───────────────────────────────────────────────┘
```

---

## Bidirectional Conversion Workflows

### 1. Convert LaTeX to Markdown / Plain Text / JSON / PDF
```bash
# Convert LaTeX to Markdown
python3 scripts/resume_builder.py convert --input resume.tex --to md --output resume.md

# Convert LaTeX to Plain Text (for job portal copy-paste)
python3 scripts/resume_builder.py convert --input resume.tex --to txt --output resume.txt

# Convert LaTeX to Structured JSON
python3 scripts/resume_builder.py convert --input resume.tex --to json --output resume.json

# Convert LaTeX to PDF
python3 scripts/resume_builder.py convert --input resume.tex --to pdf
```

### 2. Convert Markdown / JSON / PDF / DOCX to LaTeX
```bash
# Convert Markdown to LaTeX
python3 scripts/resume_builder.py convert --input resume.md --to latex --output resume.tex

# Convert JSON to LaTeX
python3 scripts/resume_builder.py convert --input resume.json --to latex --output resume.tex

# Ingest PDF/DOCX and build ATS-optimized LaTeX
python3 scripts/resume_builder.py build --input resume.pdf --output resume.tex
```

---

## Step-by-Step Agent Execution Workflow

When user invokes `/resume-build [file_path]` or asks to craft/tailor/convert a resume:

### Phase 1: Ingest & Extract
Extract plain text and structural signals from the input document:
```bash
python3 scripts/resume_builder.py extract --input <path_to_input_file>
```

### Phase 2: ATS Pre-Audit & Analysis
Run the built-in diagnostic audit to identify gaps in metrics, weak verbs, or structure:
```bash
python3 scripts/resume_builder.py audit --input <path_to_input_file>
```

### Phase 3: Content Transformation & Metric Hardening
1. **Apply Google XYZ Formula**:
   - ❌ *Weak*: "Worked on automation frameworks and ran test suites for EV charging."
   - ✅ *Strong*: "Architected modular BDD automation frameworks (Python/Behave) and integrated into Jenkins CI/CD pipelines, achieving **40% faster execution** across deployment cycles."
2. **Prioritize Technical Ownership**: Emphasize architectural initiatives, tooling creation, DevSecOps/security validation, and reliability improvements.
3. **Categorize Technical Skills**: Group skills logically into clean lines (e.g., *Frameworks & Languages*, *DevOps & Infrastructure*, *Databases & Security*, *Protocols & APIs*).

### Phase 4: LaTeX Code Generation & Review
Generate the standardized LaTeX file with tight margin spacing and clean formatting:
```bash
python3 scripts/resume_builder.py build --input <path_to_input_file> --output <output_path.tex>
```

---

## Canonical LaTeX Structure Template

```latex
\documentclass[a4paper,10pt]{article}
\usepackage[margin=0.5in]{geometry}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}

% Clean, modern Sans-Serif Font
\renewcommand{\familydefault}{\sfdefault}

% Section formatting: Uppercase with crisp divider rule
\titleformat{\section}{\large\bfseries\uppercase}{}{0em}{}[\titlerule]
\titlespacing*{\section}{0pt}{1.2ex plus 1ex minus .2ex}{0.8ex plus .2ex}

% Dense, readable itemized list
\setlist[itemize]{noitemsep, topsep=2pt, leftmargin=1.5em, parsep=0pt, partopsep=0pt}

\begin{document}

%----------------------------
% Name and Contact
%----------------------------
\begin{center}
    {\Huge \textbf{Candidate Name}}\\[4pt]
    \href{mailto:email@example.com}{email@example.com} \,|\,
    +91 99999 99999 \,|\,
    Location, Country \,|\,
    \href{https://linkedin.com/in/profile}{linkedin.com/in/profile} \,|\,
    \href{https://github.com/profile}{github.com/profile}
\end{center}

%----------------------------
\section{Summary}
\begin{itemize}
    \item Senior Engineer with \textbf{5+ years} of experience architecting scalable test systems and CI/CD pipelines.
    \item Track record of building shared developer tools, reducing triage time by 30\% across cross-functional teams.
\end{itemize}

%----------------------------
\section{Experience}
\textbf{Senior Software Engineer} \hfill \textit{Apr 2024 -- Present}\\
Company Name, Location
\begin{itemize}
    \item Spearheaded system architecture and pipeline automation, achieving \textbf{40\% faster deployment cycles}.
    \item Architected internal utilities in Python and FastAPI, cutting defect triage time by 30\%.
\end{itemize}

%----------------------------
\section{Education}
\textbf{B.Tech, Computer Science} \hfill \textit{2018 -- 2022}\\
Institute / University Name

%----------------------------
\section{Skills}
\textbf{Languages \& Frameworks:} Python, Java, FastAPI, Pytest, Playwright\\
\textbf{DevOps \& Infrastructure:} Docker, Jenkins, Linux CLI, Git, CI/CD\\
\textbf{Protocols \& Security:} REST API, Postman, Wireshark, Burp Suite

\end{document}
```

---

## CLI Reference

| Command | Usage | Description |
|---|---|---|
| `audit` | `python3 scripts/resume_builder.py audit -i <file>` | Runs 100-point ATS evaluation |
| `convert` | `python3 scripts/resume_builder.py convert -i <file> -t [md|txt|json|latex|pdf]` | Bidirectional format converter |
| `build` | `python3 scripts/resume_builder.py build -i <file> -o resume.tex` | Generates ATS-optimized LaTeX |
| `extract` | `python3 scripts/resume_builder.py extract -i <file>` | Dumps raw text from PDF/DOCX |
| `compile` | `python3 scripts/resume_builder.py compile -i resume.tex` | Compiles LaTeX to PDF |

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

### linkedin-official-publisher
**Description**: Drafts, formats, and publishes high-impact posts to LinkedIn using the official REST API (/rest/posts) with mandatory versioning headers, automatic UUID idempotency keys, and interactive Rich terminal previews with dry-run confirmation before live transmission. Trigger with `/linkedin-publish [topic_or_draft] [--media path] [--link url]`.

# LinkedIn Official Publisher Skill

Executes 100% compliant post publishing via LinkedIn's official `/rest/posts` API with built-in character limit validation, visual previews, and idempotency protection.

## Core Architectural Guardrails
1. **Modern Endpoints Exclusively**: Targets `POST /rest/posts` (never deprecated `/v2/ugcPosts` or `/v2/shares`).
2. **Mandatory Versioning Headers**: Globally injects `LinkedIn-Version: 202401` and `X-Restli-Protocol-Version: 2.0.0`.
3. **Idempotency Protection**: Injects a cryptographically unique UUID into `X-RestLi-Idempotency-Key` on every POST to prevent accidental duplicates.
4. **2-Step Media Upload**: Executes `initializeUpload` -> binary `PUT` for images before attaching to posts.
5. **Dry-Run Default**: Prints a Rich console diff showing character counts, hook structure, and parsed hashtags, requiring `[y/N]` confirmation before live dispatch.

## Execution
```bash
# Preview post in terminal before publishing
python3 scripts/linkedin_suite.py publish --text "Exploring new AI agent architectures with official LinkedIn APIs #ai #python"

# Publish with attached image
python3 scripts/linkedin_suite.py publish --text "System Blueprint" --media architecture.png

# Check profile & member URN
python3 scripts/linkedin_suite.py profile

# Rotate 365-day token
python3 scripts/linkedin_suite.py refresh
```

### linkedin-company-manager
**Description**: Monitors LinkedIn Organization Pages, inspects recent company updates, retrieves inbound comment threads, and posts official company replies using LinkedIn's Community Management API (/rest/socialActions). Trigger with `/linkedin-company [comments|posts|reply] [--urn target_urn]`.

# LinkedIn Company Manager Skill

Manages LinkedIn Organization/Company pages and community discussions using official LinkedIn Community Management endpoints (`/rest/socialActions` and `/rest/posts`).

## Capabilities
1. **Activity Monitoring**: Lists recent posts authored by an organization page.
2. **Comment Moderation**: Pulls live comment threads on company posts.
3. **Official Replies**: Crafts and submits official responses as the company or admin actor.

## Execution
```bash
# Fetch comments on post URN
python3 scripts/linkedin_suite.py comments --urn urn:li:share:123456789 --count 20
```


