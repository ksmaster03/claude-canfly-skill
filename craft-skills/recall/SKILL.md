---
name: recall
description: Fast semantic-ish retrieval across the user's memory directory using Grep + Read. Trigger when the user types /recall, /remember, or asks "what did I know about X / did we decide Y / how do I do Z" where X/Y/Z is plausibly something stored in memory. Cheaper and faster than rereading MEMORY.md cover-to-cover.
---

# /recall — search the memory dir without burning context

The user's memory lives under `~/.claude/projects/<slug>/memory/` (the folder holding the `MEMORY.md` that is auto-loaded each session; `<slug>` encodes the session launch cwd). `MEMORY.md` is the index and individual `*.md` files hold details. When the user wants to retrieve something specific, **do not** ask me to recite MEMORY.md — search across the dir directly.

> If you don't know the slug, `Glob ~/.claude/projects/*/memory/MEMORY.md` once and use the match.

## Input

The user's query — natural language. May be Thai or English. Examples:
- `/recall fleet warranty`
- `/recall how do we deploy the api`
- `/recall the cwd discipline thing`
- `/recall that client's spec details`

## Procedure

### 1. Tokenize the query

Extract 2-4 keywords. Drop stopwords (the/a/how/do/we/มัน/ของ/แบบ). Keep proper nouns, project names, tech names. If the query contains a project name, include it as one of the keywords — project names are the highest-signal token in a memory dir.

### 2. Grep the memory dir

Use the **Grep tool**, `path` = the memory dir resolved above, `output_mode: "files_with_matches"`, case-insensitive. Try the most distinctive keyword first; if it returns 0 files, try the second.

If 0 files match the first single keyword, **stop and tell the user** — don't hallucinate. Suggest 2-3 alternative spellings or related terms they might have meant.

### 3. Read only the matches

For each matching file (cap at 4 files), Read with `limit: 80` first to skim. If the relevant snippet is clearly past line 80, do a second targeted Read with an `offset`.

### 4. Synthesise — never copy verbatim

Reply in 3 parts:

1. **Direct answer** (1-3 sentences) — the fact, not the prose around it
2. **Source** — `[file.md](relative/path)` link so the user can verify
3. **Related links** — if you saw `[[wikilink]]` references in the file, mention which 1-2 are most likely to also be relevant (do NOT pre-emptively load them; let the user say "expand")

Keep the whole reply ≤ 12 lines. The point of this skill is to be **cheaper than re-reading MEMORY.md** — if you write a long essay you've defeated it.

### 5. If the answer isn't there

If Grep matches a file but reading it doesn't actually answer the question, say so honestly:

> Found `project_X.md` mentioning that term but it's about a different aspect (Y, not Z). MEMORY.md doesn't seem to have what you asked for — want me to save it now?

This is the natural moment to capture a new memory.

## Anti-patterns

- ❌ Re-stating the whole MEMORY.md hook line ("yes you have a memory called X")
- ❌ Loading 5+ files "to be thorough" — that's exactly what this skill exists to avoid
- ❌ Quoting long paragraphs from the source file — synthesise the answer instead
- ❌ Inventing details that "should be there" — only repeat what Grep + Read actually showed

## Why this skill exists

The user is on a token budget and works across 5+ sibling projects with ~25 memory files. Re-reading MEMORY.md every time costs ~600 tokens; reading a wrong file costs another ~500-2000. Grep-first retrieval typically lands in ~1 file × 80 lines = ~400 tokens — a clear win when the user already knows roughly what they're after.
