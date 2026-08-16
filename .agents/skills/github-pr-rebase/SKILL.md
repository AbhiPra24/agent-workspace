---
name: github-pr-rebase
description: >-
  Rebases current branch or PR on top of target base branch, resolves merge conflicts,
  maintains clean linear history, and safely pushes with lease verification using
  direct git and gh CLI bash commands.
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
