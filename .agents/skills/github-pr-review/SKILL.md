---
name: github-pr-review
description: >-
  Fetches Pull Request diffs, reviews changes for security, performance, correctness,
  and architecture, and submits structured PR reviews (Approve, Comment, Request Changes)
  using token-efficient GitHub CLI (gh) bash commands.
  Trigger with `/pr-review [pr_number_or_url]`.
parameters:
  pr:
    type: string
    description: Pull request number, branch name, or GitHub PR URL
    required: true
  action:
    type: string
    description: Review verdict (comment | approve | request-changes)
    default: comment
---

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
