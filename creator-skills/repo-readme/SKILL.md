---
name: repo-readme
description: Create or refresh a project's GitHub face — bilingual README (README.md English + README.th.md Thai, cross-linked), a hero illustration generated with chatgpt-bridge, and the GitHub repo itself if it does not exist. Called by /handoff on every run; also trigger on /repo-readme or "สร้าง repo ใหม่บน github / เขียน readme 2 ภาษา / ทำภาพประกอบ readme / อัปเดต readme".
---

# /repo-readme — bilingual README + hero image + GitHub repo

Makes a project presentable and resumable on GitHub. Three parts; each is skipped when already up to date.

## Input (optional)
- `repo` = `owner/name` (default: existing `origin`, else `ksmaster03/<folder-name>`)
- `visibility` = `private` | `public` (default **private**)
- `image-concept` = one line describing the picture (default: derive from what the project is)
- `no-image` to skip the illustration

## 0. Decide what is needed
```bash
cd <repo> && git remote -v && git status -sb
ls README.md README.th.md docs/*-hero.* 2>/dev/null
```
| State | Do |
|---|---|
| No README or only a stub (`bun init` / framework default) | Write both files + image |
| README exists in one language | Add the other language, keep existing content |
| Both exist | **Update only what changed this session**: commands, API, numbers, limitations. Do not rewrite prose that is still true |
| Hero image exists | Keep it. Regenerate only if the user asks or the project's purpose changed |

`origin` is not always GitHub (DockSync is Azure DevOps). If `origin` points elsewhere, write the README and image but do **not** create a GitHub repo unless the user asked for one.

## 1. README (two files, cross-linked)
- `README.md` = English. First line under the title: `**English** · [ภาษาไทย](README.th.md)`
- `README.th.md` = Thai. First line: `[English](README.md) · **ภาษาไทย**`
- Same sections, same order, same facts in both. Write each natively; do not machine-translate sentence by sentence.
- Hero image directly under the language switcher: `![alt](docs/<name>-hero.jpg)`

Section order (drop any that do not apply):
1. One-paragraph what and why
2. What it does (short list)
3. Quick start: commands that were **actually run this session**
4. Usage / API table
5. How it works (only the non-obvious design decisions)
6. Results or benchmarks, with the command that reproduces them
7. Known limitations
8. License (only if a LICENSE file exists)

Rules:
- **Every number must come from a command run in this session.** If it was not re-measured, leave it out or mark the date measured.
- No secrets, account ids, internal hostnames, customer names. Eval/sample data must be synthetic.
- Thai text: plain natural Thai, no em dash, no emoji on marketing-style pages, technical terms stay in English.
- Write files with python `io.open(..., encoding='utf-8', newline='\n')` or the Write tool. Never pipe Thai through a shell argument.

## 2. Hero illustration (chatgpt-bridge)
```bash
mkdir -p <repo>/docs
cd $PROJECTS/chatgpt-bridge
node chatgpt-img.mjs "<ASCII-only English prompt>" "$PROJECTS/<repo>/docs/<name>-hero.png"
```
- Run it in the background (takes 1 to 3 minutes) and keep working. **One run at a time**: the browser profile in `chatgpt-data/` is locked while a run is active.
- **Prompt must be ASCII only**. Git Bash turns non-ASCII arguments into `?????` and still exits 0.
- Ask for `wide 16:9 landscape banner`, a named style and palette, and end with `Absolutely no text, no letters, no logos, no watermark.` Generated Thai lettering is unreliable; put words in the README, not in the picture.
- If the first run opens a login window, tell the user: it needs their ChatGPT session once.
- **Look at the result with the Read tool before committing.** Reject images with stray text, extra limbs, or a concept that does not match the project.
- Shrink before commit (ChatGPT PNGs are about 2 MB):
  `ffmpeg -y -i docs/<name>-hero.png -vf "scale=1600:-2" -q:v 3 docs/<name>-hero.jpg` then delete the PNG. Target under 400 KB.
- If chatgpt-bridge fails twice (bot check, DOM change), stop retrying: ship the README without the image and say so.

## 3. GitHub repo
Security gate first, same as /handoff: `.gitignore` covers `.env*`, keys, `node_modules/`, data dirs; after staging check `git status --porcelain` and `git ls-files` for secrets; grep staged files for `AKIA`, `BEGIN PRIVATE KEY`, `sk-`, `sm_`, `password=`.
```bash
git add <explicit paths>          # never git add -A / git add .
git commit -F <message-file>      # message via file if it contains Thai
gh repo create <owner>/<name> --private --source . --remote origin --description "<ASCII one-liner>"
git push -u origin <branch>
gh repo edit <owner>/<name> --add-topic <topic> ...
```
- Default **private**. Tell the user the one command to flip it: `gh repo edit <owner>/<name> --visibility public --accept-visibility-change-consequences`.
- **No `Co-Authored-By: Claude` trailer** on public repos, and none on a private repo that is likely to go public (anything with a bilingual README and a hero image usually is).
- Existing repo: just commit the README/image changes and push. Never force-push.
- Verify: `git rev-parse HEAD` equals `git rev-parse origin/<branch>`; `gh repo view --json url,visibility`.

## Report
Repo URL · visibility · commit hash · which README sections changed · image path and size (or why there is none) · anything left uncommitted on purpose.

## Anti-patterns
- Rewriting the whole README on every handoff. Update the facts that changed.
- Copying numbers from memory or an older README without re-running the command.
- Publishing as public by default.
- Committing the 2 MB PNG instead of the compressed JPG.
- Thai or any non-ASCII text inside the image prompt argument.
