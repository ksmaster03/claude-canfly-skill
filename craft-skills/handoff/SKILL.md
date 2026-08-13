---
name: handoff
description: End-of-session handoff — persist what happened into the user's memory directory AND push the project's code to GitHub, so the work can be resumed later (by a future session, another machine, or another person). Runs the two halves in parallel via subagents. Trigger when the user types /handoff or asks to "handoff / wrap up / save my work / save progress / จบงาน / บันทึกงาน(ความทรงจำ) + push/upload code ขึ้น github / เก็บงานวันนี้".
---

# /handoff — save memory + upload code to GitHub

Two independent jobs that together make work resumable:
- **A. Save memory** — durable project state + resume points into the memory dir
- **B. Push code** — latest code onto GitHub, with a hard secrets gate

Do **both** unless the user scopes it (`/handoff memory-only` or `/handoff push-only`). The two halves are independent → **launch them as two subagents in parallel** (one general-purpose for memory, one for the git push), then synthesise a handoff summary. Doing it via subagents keeps the main context clean and runs both at once.

## Input (optional args)
- a one-line "what shipped / what changed" note (used for the commit message AND the memory hook). If omitted, derive from `git diff --stat HEAD` / the session's work.
- `repo` = `owner/name` (default: existing `origin`, else `<your-github-user>/<folder-name>`)
- `visibility` = `private` | `public` (default **private**)
- `memory-only` / `push-only` to run just one half.

First: identify **which project** this is (default = cwd / the project just worked on) and **its GitHub repo** and **its memory file**. State these back in one line before acting.

---

## Part A — Save memory  (subagent: general-purpose)

**Target the ACTIVE session's memory directory** — the folder holding the `MEMORY.md` that is auto-loaded into context. That is `~/.claude/projects/<slug>/memory/`, where `<slug>` encodes the session launch cwd (e.g. a session started in `D:\Project\acme` becomes `d--Project-acme`). Some projects keep their OWN memory dir rather than sharing one. If unsure which, `Glob ~/.claude/projects/*/memory/MEMORY.md` and pick the index that already mentions this project; if still ambiguous, ask.

**Capture ONLY durable facts** (things a future session can't re-derive from the code/git/CLAUDE.md):
- project status + what's LIVE (URLs, infra, accounts/ids)
- **resume points** — what's done, what's next, what's blocked and on whom
- key decisions + **why** (the road not taken matters)
- gotchas discovered this session (the thing that cost time)
- external identifiers (repo URL, AWS account, domain, dashboards, tickets)

**Do NOT save**: in-progress code detail, anything already in the repo/git history/CLAUDE.md, or conversation-only context. That's churn.

**Format (strict — one fact per file):**
```
---
name: <kebab-slug == filename without .md>
description: <one-line, used for recall>
metadata:
  type: project | reference | feedback | user
---

<the fact. For project/feedback add **Why:** and **How to apply:** lines. Convert relative dates to absolute. Link related memories with [[their-name]].>
```
- **Update the existing file in place** if one already covers this project — do NOT create a duplicate; delete memories that turned out wrong.
- Add/refresh **one line** in `MEMORY.md` (`- [Title](file.md) — hook`). MEMORY.md is an index only — never put content there.

Give the subagent the actual facts to write (don't make it re-investigate). Have it report which files it created vs updated and the exact MEMORY.md line(s).

---

## Part B — Push code to GitHub  (subagent: general-purpose)

### 🔒 SECURITY GATE — runs before any commit (non-negotiable)
1. Ensure a `.gitignore` exists at the repo root and excludes secrets:
   `*.env` / `.env*`, `*.pem`, `*.key`, `*accessKeys*.csv`, credential `*.csv`, `node_modules/`, build dirs (`.next/`, `dist/`, `build/`), `src/generated/`, secret JSON. Add missing lines BEFORE `git add`.
2. After staging, run **`git status --porcelain`** AND **`git ls-files`**. If any `.env`, key, `*.pem`, `*accessKeys*.csv` or other credential file appears → **ABORT**, unstage, report. Do not commit.
3. Grep staged text files for obvious secrets (`AKIA`, `BEGIN PRIVATE KEY`, `aws_secret`, `password=`, long base64 tokens). Any hit → stop and report.

### Push
Windows: `git` + `gh` are installed; the user is authenticated to GitHub (`gh auth status`). Use Bash (Git Bash) or PowerShell.
1. `git init` if needed; `git branch -M main`.
2. Remote: if `origin` exists, use it. Else create the repo:
   `gh repo create <owner>/<name> --private --source . --remote origin`
   (default **private** — the code often references AWS account ids / infra; the user can flip to public later with `gh repo edit --visibility public`).
3. If there's nothing to commit (`git status --porcelain` empty), say so and skip — don't make empty commits.
4. Commit (explicit paths or `-A` only AFTER the gate passes). Message = the "what shipped" note (or derive from `git diff --stat`), then end with the harness's required co-author line, e.g.:
   `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
5. `git push -u origin main`. If the remote has diverged / is ahead → **report the conflict, do NOT force-push** without asking.
6. **Verify**: push succeeded, and `git ls-files` contains NO secret file. Report repo URL + branch + commit hash + visibility.

---

## Part C — Handoff summary (you, after both subagents return)
Output a tight wrap-up:
- **Memory**: files created/updated + the MEMORY.md line(s)
- **Code**: repo URL · commit hash · visibility · confirmation secrets stayed out
- **Resume points**: 2–5 bullets a future session can act on immediately (what's next / what's blocked)
- Any flag the user must act on (e.g. repo is public, remote diverged, AWS verify pending)

## Anti-patterns
- ❌ Pushing before the security gate, or committing `*.env` / an access-key `*.csv`. This has fired for real — an `*accessKeys*.csv` sitting in the repo folder was caught only by the gate. A leaked AWS key = real incident.
- ❌ `git push --force` to "fix" a diverged remote without asking.
- ❌ Defaulting a new repo to **public** when the code carries account ids / infra detail.
- ❌ Saving routine churn or in-progress code to memory — capture decisions, resume points, gotchas, not a changelog.
- ❌ Writing to the wrong project's memory dir — use the ACTIVE session's `…/memory/`.
- ❌ Running both halves serially in the main context when they're independent — fan them out as parallel subagents.

## Why this skill exists
A "handoff" makes work survivable. The user runs 50+ projects; sessions get summarized/reset and machines change. Two things make any project resumable: (1) the **memory** that records why/where/what-next, and (2) the **code on GitHub**. This skill does both every time, with the secrets gate that a tired end-of-day push tends to skip. Pattern proven this session: parallel memory-subagent + security-gated git-push subagent.
