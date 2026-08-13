---
name: i18n-sync
description: Add or sync i18n translation keys across all locale files (EN + TH) in any monorepo with parallel locale JSON (next-intl, i18next, React Native). Detects missing/orphan keys, keeps EN/TH in lockstep, and fills Thai translations. Trigger when the user types /i18n-sync, asks to "add a translation / เพิ่มคำแปล / sync i18n / ใส่ภาษา / แปล key", or edits locale files and risks leaving a locale out of sync.
---

# /i18n-sync — keep locale files in lockstep

Adding a UI string means touching **every** locale file or the app throws a missing-key warning. This skill does it once, correctly, in EN + TH.

## Locate the locale files first
Don't assume — discover per app, because web and mobile differ:
1. **Web (Next.js / next-intl):** typically `messages/en.json` + `messages/th.json` (nested namespaces).
2. **Mobile (React Native):** grep for `i18n`, `translations`, `locales/` under the mobile app — structure may be flat or per-namespace.
3. **Shared strings:** check any `packages/shared` for cross-app message constants.

If the layout differs, glob for `**/messages/*.json`, `**/locales/*.json`, or `en.json`/`th.json` pairs and infer the convention from what exists.

## Procedure
1. **Read every locale file in the target app** so you see the real key tree and namespace style.
2. **Place the new key** in the namespace that matches sibling keys (don't invent a new top-level namespace unless asked).
3. **Write all locales together** — EN (technical/source) and TH. For TH use natural business Thai, not literal machine translation.
4. **Keep key order identical** across locale files so diffs stay reviewable.
5. **Report** the keys added and any pre-existing drift you noticed.

## Audit mode (when asked "are translations in sync?")
- Diff the key sets of each locale pair. List: keys in EN missing from TH (and vice-versa), and orphan keys not referenced in code (grep the key string).
- Output a table: `key | en | th | status (missing-th / orphan / ok)`.

## Gotchas
- ⚠️ Thai text in JSON must stay UTF-8 — never let an editor save as cp1252 (the classic Windows trap).
- next-intl keys are referenced as `t('namespace.key')` — when adding, grep the namespace to confirm it exists before nesting.
- Don't reorder or reformat unrelated keys; minimise the diff.
