---
name: human-docx
description: Draft Word (.docx) documents that read as genuinely written by a person — formal letters, company/HR announcements, memos (บันทึกข้อความ), general correspondence — in Thai or English, instead of the emoji-headers-and-color-tables look AI output defaults to. Trigger this whenever the user asks for a document "เขียนแบบคน", "human-written", explicitly says no emoji / no icons / no dividing lines / no colored highlight boxes, asks to make an existing draft "ดูไม่เหมือน AI เขียน" or less templated, or asks for any official-sounding Word document (ประกาศ, จดหมาย, หนังสือราชการ, memo, announcement email) without specifying a decorated style. If the user's request doesn't rule out heavy visual formatting, still default to this plain style for anything that reads as a real letter or announcement — save icons/tables/color for dashboards, slide decks, or things explicitly asked to look "eye-catching."
---

# Writing documents that read as human-written

AI-generated Word documents have a recognizable tell: emoji stapled onto every heading, bullet lists standing in for paragraphs, colored highlight tables for anything resembling a schedule, and horizontal rules chopping the page into little dashboard cards. A person writing a real letter, announcement, or memo doesn't do any of that — they write in sentences, group related sentences into paragraphs, and use a bold word or two only where it actually helps the reader find something later.

This skill produces the second kind of document. Use the bundled helper script rather than hand-rolling `python-docx` calls each time — it already has the Thai font plumbing worked out (see "Common pitfall" below), and reusing it means every document this skill produces looks consistent.

## The rules, and why they matter

- **No emoji, no icon glyphs** (🎉📅✅🔔💬 etc.) anywhere in the body or headings. A real HR announcement or official letter never has an emoji next to "Subject:". If the user's own message is full of emoji, that's their voice, not the document's.
- **No horizontal rules / border lines** separating sections. Section breaks come from a paragraph gap, not a drawn line — a printed letter doesn't have a `<hr>`.
- **No colored highlight tables or shaded boxes** for things like schedules, at least by default. A sentence like "งานจะกลับมาทำงานตามปกติในวันจันทร์ที่ 28 กันยายน" says the same thing a three-row colored table says, and it's what a person would actually type. A plain table is fine if the content is genuinely tabular data (a price list, a comparison of options) — the rule is against *decorating* prose as a table, not against tables that hold real tabular data.
- **Paragraphs over bullet lists.** If you catch yourself about to write four bullet points that are each a full sentence, they're a paragraph that got split up. Reserve bullets for things that are truly a list of short, parallel items (e.g., "เอกสารที่ต้องเตรียม: บัตรประชาชน, สำเนาทะเบียนบ้าน, รูปถ่าย"), not for turning every instruction into its own line.
- **Bold sparingly**, only on the one or two facts a skimming reader most needs (a date, a deadline, an amount) — not on every heading or every sentence's key phrase.
- **Natural register.** Thai business writing sits between the stiffness of a government circular and the looseness of a chat message — full sentences, polite particles where a person would actually say them (ครับ/ค่ะ, if the org's voice uses them), but not so formal it reads like a legal notice unless the document genuinely is one (an NDA, a government filing). Ask the user, or infer from context, which end of that register a given document should sit at — an HR announcement to all staff and a legal contract don't belong at the same register.

None of this means the document should look bare or unstructured — it means the structure is the kind a human writer produces: a clear opening line, one paragraph per idea, and a closing line, the same shape as an email you'd actually receive from a colleague.

## Workflow

1. **Confirm the content first, formatting second.** Get (or infer from the conversation) what the document needs to say: who it's to, the core fact/decision/date, any actions the reader needs to take, who signs it. Don't ask the user to specify formatting preferences unless they've given contradictory signals — the plain-prose style is the default for this skill, not one option among several.
2. **Pick the font and register.**
   - Thai body text: `Leelawadee UI` (the module default) for anything that will mainly be read on screen; switch to `TH Sarabun New` (`THAI_FONT_OFFICIAL` in the script) if the user wants an official-government-document look, or if the recipient organization uses it as a house style.
   - English-only documents: `Calibri` (`ENGLISH_FONT` in the script) reads more naturally than a Thai UI font's Latin glyphs.
3. **Build the document with the bundled script**, not raw `python-docx` boilerplate. From a scratch Python file:

   ```python
   import sys
   sys.path.insert(0, r"~\.claude\skills\human-docx\scripts")
   from human_docx import new_document, add_para, add_rich, add_page_break, save

   doc = new_document()
   add_para(doc, "เรียน เพื่อนพนักงานทุกท่าน", space_after=10)
   add_para(doc, "ย่อหน้าที่อธิบายเนื้อหาหลัก เขียนต่อเนื่องเป็นประโยคสมบูรณ์ ...", space_after=10)
   add_rich(doc, [("ส่วนที่อยากเน้น เช่นวันที่ ", False), ("25 กันยายน 2569", True), (" เขียนแทรกในประโยคได้เลย", False)])
   add_para(doc, "ขอแสดงความนับถือ", space_after=2)
   add_para(doc, "[ชื่อผู้ลงนาม]", space_after=0)
   save(doc, r"<path>\to\output.docx")
   ```

   `add_para` covers a single-run paragraph (size, bold, color, italic, spacing). `add_rich` covers a paragraph that mixes bold/plain runs in one sentence — use it instead of breaking a sentence across paragraphs just to bold part of it. See the docstrings in `scripts/human_docx.py` for the full parameter list.
4. **Common structure for a formal letter/announcement/memo**, adapt as needed — this is a shape, not a template to fill in mechanically:
   - Header block (To / Cc / From / Date / Subject as plain lines, or a formal Thai letterhead if it's an official document) — no table borders needed, plain lines with a bold subject line are enough.
   - Opening line addressing the reader.
   - One paragraph stating the core news/decision plainly.
   - One or two paragraphs giving the practical detail (dates, what changes, what the reader needs to do) — as prose, not bullets, unless the detail is genuinely a short parallel list.
   - A paragraph on who to contact with questions, if relevant.
   - Closing line and signature block.
   - If the document is a draft with placeholders the sender must fill in before sending (names, dates, contact info), it's fine to add a second page after a page break with a note listing what to fill in and what to double-check — that's a genuinely useful annex, not decoration, so plain paragraphs there are fine too (still no emoji/icons/color).
5. **Before declaring done, check the output against the rules above** — search your own draft mentally for emoji, bullet-heavy sections that are really prose, and any table/shading you added out of habit rather than because the content is tabular.

## Common pitfall: Thai text in a raw string / docstring

If you write your own script instead of importing the helpers, remember that a Windows path like `C:\Users\...` inside a normal (non-raw) Python string will choke on sequences like `\U` (interpreted as the start of an 8-hex-digit unicode escape) — prefix the string with `r` (`r"C:\Users\..."` or `r"""..."""`) whenever it contains a Windows path or arbitrary backslashes. The bundled script already does this.

## If the file won't save

`save()` raises a clear `PermissionError` if the target path is open in Word — this happens often when you're re-generating a file you just sent the user for review. Ask the user to close it, or write to a new filename, rather than guessing.
