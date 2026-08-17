# GitHub Copilot Custom Instructions

## Project Guidelines
- Modular, well-typed Python (3.9+) and TypeScript codebase.
- Adhere strictly to the Model Context Protocol standards for MCP servers.
- Use `pydantic` schemas for validation and `rich` for CLI output formatting.

## Registered Agent Skills
- **code-reviewer**: Performs deep, senior-level code reviews focusing on architecture, security vulnerabilities, performance bottlenecks, test coverage, and adherence to clean code principles. Trigger with `/review [path_or_git_diff]`.
- **github-ci-debugger**: Inspects GitHub Actions workflow runs, downloads and parses failed job logs, extracts root cause stack traces, and suggests targeted code patches using token-efficient gh CLI bash commands. Trigger with `/ci-debug [run_id_or_branch]`.
- **github-issue-triage**: Analyzes incoming GitHub issues, identifies duplicates, classifies bug vs feature, assigns appropriate labels/milestones, and drafts diagnostic or reproduction responses using token-efficient gh CLI bash commands. Trigger with `/issue-triage [issue_number]`.
- **github-pr-create**: Analyzes git diff and commit history, drafts semantic PR title and description with test verification and breaking change notices, and creates the pull request via token-efficient GitHub CLI (gh) bash commands. Trigger with `/pr-create [title_or_target_branch]`.
- **github-pr-rebase**: Rebases current branch or PR on top of target base branch, resolves merge conflicts, maintains clean linear history, and safely pushes with lease verification using direct git and gh CLI bash commands. Trigger with `/pr-rebase [base_branch]`.
- **github-pr-review**: Fetches Pull Request diffs, reviews changes for security, performance, correctness, and architecture, and submits structured PR reviews (Approve, Comment, Request Changes) using token-efficient GitHub CLI (gh) bash commands. Trigger with `/pr-review [pr_number_or_url]`.
- **github-release-drafter**: Extracts merged PRs, commits, and breaking changes since the latest git tag, generates semver release notes, and publishes GitHub releases with changelogs using token-efficient gh CLI and git bash commands. Trigger with `/release-draft [version_tag]`.
- **job-matcher**: Extracts, evaluates, and ranks job postings against candidate resumes using an intelligent Hybrid Scrape & Cache layer (SQLite + BeautifulSoup + Firecrawl MCP fallback) and local or cloud LLM scoring. Trigger with `/jobmatch [resume_path] [optional_keywords]` or `/jobhunt [resume_path]`.
- **mcp-builder**: Guides the design, implementation, testing, and distribution of Model Context Protocol (MCP) servers in Python or TypeScript according to the official MCP specifications. Trigger with `/new-mcp-server [server_name]`.
- **prompt-engineer**: Designs, evaluates, and optimizes system prompts, few-shot examples, tool schemas, and agent personas for maximum reasoning accuracy and reliability. Trigger with `/prompt-opt [prompt_or_task]`.
- **resume-builder**: Ingests candidate background info from any source (.pdf, .docx, .txt, .md, .tex, or raw notes), applies deep ATS heuristics & Google XYZ metric quantification, generates crystal-clear modern LaTeX resumes, and provides bidirectional conversion to/from LaTeX (Markdown, Text, JSON, PDF). Trigger with `/resume-build [input_path]` or `/resume [input_path]`.
- **web-researcher**: Performs multi-step, autonomous web research, documentation lookup, fact verification, and synthesizes findings into structured technical summaries or comparison tables. Trigger with `/research [query]`.
