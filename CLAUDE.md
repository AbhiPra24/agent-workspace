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
**Description**: Inspects GitHub Actions workflow runs, downloads and parses failed job logs, extracts root cause stack traces, and suggests targeted code patches. Trigger with `/ci-debug [run_id_or_branch]`.

# GitHub CI Debugger Skill

Automates diagnosis and resolution of failed GitHub Actions continuous integration (CI) workflows.

## Workflow

### 1. Identify Failed Runs & Jobs
- List recent workflow runs:
  ```bash
  gh run list --limit 10 --json databaseId,name,status,conclusion,headBranch,url
  ```
- Identify the failed run ID and view run details:
  ```bash
  gh run view <run_id>
  ```

### 2. Extract Failed Job Logs
- Download failure log lines:
  ```bash
  gh run view <run_id> --log-failed
  ```
- Filter out noise (ANSI escape codes, runner setup/teardown steps) to isolate:
  - Exact failing test assertion or error message.
  - Full Python/TypeScript/Go stack trace.
  - Environment differences (OS version, missing dependencies, locked files).

### 3. Root-Cause Analysis & Code Fix
- Map stack trace lines to source repository files.
- Formulate hypothesis for failure:
  - Test assertion mismatch / updated schema.
  - Missing environment variable or secret.
  - Platform/OS-specific path separator or concurrency timing.
  - Dependency version drift.
- Apply code patch locally, run test suite to verify fix, and commit fix.

### github-issue-triage
**Description**: Analyzes incoming GitHub issues, identifies duplicates, classifies bug vs feature, assigns appropriate labels/milestones, and drafts diagnostic or reproduction responses. Trigger with `/issue-triage [issue_number]`.

# GitHub Issue Triage Skill

Streamlines open-source and team issue triage by categorizing reports, checking for duplicate tickets, and formulating reproduction checklists.

## Workflow

### 1. Fetch Issue Details
- Retrieve issue body, author, existing labels, and comments:
  ```bash
  gh issue view <issue_number> --json number,title,body,author,labels,comments,createdAt
  ```

### 2. Duplicate Detection
- Search repository for existing issues with similar keywords or error traces:
  ```bash
  gh issue list --search "<key_terms>" --state all --json number,title,state
  ```
- If a duplicate is identified, note the duplicate ID and prepare a closure reference.

### 3. Classification & Triage Plan
Classify into:
- **Type**: `bug`, `feature-request`, `documentation`, `question`
- **Severity**: `p0-critical`, `p1-high`, `p2-medium`, `p3-low`
- **Component Area**: e.g., `area/cli`, `area/skills`, `area/mcp`, `area/ci`

### 4. Response Drafting & Action
- If information is missing (reproduction steps, logs, OS version), draft a polite diagnostic template requesting clarification.
- If bug is clear, assign appropriate labels:
  ```bash
  gh issue edit <issue_number> --add-label "bug,triage/accepted,area/cli"
  ```
- Post comment with reproduction verification or resolution roadmap:
  ```bash
  gh issue comment <issue_number> --body "<triage_response>"
  ```

### github-pr-create
**Description**: Analyzes git diff and commit history, drafts semantic PR title and description with test verification and breaking change notices, and creates the pull request via GitHub CLI or MCP. Trigger with `/pr-create [title_or_target_branch]`.

# GitHub PR Creator Skill

Automates end-to-end Pull Request generation following professional open-source and enterprise standards.

## Workflow

### 1. Git State Inspection
- Check current branch: `git branch --show-current`
- Verify working tree is clean and local commits are up-to-date:
  ```bash
  git status
  git log origin/main..HEAD --oneline
  ```
- Generate complete diff against base branch:
  ```bash
  git diff origin/main...HEAD
  ```

### 2. Title & Description Generation
Generate a semantic title adhering to **Conventional Commits**:
- `feat(scope): ...` for new features
- `fix(scope): ...` for bug fixes
- `refactor(scope): ...` for structural changes without behavior alterations
- `docs(scope): ...`, `test(scope): ...`, `chore(scope): ...`

Generate a structured description using the following template:

```markdown
## Summary
Concise 2-3 sentence overview of what this PR does and why.

## Proposed Changes
- **Component / Module**: Bullet points detailing specific additions, deletions, or modifications.
- **Architectural Notes**: Any design decisions or patterns introduced.

## Breaking Changes
- [ ] None / Details of breaking changes if any.

## Verification & Testing
- [x] Unit tests passed (`make test` / `pytest`)
- [x] Manual verification performed (include steps or logs)

## Related Issues
Closes #<issue_number> (if applicable)
```

### 3. Execution & PR Creation
1. Push branch to remote:
   ```bash
   git push -u origin <current_branch>
   ```
2. Create PR using `gh` CLI:
   ```bash
   gh pr create --base main --title "<title>" --body "<body>"
   ```
   *(Or with `--draft` if requested)*
3. Return the created PR URL and review summary to the user.

### github-pr-rebase
**Description**: Rebases current branch or PR on top of target base branch, resolves merge conflicts, maintains clean linear history, and safely pushes with lease verification. Trigger with `/pr-rebase [base_branch]`.

# GitHub PR Rebase & Conflict Resolver Skill

Maintains clean, linear git histories and automates upstream branch synchronization with safety guardrails.

## Safety Rules & Principles
1. **Never use blind `--force`**: Always use `--force-with-lease` to prevent overwriting remote commits pushed by collaborators.
2. **Preserve working tree**: Stash or commit uncommitted local modifications before initiating a rebase.
3. **Linear History**: Rebase feature branches rather than creating messy merge commits into PRs.

## Workflow

### 1. Fetch & Prepare
```bash
# Ensure working directory is clean
git status

# Fetch latest changes from all remotes
git fetch --all --prune
```

### 2. Execute Rebase
```bash
# Rebase current branch onto target base
git rebase origin/main
```

### 3. Merge Conflict Resolution (if conflicts occur)
When conflicts arise:
1. Identify conflicted files:
   ```bash
   git status --short
   ```
2. Analyze conflict markers (`<<<<<<< HEAD`, `=======`, `>>>>>>>`):
   - Determine incoming vs current changes.
   - Edit files to retain correct logic and remove conflict markers.
3. Verify project integrity & run tests:
   ```bash
   make test # or pytest / npm test
   ```
4. Stage resolved files and continue rebase:
   ```bash
   git add <resolved_files>
   git rebase --continue
   ```
   *(To abort safely if needed: `git rebase --abort`)*

### 4. Push Updated Branch
```bash
# Push rebased commits safely
git push --force-with-lease origin HEAD
```

### github-pr-review
**Description**: Fetches Pull Request diffs, reviews changes for security, performance, correctness, and architecture, and submits structured PR reviews (Approve, Comment, Request Changes) via GitHub CLI or MCP. Trigger with `/pr-review [pr_number_or_url]`.

# GitHub PR Reviewer Skill

Performs deep, senior-level code reviews on GitHub Pull Requests.

## Workflow

### 1. Fetch PR Details & Diff
- Retrieve PR metadata and checks:
  ```bash
  gh pr view <pr_number> --json title,body,author,baseRefName,headRefName,statusCheckRollup
  ```
- Fetch full diff:
  ```bash
  gh pr diff <pr_number>
  ```
- Inspect CI status: Check for failed jobs or test timeouts.

### 2. Multi-Dimensional Review Rubric

Review the diff across 5 critical dimensions:
1. **Logic & Correctness**: Edge cases (empty strings, null values, division by zero, network timeouts), concurrency safety, off-by-one errors.
2. **Security & Vulnerabilities**: Injection attacks (SQL/NoSQL/Command/XSS), unsanitized user input, secrets/tokens committed, improper authorization checks.
3. **Performance & Scalability**: N+1 queries, memory leaks, algorithmic complexity ($O(N^2)$ vs $O(N)$), unindexed lookups.
4. **Test Coverage & Reliability**: Are unit/integration tests included for new paths? Are tests deterministic (no flaky time/sleep dependencies)?
5. **Architectural Consistency & Clean Code**: Separation of concerns, backwards compatibility, typing annotations, maintainability.

### 3. Review Formulation & Submission

Draft structured markdown comments:
- Categorize feedback into:
  - 🚨 **Blockers (Must-Fix)**: Security vulnerabilities, logic bugs, test regressions.
  - 💡 **Suggestions (Non-Blocking)**: Refactoring opportunities, documentation improvements.
  - 👏 **Positive Feedback**: Highlighting great design patterns or clean abstractions.

Submit review via `gh` CLI:
```bash
# Submit as general comment
gh pr review <pr_number> --comment --body "<review_markdown>"

# Approve PR
gh pr review <pr_number> --approve --body "<review_markdown>"

# Request changes
gh pr review <pr_number> --request-changes --body "<review_markdown>"
```

### github-release-drafter
**Description**: Extracts merged PRs, commits, and breaking changes since the latest git tag, generates semver release notes, and publishes GitHub releases with changelogs. Trigger with `/release-draft [version_tag]`.

# GitHub Release Drafter Skill

Automates semantic versioning release notes, changelog extraction, and GitHub Release publication.

## Workflow

### 1. Identify Release Scope & Commits
- Locate latest git tag:
  ```bash
  git describe --tags --abbrev=0 2>/dev/null || echo "No previous tags"
  ```
- Collect all commits and merged PRs since previous tag:
  ```bash
  git log $(git describe --tags --abbrev=0 2>/dev/null)..HEAD --pretty=format:"* %s (%h)" --no-merges
  ```
- List merged pull requests via `gh` CLI:
  ```bash
  gh pr list --state merged --limit 30 --json number,title,author,labels,mergedAt
  ```

### 2. Categorize Changes & Determine SemVer
Parse commit messages and PR titles into standard changelog sections:
- 🚀 **Features**: New functionality (`feat: ...`)
- 🐛 **Bug Fixes**: Fixes and patches (`fix: ...`)
- ⚡ **Performance & Refactoring**: Optimizations (`perf: ...`, `refactor: ...`)
- 💥 **Breaking Changes**: Non-backwards-compatible modifications (`BREAKING CHANGE: ...` or `feat!: ...`)
- 📝 **Documentation & Chores**: Internal improvements (`docs: ...`, `chore: ...`)

**Version Bump Heuristic**:
- Breaking changes $\to$ **Major** bump (`vX.0.0`)
- Features $\to$ **Minor** bump (`v0.X.0`)
- Bug fixes only $\to$ **Patch** bump (`v0.0.X`)

### 3. Generate Release Notes & Publish
Draft markdown release notes and publish via `gh`:
```bash
gh release create <tag> \
  --title "<tag> - <Release Title>" \
  --notes "<markdown_changelog>" \
  --draft
```

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

