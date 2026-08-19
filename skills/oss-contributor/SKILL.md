---
name: oss-contributor
description: >-
  Universal open-source contribution engine for any GitHub repository across all
  languages and stacks. Traverses open issues, evaluates reproduction feasibility,
  strictly enforces repository CONTRIBUTING.md rules and PR templates, executes
  targeted fixes with local test/linter verification, and automates PR submission.
  Trigger with `/contribute [repo_or_issue_url]` or `/contribute find [repo]`.
parameters:
  repo:
    type: string
    description: Target repository in "owner/repo" or full GitHub URL format
    required: true
  issue:
    type: string
    description: Specific issue number or URL to solve (optional)
    required: false
  mode:
    type: string
    description: Operation mode - "solve" (fix specific issue) or "scan" (traverse and find best issues)
    default: solve
---

# Universal Open-Source Contributor Skill (`oss-contributor`)

An extensible, language-agnostic engine designed to traverse **any public repository on GitHub**, discover solvable issues, enforce repository governance (`CONTRIBUTING.md`), and produce verified, production-ready Pull Requests.

---

## 🎯 Universal Principles of OSS Contribution

1. **Governance First (`CONTRIBUTING.md`)**:
   Every repository has unique rules. Always inspect `CONTRIBUTING.md`, `.github/CONTRIBUTING.md`, `DEVELOPMENT.md`, and PR templates before writing a single line of code.
2. **Precision & Non-Invasive Diffs**:
   Only touch lines directly related to the issue. Never reformat entire files or modify unrelated formatting/dependencies.
3. **Verification Before Assertion**:
   Never submit code without executing and passing the repository's native test suites, type-checkers, and linters.
4. **PR Checklist & Template Fidelity**:
   Automated bots reject PRs that omit required checklist headers or checkboxes. Maintain 100% compliance with `.github/PULL_REQUEST_TEMPLATE.md`.

---

## 🔍 Phase 1: Repository & Issue Traversal (Any Repo)

When given any repository (or using `mode: scan`), execute automated issue discovery:

```bash
# 1. Fetch top candidate issues filtered by actionable labels
gh issue list \
  --repo <owner>/<repo> \
  --state open \
  --limit 30 \
  --json number,title,labels,comments,assignees,createdAt \
  --jq '.[] | select((.assignees | length) == 0) | {number, title, labels: [.labels[].name], comments}'
```

### Issue Quality Filter Heuristics:
* ✅ **High Value / High Merge Rate**:
  * Unassigned issues with labels: `help wanted`, `good first issue`, `bug`, `documentation`, `a11y`, `types`, `dx`.
  * Issues with clear reproduction steps or maintainer confirmation ("PRs welcome" / "Accepting PRs").
* ⚠️ **Avoid / Reject**:
  * Issues already assigned to active contributors.
  * Architectural changes requiring design RFCs without prior maintainer consensus.
  * `first-timers-only` issues that explicitly require maintainer reservation comments before starting.

---

## 📜 Phase 2: Dynamic Governance & Environment Inspection

Inspect repository contribution rules dynamically:

```bash
# Locate all governance, contribution, and template docs
find . -maxdepth 3 \( -iname "*contribut*" -o -iname "*development*" -o -iname "*pull_request_template*" -o -iname "*readme*" \)
```

### Checklist to Extract:
| Rule | What to Check | Command / File |
| :--- | :--- | :--- |
| **Base Branch** | `main`, `master`, `dev`, `develop`, or `canary` | `git remote show origin` or `CONTRIBUTING.md` |
| **Commit Standard** | Conventional Commits (`fix:`, `feat:`), Scope requirements | `git log -n 5 --oneline` |
| **DCO / Signing** | Signed-off-by required? GPG signing required? | Look for `Signed-off-by` in recent commits (`git log -n 5`) |
| **CLA Requirement** | Microsoft, Google, Linux Foundation, or EasyCLA | `CONTRIBUTING.md` |
| **PR Checklist** | Mandatory Markdown checkboxes (`- [x]`) | `.github/PULL_REQUEST_TEMPLATE.md` |

---

## ⚙️ Phase 3: Setup & Shallow Forking

Conserve disk space and network bandwidth on large codebases by using depth-limited clones:

```bash
# 1. Fork and shallow clone
gh repo fork <owner>/<repo> --clone=true -- --depth=1

# 2. Enter repository and create a descriptive branch
cd <repo_name>
git checkout -b <type>/<concise-issue-description>
```

---

## 🛠 Phase 4: Universal Language & Stack Verification Matrix

Before writing or submitting fixes, identify the tech stack and its verification commands:

| Ecosystem | Setup / Install | Test Command | Linter / Formatter | Type Checker |
| :--- | :--- | :--- | :--- | :--- |
| **Node.js / TS** | `pnpm i` / `npm i` / `bun i` | `npm test` / `pnpm test` | `npm run lint` / `eslint` | `npm run test:types` / `tsc` |
| **Python** | `pip install -e .` / `poetry install` | `pytest` / `python -m unittest` | `ruff check .` / `flake8` | `mypy .` / `pyright` |
| **Go** | `go mod download` | `go test ./...` | `golangci-lint run` | `go vet ./...` |
| **Rust** | `cargo check` | `cargo test` | `cargo clippy` / `cargo fmt` | Built into `cargo check` |
| **Java / Kotlin** | `./gradlew build` / `mvn compile` | `./gradlew test` / `mvn test` | `./gradlew checkstyle` | Compiler verification |
| **C / C++** | `cmake -B build` / `make` | `ctest` / `make test` | `clang-format -i` | Compiler verification |
| **Ruby** | `bundle install` | `bundle exec rspec` | `bundle exec rubocop` | `sorbet` (if present) |

---

## 🎯 Phase 5: Domain-Specific Fix Patterns

### 1. Web Accessibility (A11y)
* Ensure keyboard navigation (`Enter`, `Space`, `Tab`, `Arrow keys`).
* Verify ARIA landmarks and states (`role="button"`, `role="tab"`, `aria-expanded`, `aria-selected`, `aria-controls`).
* Always provide accessible text for visual-only indicators:
  ```tsx
  <span role="status" className="sr-only">Loading</span>
  ```

### 2. TypeScript / Typings
* Maintain strong typing without resorting to `any`.
* Keep generics intact across request/reply interfaces.
* Validate with TypeScript assertion suites (e.g. `tstyche`, `dtslint`).

### 3. API & Backend Logic
* Handle edge cases: null/undefined inputs, empty collections, timeouts, boundary numbers.
* Preserve backward compatibility for public method signatures.

### 4. Docs, Links & Curriculum
* Verify that all added or modified links return HTTP 200 and point to canonical resources.
* Ensure code snippets in markdown are syntax-highlighted and executable.

---

## 🚀 Phase 6: Commit, Push & PR Submission

### 1. Verify Git Status & Diff
```bash
# Check for stray or untracked files
git status --short
# Verify exact changes
git diff --stat
```

### 2. Commit with Proper Formatting
```bash
# Standard Conventional Commit
git commit -m "<type>(<scope>): <concise message> (#<issue_number>)"

# If DCO sign-off is required by CONTRIBUTING.md:
git commit -s -m "<type>(<scope>): <concise message> (#<issue_number>)"
```

### 3. Push and Open Pull Request
```bash
# Push branch to personal fork
git push -u origin <branch_name>

# Create PR matching the repo's template and checklist
gh pr create \
  --repo <owner>/<repo> \
  --head <your_username>:<branch_name> \
  --base <base_branch> \
  --title "<type>(<scope>): <concise title>" \
  --body "$(cat << 'PR_EOF'
Fixes #<issue_number>

### Summary of Changes
- <concise bullet point 1>
- <concise bullet point 2>

### Checklist
- [x] I have read and followed the repository's CONTRIBUTING guidelines.
- [x] All automated tests pass locally.
- [x] Linters and formatters passed with zero warnings.
PR_EOF
)"
```

---

## 📊 Phase 7: Post-PR Monitoring & Tracking

1. **Check CI Rollup & Bot Comments**:
   ```bash
   gh pr view <pr_number> --repo <owner>/<repo> --json statusCheckRollup,comments
   ```
2. **Handle Automated Bot Prompts**:
   * If a CLA prompt appears (e.g., Microsoft, Google, Linux Foundation), post the required agreement reply immediately.
3. **Log to Central Tracker**:
   * Update `/Users/abhipra/Developer/Github/CONTRIBUTIONS.md` with PR link, issue, and status.

---

## 🛡️ Anti-Patterns & Rejection Traps

| Trap | Failure Mode | Remedy |
| :--- | :--- | :--- |
| **Skipping PR Checklists** | Triage bots instantly close PRs that lack required checklist boxes (e.g. FreeCodeCamp). | Always inspect `.github/PULL_REQUEST_TEMPLATE.md` and include all checkboxes marked `[x]`. |
| **Large Unformatted Diffs** | Modifying entire files with prettier or changing line endings (`CRLF` vs `LF`). | Configure git to preserve repo formatting; check `git diff --stat` before committing. |
| **Unsigned CLA** | PRs cannot be merged without signed Contributor License Agreement. | Check PR comments immediately and reply with sign-off. |
| **Untested Code** | Pushing broken code breaks CI and creates negative maintainer impression. | Always execute the project's native test runner before pushing. |
