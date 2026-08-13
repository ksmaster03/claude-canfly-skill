---
name: prisma-migrate-safe
description: Change a Prisma schema and produce a migration safely — review the generated SQL, guard against destructive data loss, and ensure the migration is git-tracked so it actually ships. For any Prisma project. Trigger when the user types /prisma-migrate-safe or asks to "change the schema / add a column / add a table / เพิ่มฟิลด์ / แก้ schema / prisma migrate / new migration".
---

# /prisma-migrate-safe — schema change that won't blow up prod

Prisma migrations have one infamous failure mode: an un-git-added `migration.sql` never reaches the prod box, and `prisma migrate deploy` silently no-ops it. This skill prevents that and the destructive-change traps.

## Locate
- Glob `**/prisma/schema.prisma`; migrations sit beside it in `prisma/migrations/`.
- In a monorepo the schema usually lives under the API package (e.g. `apps/api/prisma/`) — glob rather than guess.

## Procedure
1. **Edit `schema.prisma`** — make the model change. Match existing field naming, relations, and `@map`/`@@map` conventions already in the file.
2. **Generate the migration** from the dir holding `prisma/`:
   `npx prisma migrate dev --name <verb_noun>` (e.g. `add_status_to_asset`).
3. **READ the generated `migration.sql` before trusting it.** Confirm it does what you intended and nothing more.
4. **Destructive-change gate** 🔴 — if the SQL contains `DROP COLUMN`, `DROP TABLE`, a type change that truncates, or a new `NOT NULL` column without a default on a populated table: STOP. Surface it, propose a safe path (add nullable → backfill → enforce), and get the user's OK before continuing.
5. **`git add prisma/migrations/`** — the new folder + `migration.sql` MUST be staged. This is the #1 reason a migration "didn't run" in prod.
6. **Regenerate client** if needed: `npx prisma generate`. Typecheck: `npx tsc --noEmit`.
7. **Prod**: do NOT run migrate against prod by hand. Let it ship through your normal deploy path (`prisma migrate deploy` runs on the box).

## Output
Report: schema diff summary, the migration name, the SQL verdict (safe / destructive-needs-plan), and confirmation that migrations are git-tracked.

## Hard rules
- ⚠️ Never edit an already-applied migration file — create a new one.
- ⚠️ Never `migrate reset` against anything with real data.
- cwd discipline: background shells may start in the wrong repo — verify `git rev-parse --show-toplevel` before `git add`.
