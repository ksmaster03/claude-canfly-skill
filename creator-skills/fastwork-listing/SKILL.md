---
name: fastwork-listing
description: Build a Fastwork freelancer presence. fastwork.com (new platform, Oct 2026) - profile, show reel video, portfolio posts and services via claude-in-chrome on the user's logged-in Chrome. seller.fastwork.co (legacy) - service listings via Playwright CDP. Trigger when the user asks to "อัปเดตโปรไฟล์ fastwork / ลงงานใน fastwork / เพิ่มงาน fastwork / add post / add service / show reel fastwork / แก้ไข listing fastwork" or gives a fastwork.com or fastwork.co URL.
---

# fastwork.com (new platform, since Oct 2026) — use THIS first

Fastwork moved to **fastwork.com**. Old fastwork.co profiles and listings do **not** carry over (old URLs bounce to the home page). Everything below was run for real on 16-17 Oct 2026.

**Driver:** the claude-in-chrome extension on the user's own Chrome, which is already logged in to fastwork.com. Do not use the Playwright profile below for fastwork.com (its launcher closed itself on every run, and `check.js` calls `browser.close()`, which kills a CDP browser).

**Language:** ask once; this user wants every profile/post/service text in **English** (check Thai is gone with a U+0E00 to U+0E7F regex).

**UI is Svelte.** Rules that cost real turns:
- Set inputs/textareas with the native value setter + `input` event (`Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set`), then verify `.value`.
- Typeahead fields (company, school, skills, tags) drop a JS-set value on blur: pick the option. Options are `[role=option]`, label in `.sb-text`; when nothing matches, the last option is `Create "..."` or `Add "..."` (JS click works on those).
- Some controls ignore JS clicks and need a real mouse click: the language picker option, the circle checkbox on posts inside "Add media".
- Tag search sometimes returns nothing on the first query (dropdown still loading): retry 3-4 times with an empty value in between.
- Month/Year dropdowns are `button[aria-label="Start Month"]` etc.; clicking an already-open one closes it. Education and certificates **require a month and a year** — do not invent them, ask the user.
- `javascript_tool` results that look like query strings or JWTs come back `[BLOCKED ...]`; return booleans/counts instead.
- `file_upload` (claude-in-chrome) accepts **at most 10 MB per call**. Videos bigger than that: 2-pass encode under 10 MB (`-b:v 690k` for a 95 s 1080p motion-graphics clip gave 9.5 MB and readable text) — Fastwork itself accepts up to 1.5 GB.
- Never `find` "file input" and click it — use `find` to get the ref, then `file_upload`.

**Profile** (`/user/<handle>`): Edit name / bio (250 chars, one line) / role / location (city typeahead) / skills (ESCO tag library, `Create "..."` allowed) / avatar (click the avatar circle → `Update avatar` dialog → file input → crop → Save). About tab: Work experience (role, company typeahead, current checkbox, months/years, description 2000), Education, Certificates, Languages (Native or bilingual / Professional / ...). The header "+ Claim" username button sits right next to "Edit bio" — easy to hit by mistake; claiming needs 4 invited friends.

**Show reel:** pencil "Edit cover" on the reel → Video → upload into the dialog's file input → the new clip is auto-selected → Save → "Choose a thumbnail": drag the frame picker (≈3.8 px per second on a 95 s clip) to a frame with the person's face/name → Save. Old videos stay in the library unselected. Verify with `document.querySelectorAll('video')[0].duration` after reload.

**Posts** (Add → Post): Add media opens "Select media" → `file_upload` into its input; uploads are auto-selected **in completion order**, and #1 is the cover — upload the cover file alone first, then the rest. Caption textarea placeholder `Adding a caption for this post` (2000). Add tags (3-5). Post. Newest post shows first, so post the strongest last. Post menu (… → Edit / Pin up to 3 / Delete). Check tags are factually right (e.g. which BI tool) — edit via … → Edit → Add tags → remove chip `button[aria-label="Remove <tag>"]`.

**Services** (Add → Service): name, description (2000), price (leave empty = **Price on request**; do not invent prices), unit (Not specified / Project / Hour / Day / Session), Add package (name, optional description 5000, price, unit; preview shows "From ฿X"). Media: Browse → Post tab → select whole posts (real mouse click on the circle) → this also **links those posts** to the service. Tags. Publish. Newest service shows first.

**Before publishing anything public:** client screenshots only as pixelated copies (logos, company names, person names); leave out anything from production with real people, unsubmitted tenders, or confidential footers.

# seller.fastwork.co (legacy) — original procedure below

# /fastwork-listing — create or edit a Fastwork seller listing

Fastwork has no public API. Everything here is browser automation over CDP against the seller's own
logged-in session — same pattern as `chatgpt-bridge` / `suno-bridge`. Built and hardened across two
real listings on 2026-08-30 (an AI-music-course gig, then a Claude Code training-for-enterprise gig).
Every gotcha below cost real turns to discover — read this before improvising new selectors.

## One-time setup (per machine, persists across sessions)

- Browser profile: `$WORK/tmp\pw-fastwork-profile` — once the user logs in here, the session persists.
  **Never ask for the password** — launch the browser and let the user log in themselves in the window.
- Debug port: `9224` (arbitrary but consistent — reuse it so `scripts/check.js` finds the same instance).
- Helpers: `scripts/fw-lib.js` — `require()` this from any one-off driver script instead of re-deriving
  Playwright boilerplate. `scripts/launch.js` and `scripts/check.js` are ready-to-run entry points.
- Every script in this skill needs the borrowed Playwright install:
  ```bash
  NODE_PATH="$APPDATA/npm/node_modules/@playwright/mcp/node_modules" node <script>.js
  ```
  (There's no standalone `playwright` package on this box — it's bundled inside the global
  `@playwright/mcp` install. Do NOT run `npx playwright install`, it'll try to fetch a chromium
  revision that isn't needed; `fw-lib.js` already pins the installed one.)

## Procedure

### 0. Check / launch the browser

```bash
NODE_PATH="$APPDATA/npm/node_modules/@playwright/mcp/node_modules" node scripts/check.js
```
If it errors (no listener on 9224), launch it in a **background** bash task (it never exits):
```bash
NODE_PATH="$APPDATA/npm/node_modules/@playwright/mcp/node_modules" node scripts/launch.js
```
If the launch exits immediately with `exitCode=21` and no useful stderr — just run it again. Seen once,
transient, no root cause found (not Smart App Control, not a port conflict — retried and it just worked).

If `check.js` reports the URL is on `auth2.fastwork.co`, tell the user to log in in the visible window
and wait; do not proceed until `LOGGED_IN: true`.

### 1. Gather what only the seller knows

Before writing anything, get from the user (ask via AskUserQuestion if not already given — do not invent
these): what the service actually is, price(s), session/hour structure, delivery mode (online / on-site
at client / both). Everything else (category pick, copywriting, images, tags) you can do yourself.

### 2. Optional: research a competitor or a reference listing first

If the user gives a `fastwork.co/user/<handle>/<slug>-<id>` URL, open it in a **new tab** (`ctx.newPage()`,
not the main page — keeps your own draft-in-progress untouched) while logged in. The page renders a LOT
of seller-center chrome first (notification history, the entire category mega-menu — hundreds of lines)
before the actual listing content; `document.body.innerText` will be huge. Read past the chrome to the
section starting around `"1/6 ภาพรวม แพ็กเกจ ฟรีแลนซ์ รีวิว"` — that's the real listing: title, subtitle,
full description, all packages with per-package deliverable bullets, and reviews. Extract structural
techniques (keyword-dense opening line, an explicit differentiation section, concrete/countable
deliverables, launch bonuses) to apply to your own copy — do not copy their sentences verbatim.

### 3. Category

Click the category react-select input and type a guess; Fastwork's own "หมวดหมู่แนะนำ" (suggested
categories) list that appears is usually right. Useful known nodes: `ผู้เชี่ยวชาญ AI > คอร์สเรียน AI`,
`ผู้เชี่ยวชาญ AI > AI Consultant`, `เรียนพิเศษ > เรียนเขียนโปรแกรม`, `ทำแอปเว็บไซต์ > Web Development`.
⚠️ Category **locks permanently once the listing is approved** — get this right before first submit.

### 4. Generate images with chatgpt-bridge

`$PROJECTS/chatgpt-bridge` (NOT `notebooklm-bridge`, a similarly-named different project) drives
chatgpt.com with the user's own logged-in ChatGPT Plus session — no per-image API cost, and GPT-4o
renders Thai text inside images accurately when you spell it out exactly in the prompt.

```bash
cd $PROJECTS/chatgpt-bridge
node chatgpt-img.mjs "<prompt, ~40-60s per image>" <out.png>
```

Cover image target: **1280×720 (16:9)**, max 6000×6000px, ≤10MB. Run generations for cover + portfolio
sequentially, not in parallel — untested whether the shared `chatgpt-data/` profile handles two
concurrent driver processes. Kick a generation off as a **background** bash task and keep filling other
form fields on the Fastwork side while it runs.

Two style directions that both worked well:
- **Flat brand infographic** (navy/gold, line icons, big Thai headline) — good for process diagrams and
  package-comparison graphics.
- **Photorealistic office/training scene** — good for cover images selling a service to a corporate
  buyer; ask for "no readable text, no logos, no watermarks" so GPT-4o doesn't garble English UI chrome.

### 5. Fill basic-info (`/product/basic-info?id=<uuid or omitted for new>`)

Fields: `input[name="title"]`, `textarea[name="description"]` (max 5000 chars), `input[name="price"]`
(starting price — category has its own minimum, shown live under the field), cover image via
`input[type="file"]` (opens a crop/caption dialog after upload — caption is search-only, never shown on
page). Service area: "นอกสถานที่" (on-site) needs an explicit "เพิ่มพื้นที่ให้บริการ" click, which opens
a map modal defaulting to "ทั่วประเทศ" (nationwide) — just click บันทึก unless the user wants a narrower
area. "ออนไลน์" is on automatically.

**Call `fw.saveDraft(page)` immediately after filling — before any `page.goto()` elsewhere.** An
unsaved-changes confirm dialog fires on navigation and the `dialog` handler in `fw-lib.connect()`
auto-accepts it, which silently **discards the unsaved edit**. This bit twice in one session.

### 6. Packages (`/product/packages?id=...`)

Two display modes: `#display_mode_list` (แบบคำอธิบาย, up to 10 packages, free-text) vs
`#display_mode_table` (แบบตาราง, max 3, side-by-side comparison with a shared deliverables checkbox
matrix). Use table mode whenever you have ≤3 tiers — it reads far better as a pricing table.

⚠️ **Radio/checkbox inputs here do not respond to a normal Playwright click, even with `force: true`.**
Use `fw.nativeClick(page, selector)` (raw `element.click()` via `page.evaluate`) — that's what actually
flips React's state. Switching display mode pops a **second** confirm modal
("ยืนยันการเปลี่ยนรูปแบบการแสดงแพ็กเกจหรือไม่?") — click its "ยืนยัน" too.

⚠️ **Every field/checkbox for every package (including ones not currently selected in the left sidebar)
stays in the DOM at once, just hidden with CSS.** A plain `input[placeholder="ระบุชื่อแพ็กเกจ"]` will
match the WRONG package's hidden field. Always use `fw.fillVisible(page, selector, value)` (appends
`:visible`) or `fw.setCheckboxVisible`.

Per package: name, `รายละเอียด` (200 char cap), `ราคาเริ่มต้น` (category minimum applies), `ระยะเวลาใน
การทำงาน` (days — for a training service this is more "spread across N sessions" than a hard SLA, pick
something proportionate), unlimited-revisions checkbox (`#is_revision_times_unlimited`), and the
`#package-switch-<uuid>` visibility toggle (id suffix is empty until the package is first saved —
`input[id^="package-switch-"]` prefix-match, filtered to the visible one).

Add a package: `.Style_add-item-container__o89_z button` is the real control — the visible "+" text is a
`<span>` with no handler of its own; clicking the span does nothing.

**Deliverables matrix** ("สิ่งที่ลูกค้าจะได้รับ", table mode only): one row = one feature
(`input[name="deliverables.N.title"]`), one checkbox per package column
(`input[name="deliverables.N.packages.<packageId>"]`, empty packageId = an unsaved package). Add rows
with `fw.addRowsUntil` (a blind loop of clicks over/under-adds — it verifies count after each click), then
fill with `fw.setDeliverableRow(page, {rowIndex, title, checks})` per row. Deleting a stray row pops yet
another confirm modal ("ยืนยันการลบสิ่งที่ลูกค้าจะได้รับ?").

Save draft after packages are done, same rule as step 5.

### 7. Album (`/product/album?id=...`)

`input[type="file"]` takes multiple files directly (`setInputFiles([a, b])`) — no need to click the
visible "อัปโหลดภาพผลงาน" button first. **Before adding new images, check what's already there — read
each existing image's `alt` text**, it often carries real proof-of-work captions (e.g. "ภาพผลงานเพลงที่
ลงบน spotify แล้ว...") that look unrelated to the new content at a glance but are legitimate and must not
be deleted. Portfolio video field (`input[type="url"]`) may already hold a real saved link too — check
`.inputValue()`, don't assume a placeholder.

### 8. Tags (`/product/searchable-info?id=...`)

react-select combobox, `input[id*="react-select"]` — click, type, `Enter`, repeat. Tags help search
matching only; never shown on the listing page itself.

### 9. Submit

`fw.submitForReview(page)` — clicks "ส่งตรวจสอบ", then the "ยืนยันการบันทึกข้อมูล? ระบบใช้เวลาใน
การตรวจสอบภายใน 2 วันทำการ" confirm modal. Do this only when the user has actually authorized publishing
in the current turn (per this machine's standing prod-write rule) — filling the form is safe/reversible,
submitting makes it visible to Fastwork's review queue and, once approved, to buyers.

Approval can land fast — one listing this session was approved ~9 minutes after submit (seen via the
seller-center notification bell on an unrelated page load, not by polling).

### 10. Editing a listing that's ALREADY approved

Any edit to an approved listing creates a separate "ฉบับแก้ไข" (revision) sub-record — the live version
stays untouched and serving buyers until the revision itself gets approved. Same URL/id, so the same
scripts work unchanged.

⚠️ **The deliverables checkbox matrix does NOT carry over into the revision copy**, even though the
packages themselves (names/prices/visibility), album images, and tags all do carry over correctly.
Confirmed by re-editing a listing on the same day it was created: reopening `/product/packages?id=...`
on the revision showed 3 intact packages but an empty (0-row) deliverables table, silently dropping 6
rows that had been filled and saved before the first submit. **After editing an approved listing, always
`fw.readDeliverables(page)` and compare against what you expect before re-submitting** — if it's empty,
re-fill from scratch (keep your row content sitting in the driver script so this is a re-run, not a
re-derivation).

## Common failures

| Symptom | Cause | Fix |
|---|---|---|
| `exitCode=21` on first browser launch | unknown, transient | just retry the launch |
| Field ends up on the wrong package | hidden packages share selectors | always `:visible`-scope (`fw.fillVisible`) |
| Radio/checkbox click does nothing | Playwright synthetic click doesn't reach Fastwork's React handler | `fw.nativeClick` / `fw.setCheckboxVisible` |
| Edit vanishes after `page.goto()` | unsaved-changes dialog auto-accepted by the connect() handler | `fw.saveDraft(page)` before every navigation |
| "+เพิ่ม..." click does nothing | visible text is a non-interactive `<span>` | target `<container> button`, not the text |
| Deliverables empty after editing an approved listing | revision copy doesn't carry that sub-collection | re-fill and verify with `readDeliverables` before submit |
| A portfolio asset looks off-topic | you didn't check its `alt`/value before judging it | read `alt`/`.inputValue()` first, it may be real proof-of-work |

## Anti-patterns

- ❌ Re-running a "create new job" navigation script mid-session out of habit — it's harmless (nothing
  saves until you click a save button) but wastes a turn double-checking `งานของฉัน (N/10)` didn't grow.
- ❌ Trusting a filled-in field without a follow-up `.inputValue()` read after any mode switch (display
  mode toggle, page reload, revision creation) — this skill exists because three separate things silently
  discarded data this way in one session.
- ❌ Inventing business specifics (price, promo/bonus offers, session count) the seller hasn't given you.
  Ask. Copywriting, structure, and images are yours to originate; commitments that cost the seller real
  money or reputation are not.
