# Antigravity Agent Workspace Rules & Registered Skills

Universal pair-programming and automation rules for Google Antigravity (AGY).

## Active Workspace Skills

| Skill | Trigger / Command | Description |
| :--- | :--- | :--- |
| **linkedin-official-publisher** | `/linkedin-publish [topic]` | Drafts, formats, and publishes posts to LinkedIn via official `/rest/posts` REST API with mandatory versioning, UUID idempotency keys, and Rich dry-run previews. |
| **linkedin-company-manager** | `/linkedin-company [comments\|posts]` | Monitors LinkedIn Organization Pages, inspects updates, retrieves comments, and posts official replies via Community Management API (`/rest/socialActions`). |
| **resume-builder** | `/resume-build [file]` | Ingests background info (.pdf, .docx, .md, .txt, .json), applies ATS heuristics & Google XYZ metric quantification, guarantees 1-page vertical fit, and provides bidirectional LaTeX conversions. |
| **job-matcher** | `/jobmatch [resume]` | Evaluates job postings with Hybrid Scrape & Cache (SQLite + BS4 + Firecrawl), verified recruiter sourcing, and anti-bounce email deliverability guardrails. |
| **oss-contributor** | `/contribute [issue_url]` | Autonomous open-source contribution engine for exploring issues, validating reproductions, and automating pull request workflows. |
| **code-reviewer** | `/review [path_or_diff]` | Senior-level code review focusing on security, performance, logic correctness, and clean architecture. |
| **github-ci-debugger** | `/ci-debug [run_id]` | Inspects GitHub Actions runs, extracts failed logs with token-efficient commands, and patches code. |
| **github-pr-create** | `/pr-create [title]` | Semantic PR drafting, test verification, and pull request creation via `gh` CLI. |
| **github-pr-review** | `/pr-review [pr_number]` | Reviews GitHub PR diffs and submits structured approvals/comments/change requests. |
| **github-pr-rebase** | `/pr-rebase [branch]` | Linear git rebase, conflict resolution, and safe push with lease verification. |
| **github-release-drafter** | `/release-draft [tag]` | SemVer changelog extraction and GitHub Release publication. |
| **mcp-builder** | `/new-mcp-server [name]` | Builds Model Context Protocol servers in Python (FastMCP) or TypeScript. |
| **prompt-engineer** | `/prompt-opt [task]` | Designs, evaluates, and refines system prompts, few-shot examples, and tool schemas. |
| **web-researcher** | `/research [query]` | Multi-source technical research, documentation lookup, and comparative synthesis. |

---

## Architecture & Tooling Rules

1. **LinkedIn Official APIs**:
   - Modern `/rest/posts` and 2-step `/rest/images` protocol exclusively.
   - Mandatory headers: `LinkedIn-Version: 202401`, `X-Restli-Protocol-Version: 2.0.0`.
   - Dynamic UUID in `X-RestLi-Idempotency-Key` on every POST mutation.
   - Automatic 401 silent token refresh and 365-day token rotation.
   - Interactive Rich dry-run preview with `[y/N]` confirmation required before live transmission.

2. **Model Context Protocol (MCP)**:
   - Zero-dependency stdio JSON-RPC 2.0 protocol engine with early warning suppression.
   - All server logging directed strictly to `sys.stderr` to maintain clean `stdout` protocol frames.

3. **Git & GitHub Workflows**:
   - Token-efficient native `gh` and `git` commands.
   - Conventional Commits (`feat:`, `fix:`, `refactor:`, `perf:`).
