---
name: github-issue-triage
description: >-
  Analyzes incoming GitHub issues, identifies duplicates, classifies bug vs feature,
  assigns appropriate labels/milestones, and drafts diagnostic or reproduction responses.
  Trigger with `/issue-triage [issue_number]`.
parameters:
  issue:
    type: integer
    description: Issue number to triage
    required: true
  dry_run:
    type: boolean
    description: Print triage plan without applying labels or posting comments
    default: true
---

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
