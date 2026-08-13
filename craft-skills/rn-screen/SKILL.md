---
name: rn-screen
description: Scaffold a new React Native screen following the conventions already in the app (navigation registration, screen structure, shared components, types, i18n) instead of inventing a new structure. Trigger when the user types /rn-screen or asks to "add a screen / สร้างหน้าจอ / new RN screen / เพิ่มหน้า mobile / add a page to the app" in a React Native project.
---

# /rn-screen — add an RN screen the way this app already does it

The fastest way to a screen that doesn't look bolted on: read two existing screens first, then copy their shape exactly. This skill enforces that order.

## Input
Screen name + purpose. Optionally: route params, data source (API hook), whether it's in a tab or stack.

## Discover conventions BEFORE writing
Open 1–2 existing screens in the target app and copy their shape:
1. **Navigation**: how screens register (stack/tab navigator file), route name constants, param typing (`RootStackParamList` or similar).
2. **Screen file layout**: folder per screen vs flat, `styles` location, component split.
3. **Data**: how screens fetch (hooks/services), loading & error states.
4. **Shared UI**: reuse existing components (buttons, headers, list rows) — don't rebuild them.
5. **i18n**: how strings are referenced (then add keys via **/i18n-sync**).

## Procedure
1. Create the screen file(s) in the same place/shape as siblings.
2. Type the route + params in the navigator's param list.
3. Register the screen in the navigator.
4. Wire data the same way existing screens do; include loading/empty/error states.
5. Reuse shared components and the app's theme/spacing tokens.
6. Add user-facing strings as i18n keys (EN + TH) via **/i18n-sync**.
7. Typecheck (`npx tsc --noEmit`).

## Gotchas
- ⚠️ If the mobile app is intentionally excluded from the monorepo workspace (flat `npm install` + minimal `metro.config`), don't add workspace-style imports — they break the standalone build. Check before importing across packages.
- Match the surrounding files' comment language convention.
- Test on a real device/emulator before calling it done — a screen that compiles is not a screen that works.

## Done = screen renders + navigable + typed + i18n keys added + reuses existing components. Report files created + tsc result.
