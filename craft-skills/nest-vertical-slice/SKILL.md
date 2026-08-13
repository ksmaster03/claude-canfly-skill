---
name: nest-vertical-slice
description: Scaffold a complete NestJS feature slice (module + controller + service + DTOs, wired into the app) following the conventions already present in the repo, optionally with a Prisma model. Trigger when the user types /nest-vertical-slice or asks to "add an endpoint / สร้าง API / add a NestJS module / เพิ่ม resource / new CRUD" in a NestJS project.
---

# /nest-vertical-slice — add a NestJS feature the way this repo already does it

Builds a new feature end-to-end matching the patterns already in the repo's `src/` — pick the closest existing module as your reference (controller + service + `dto/`).

## Input
Feature name + what it does. Optionally: fields/model, auth requirement, whether it needs a Prisma table.

## Discover conventions BEFORE writing
1. Open an existing slice (e.g. `src/<some-feature>/` + its `dto/`) and copy its shape: decorators, validation style (`class-validator`), service injection, error handling, response shape.
2. Check how modules register (`app.module.ts` imports) and how auth guards / RBAC are applied — match whatever the repo already does.
3. Check any shared package for types/enums to reuse instead of redefining.

## Procedure
1. Create `src/<feature>/`:
   - `<feature>.module.ts`, `<feature>.controller.ts`, `<feature>.service.ts`
   - `dto/create-<feature>.dto.ts`, `dto/update-<feature>.dto.ts` with `class-validator` decorators
2. If a DB table is needed → hand off the schema change to **`/prisma-migrate-safe`** (do not hand-edit migrations here).
3. Register the module in `app.module.ts`. Apply the same guards/decorators as sibling modules.
4. Use Prisma service the same way existing services do (constructor injection).
5. Add i18n keys for any user-facing strings via **/i18n-sync**.
6. `npx tsc --noEmit` (or the repo's typecheck script) to prove it compiles.

## Conventions to honour
- Comments: match the surrounding file's language convention (this author uses Thai for business logic, English for technical).
- Match the surrounding code's naming/idiom; don't introduce a new style.
- Don't add libraries the repo doesn't already use.

## Done = compiles + registered + DTOs validated + i18n keys added. Report the files created and the tsc result.
