---
name: github-pr-rebase
description: >-
  Rebases current branch or PR on top of target base branch, resolves merge conflicts,
  maintains clean linear history, and safely pushes with lease verification.
  Trigger with `/pr-rebase [base_branch]`.
parameters:
  base:
    type: string
    description: Target base branch to rebase onto (default: origin/main or origin/master)
    default: origin/main
  interactive:
    type: boolean
    description: Whether to squash/fixup commits interactively
    default: false
---

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
