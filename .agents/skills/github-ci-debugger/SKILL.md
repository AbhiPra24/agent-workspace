---
name: github-ci-debugger
description: >-
  Inspects GitHub Actions workflow runs, downloads and parses failed job logs,
  extracts root cause stack traces, and suggests targeted code patches.
  Trigger with `/ci-debug [run_id_or_branch]`.
parameters:
  run_id:
    type: string
    description: GitHub Actions workflow run ID (or branch name to find latest run)
    required: false
---

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
