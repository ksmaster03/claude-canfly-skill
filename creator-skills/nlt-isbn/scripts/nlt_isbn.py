# -*- coding: utf-8 -*-
"""ขับ e-service.nlt.go.th (หอสมุดแห่งชาติ) ผ่าน Chrome จริงทาง CDP พอร์ต 9333

  python nlt_isbn.py chrome                  เปิด Chrome (โปรไฟล์ถาวร) ให้ผู้ใช้ล็อกอินเองครั้งแรก
  python nlt_isbn.py status                  ล็อกอินอยู่ไหม + รายการคำร้อง ISBN ทั้งหมด
  python nlt_isbn.py fill   <book.json> [--dry]  --dry = กรอกอย่างเดียว ไม่กดถัดไป
  (ไม่ใส่ --dry)                             ขั้นที่ 1 กรอกฟอร์ม -> กดไปขั้นตรวจสอบ (ระบบเก็บเป็น "ร่าง")
  python nlt_isbn.py attach <book.json>      ขั้นที่ 3 แนบ 3 ไฟล์จาก build_isbn_docs.py (หน้าต้องอยู่ที่ EditFiles)
  python nlt_isbn.py fix    <book.json> <editId> [--dry]  แก้คำร้องที่ถูกตีกลับ (editId จากลิงก์ /isbnreq/Edit/<id>)
  python nlt_isbn.py deposit <book.json> <editId>   ส่ง PDF ตาม พ.ร.บ. (หลังอนุมัติ + apply_isbn)
  python nlt_isbn.py submit                  ขั้นที่ 4 บันทึก + ยืนยันคำร้อง  ‼ ส่งจริงถึงเจ้าหน้าที่

ทุกคำสั่งพิมพ์ผลที่อ่านจากหน้าจริง ไม่เดาว่าสำเร็จ
"""
import io, json, os, re, subprocess, sys, time, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

BASE = 'https://e-service.nlt.go.th'
PORT = 9333
PROFILE = os.path.expandvars(r'%LOCALAPPDATA%\nlt-eservice-profile')
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'


def txt(pg):
    return re.sub(r'\s+', ' ', pg.inner_text('body'))


def page(p):
    ctx = p.chromium.connect_over_cdp(f'http://127.0.0.1:{PORT}').contexts[0]
    pg = next((x for x in ctx.pages if 'nlt.go.th' in x.url), ctx.pages[0])
    pg.set_default_timeout(20000)
    msgs = []
    pg.on('dialog', lambda d: (msgs.append(d.message), d.accept()))  # confirm() ของ "ไม่ต้องการ CIP" / "บันทึก"
    return pg, msgs


def cmd_chrome():
    subprocess.Popen([CHROME, f'--remote-debugging-port={PORT}', f'--user-data-dir={PROFILE}',
                      '--no-first-run', BASE + '/'])
    print('เปิด Chrome แล้ว — ถ้ายังไม่ล็อกอิน ให้ผู้ใช้ล็อกอินเอง (มี reCAPTCHA) แล้วค่อยรัน status')


def cmd_status():
    """ทุกหน้าของรายการคำร้อง: เลขที่คำร้อง | editId | สถานะ | ชื่อเรื่อง (เก็บ JSON ไว้ที่ status.json ข้างสคริปต์)"""
    L = BASE + '/isbnreq/List?ISBNReqTypeKey=RequestNew&RegTypeKey=JuristicPerson&fromRangeCode=00000&toRangeCode=00000&pageNo='
    with sync_playwright() as p:
        pg, _ = page(p)
        out = []
        for n in range(1, 20):
            pg.goto(L + str(n)); time.sleep(2.5)
            if n == 1 and 'ออกจากระบบ' not in txt(pg):
                sys.exit('ยังไม่ได้ล็อกอิน — รัน chrome แล้วให้ผู้ใช้ล็อกอินเอง')
            rows = pg.evaluate("""()=>[...document.querySelectorAll('table tbody tr')].filter(tr=>tr.querySelectorAll('td').length>8).map(tr=>{
                const c=[...tr.querySelectorAll('td')].map(t=>t.innerText.trim());
                const a=tr.querySelector('a[href*="/isbnreq/Edit/"],a[href*="/ISBNReq/Edit/"]');
                return {req:c[1], isbn:c[3], title:c[4], status:c[5], edit:a?(a.getAttribute('href').match(/Edit[/]([0-9]+)/)||[])[1]:''}})""")
            if not rows or (out and rows[0]['req'] == out[0]['req']):
                break
            out += rows
        json.dump(out, io.open(pathlib.Path(__file__).with_name('status.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        for r in out:
            print(f"{r['req']} | {r['edit']} | {r['status']} | {r['isbn']} | {r['title'][:50]}")
        from collections import Counter
        print('รวม', len(out), dict(Counter(r['status'] for r in out)))


def cmd_fill(cfg, dry=False, edit_id=None):
    c = json.load(io.open(cfg, encoding='utf-8')); pub = c['publisher']
    with sync_playwright() as p:
        pg, msgs = page(p)
        url = f'/isbnreq/Edit/{edit_id}?ISBNReqType=RequestNew' if edit_id else '/isbnreq/Edit?ISBNReqType=RequestNew'
        pg.goto(BASE + url); time.sleep(3)

        def setv(sel, v):  # datepicker: ต้อง set ค่าแล้ว trigger change (รูปแบบ dd/mm/พ.ศ.)
            pg.evaluate("([s,v])=>{const e=document.querySelector(s); e.value=v; $(e).trigger('change');}", [sel, v])

        def pick(sel, text, wait=2.5):  # dropdown แบบ cascade ชื่อมีวงเล็บอังกฤษต่อท้าย ต้องเลือกด้วย value
            if pg.eval_on_selector(sel, 'e=>e.disabled'):
                return  # ช่องภาษาอังกฤษถูก disable และตามค่าภาษาไทยเอง
            v = pg.evaluate("([s,t])=>{const o=[...document.querySelector(s).options].find(o=>o.text.trim().startsWith(t)); return o?o.value:null}", [sel, text])
            if v is None:
                raise SystemExit(f'ไม่พบตัวเลือก {text} ใน {sel}')
            pg.select_option(sel, value=v); time.sleep(wait)

        title = c['title'] + (' : ' + c['subtitle'] if c.get('subtitle') else '')
        pg.fill('[name=ReqBookTitleName]', title)
        rows_ = pg.locator('#table-author tbody tr.row-item:not(.row-master)')
        if rows_.count() == 0:  # คำร้องเดิม (แก้ไข) มีผู้แต่งอยู่แล้ว ห้ามเพิ่มซ้ำ
            pg.locator('text=เพิ่มผู้แต่ง').first.click(); time.sleep(1)
        row = rows_.first
        tv = pg.evaluate("t=>{const o=[...document.querySelector('#ISBNReqAuthors_TitleKey').options].find(o=>o.text.trim().startsWith(t+' ('));return o?o.value:''}", c['author_title'])
        row.locator('select').select_option(value=tv)
        row.locator('input[type=text]').last.fill(c['author_name'])
        pg.fill('[name=EditionNote]', str(c['edition']))

        pg.check('input[name=RegTypeKey][value=%s]' % ('JuristicPerson' if pub['juristic'] else 'OrdinarPerson')); time.sleep(0.5)
        org_kw = pub.get('nlt_org_search')
        if pub['juristic'] and org_kw:
            # สำนักพิมพ์อยู่ในทะเบียนหอสมุดแล้ว (เจ้าหน้าที่ลงให้หลังขอครั้งแรก): ค้นหาแล้วเลือก ระบบเติมที่อยู่ไทย/อังกฤษให้เอง
            pg.click('.manage-change-organization'); time.sleep(2.5)
            dlg = pg.locator('#dialog-search-organization')
            dlg.locator('input[name=Keyword]').fill(org_kw)
            dlg.locator('button[type=submit]').first.click(); time.sleep(2.5)
            radios = dlg.locator('input[name=Key]')
            if radios.count() != 1:
                raise SystemExit(f'ค้นสำนักพิมพ์ "{org_kw}" ได้ {radios.count()} รายการ ต้องได้ 1')
            radios.first.check()
            dlg.locator('.manage-select').click(); time.sleep(4)
            key = pg.eval_on_selector('#PubOrganizationKey', 'e=>e.value')
            name = pg.eval_on_selector('#PubName', 'e=>e.value')
            if not key or name != pub['name_th']:
                raise SystemExit(f'เลือกสำนักพิมพ์ไม่สำเร็จ key={key} name={name}')
            print('สำนักพิมพ์จากทะเบียน:', key, name)
        else:
            # นิติบุคคลที่ยังไม่อยู่ในทะเบียนหอสมุด: PubName เป็น readonly -> ตั้งด้วย JS แล้วแนบหนังสือรับรองเป็นไฟล์แยก
            pg.evaluate("v=>{$('#PubName').val(v)}", pub['name_th'])
            for k, v in [('PubAddressNo', pub['address_no']), ('PubMoo', pub.get('moo', '')), ('PubSoi', pub.get('soi', '')),
                         ('PubRoad', pub.get('road') or '-')]:
                pg.fill(f'[name={k}]', v)
            pick('[name=PubProvinceKey]', pub['province']); pick('[name=PubDistrictKey]', pub['district'])
            pick('[name=PubSubdistrictKey]', pub['subdistrict'])
            for k, v in [('PubZipCode', pub['zip']), ('PubPhone', pub['phone']), ('PubMobile', pub.get('mobile', '')),
                         ('PubEmail', pub['email']), ('PubWebAddress', pub.get('web', '')),
                         ('ENPubName', pub['name_en']), ('ENPubAddressNo', pub['address_no']), ('ENPubMoo', pub.get('moo', '')),
                         ('ENPubRoad', pub.get('road') or '-'), ('ENPubZipCode', pub['zip']), ('ENPubPhone', pub['phone']),
                         ('ENPubMobile', pub.get('mobile', '')), ('ENPubEmail', pub['email']), ('ENPubWebAddress', pub.get('web', ''))]:
                pg.fill(f'[name={k}]', v)
        for s in ['ENPubProvinceKey', 'ENPubDistrictKey', 'ENPubSubdistrictKey']:
            print(s, '=', pg.eval_on_selector(f'[name={s}]', 'e=>e.options[e.selectedIndex].text'))

        # e-book: เจ้าหน้าที่สั่ง (ต.ค. 2569) ให้เว้นว่างทุกช่องของโรงพิมพ์ และจังหวัด/อำเภอ/ตำบล เลือก "-- กรุณาเลือก --"
        # (คู่มือเล่มเก่าหน้า 43 บอกให้ใส่ "-" แต่เจ้าหน้าที่ตีกลับ)
        for n in ['PrintName', 'PrintAddressNo', 'PrintBuilding', 'PrintFloor', 'PrintRoom', 'PrintMoo', 'PrintSoi',
                  'PrintRoad', 'PrintZipCode', 'PrintPhone', 'PrintFax', 'PrintMobile', 'PrintEmail', 'PrintWebAddress']:
            pg.fill(f'[name={n}]', '')
        for n in ['PrintSubdistrictKey', 'PrintDistrictKey', 'PrintProvinceKey']:
            pg.evaluate("n=>{const e=document.querySelector('[name='+n+']'); e.value=''; $(e).trigger('change');}", n); time.sleep(1)

        pg.fill('[name=PrintYear]', c['year_be']); pg.fill('[name=NoOfPage]', str(c['pages']))
        if int(c['price']) == 0:  # เล่มแจกฟรี: ติ๊ก "ไม่มีราคาจำหน่าย (Free Copy)" ตามคู่มือข้อ 11 (คำร้องเดิมอาจติ๊กไว้แล้ว)
            if not pg.eval_on_selector('#ChkIsFree', 'e=>e.checked'):
                pg.check('#ChkIsFree'); time.sleep(0.5)
        else:
            if pg.eval_on_selector('#ChkIsFree', 'e=>e.checked'):
                pg.uncheck('#ChkIsFree'); time.sleep(0.5)
            pg.fill('[name=Price]', str(c['price']))
        pg.fill('[name=NoOfCopy]', '')                                    # e-book: เจ้าหน้าที่สั่งให้เว้นว่าง (ไม่ใช่ 0)
        pg.click('input[name=PrintOutputTypeKey][value=Others]')          # e-book = อื่นๆ (เจ้าหน้าที่ย้ำว่าต้องเลือก)
        assert pg.evaluate("()=>document.querySelector('input[name=PrintOutputTypeKey]:checked')?.value") == 'Others'
        pick('[name=PublicationCatKey]', 'หนังสืออิเล็กทรอนิกส์', 1)
        pg.fill('[name=PublicationNote]', c['url'])
        dis = pg.locator('input[name=usePubAddressForDis][type=checkbox]')
        if dis.is_visible():  # เล่มฟรี (Free Copy) ระบบซ่อนส่วนผู้จัดจำหน่ายไป
            dis.check(); time.sleep(3)
        setv('[name=PrintDate]', c['print_date']); setv('[name=PublicationDate]', c['publication_date'])
        pg.click('input[name=IsCipRequired][value=%s]' % ('True' if c.get('want_cip') else 'False')); time.sleep(1)

        vals = pg.evaluate("""()=>[...document.querySelectorAll('form input,form select,form textarea')]
          .filter(e=>e.offsetParent!==null&&e.type!=='hidden'&&!(e.type==='radio'&&!e.checked)&&(e.value||e.tagName==='SELECT'))
          .map(e=>(e.name||e.id)+'='+(e.tagName==='SELECT'?e.options[e.selectedIndex]?.text:(e.type==='checkbox'?e.checked:e.value)))""")
        print(' | '.join(vals))
        if dry:
            print('DRY: กรอกครบแล้ว ไม่กดถัดไป (ยังไม่มีอะไรถูกบันทึก) | dialogs', msgs); return
        pg.locator('text=ถัดไปขั้นตอนการตรวจสอบ').first.click(); time.sleep(5)
        errs = pg.evaluate("()=>[...document.querySelectorAll('.field-validation-error,.validation-summary-errors,.alert-danger')].filter(e=>e.offsetParent!==null&&e.innerText.trim()).map(e=>e.innerText.trim())")
        print('URL', pg.url, '| dialogs', msgs, '| errors', errs)
        if '/Preview/' in pg.url:
            pg.locator('text=ขั้นตอนส่งแนบไฟล์').first.click(); time.sleep(4)
            print('ไปขั้นแนบไฟล์แล้ว:', pg.url)


def cmd_attach(cfg):
    d = pathlib.Path(cfg).resolve().parent
    # หนังสือรับรองบริษัทต้องเป็นไฟล์แยก (เจ้าหน้าที่หาไม่เจอเมื่อรวมท้ายไฟล์หน้าลิขสิทธิ์)
    files = [('15', '1-cover-title.pdf'), ('16', '2-copyright-toc.pdf'), ('16', '4-dbd-certificate.pdf'), ('17', '3-abstract.pdf')]
    files = [(v, f) for v, f in files if (d / f).exists()]
    with sync_playwright() as p:
        pg, msgs = page(p)
        if '/EditFiles/' not in pg.url:
            sys.exit('หน้าไม่ได้อยู่ที่ EditFiles — รัน fill ก่อน หรือเปิดคำร้องร่างแล้วกดไปขั้นแนบไฟล์')
        # คำร้องที่ถูกตีกลับมีไฟล์เก่าอยู่ ลบให้หมดก่อน (ลบแบบ client เหมือนการแนบ มีผลเมื่อกดบันทึก)
        for _ in range(20):
            dl = pg.locator('#table-file-upload button.manage-delete-file:visible')
            if dl.count() == 0:
                break
            dl.first.click(); time.sleep(1.2)
            cf = pg.locator('.modal:visible >> text=ยืนยัน')
            if cf.count():
                cf.first.click(); time.sleep(1)
        # ไฟล์ผูกกับคำร้องฝั่ง client จนกว่าจะกด "ถัดไป ขั้นตอนบันทึกคำร้อง" -> ห้าม reload ระหว่างแนบ
        for v, f in files:
            pg.click(f'button.manage-upload-file[value="{v}"]')
            pg.locator('#dialog-upload-file .manage-select').wait_for(state='visible'); time.sleep(1.5)
            pg.set_input_files('#fileupload', str(d / f))
            st = []
            for _ in range(40):
                st = pg.evaluate("()=>[...document.querySelectorAll('#file-list .upload-status')].map(e=>e.innerText.trim())")
                if st and all(s == 'Done' for s in st):
                    break
                time.sleep(1)
            print(v, f, st)
            pg.locator('#dialog-upload-file .manage-select').click()
            pg.locator('#dialog-upload-file').wait_for(state='hidden'); time.sleep(1.5)
        t = txt(pg); i = t.find('การส่งหลักฐาน'); print(t[i:t.find('ลบรายการคำร้อง', i)], '| dialogs', msgs)


def cmd_submit():
    with sync_playwright() as p:
        pg, msgs = page(p)
        pg.click('#button-save'); time.sleep(3)
        btn = pg.locator('.modal:visible >> text=ยืนยัน')
        if btn.count():
            try:
                btn.first.click(timeout=60000)
            except Exception as ex:  # เว็บตอบช้า: คลิกไปแล้วแต่รอ navigation ไม่ทัน -> ไปดูผลจากหน้าจริงต่อ
                print('click timeout (ตรวจผลต่อ):', str(ex).splitlines()[0])
        for _ in range(30):
            if '/Final/' in pg.url:
                break
            time.sleep(2)
        time.sleep(2)
        t = txt(pg)
        print('URL', pg.url, '| dialogs', msgs)
        m = re.search(r'เลขที่คำร้อง : (\d+).{0,80}?วันที่ส่ง : ([\d/]+) เวลาที่ส่ง : ([\d:]+)', t)
        print('ส่งสำเร็จ' if m else 'ยังไม่เห็นหน้ายืนยัน — ตรวจหน้าจอเอง', m.groups() if m else t[:600])


def cmd_deposit(cfg, edit_id):
    """ส่ง PDF ตาม พ.ร.บ.จดแจ้งการพิมพ์ มาตรา 8-9 (ฉบับอิเล็กทรอนิกส์) ของเล่มที่อนุมัติแล้ว
    ใช้ out/<pdf> จาก apply_isbn.py เท่านั้น และตรวจก่อนว่าในเล่มมีเลข ISBN ของคำร้องนี้"""
    import fitz
    c = json.load(io.open(cfg, encoding='utf-8'))
    isbn = c.get('isbn')
    pdf = pathlib.Path(cfg).resolve().parent / 'out' / os.path.basename(c['book_pdf'])
    if not isbn or not pdf.exists():
        sys.exit(f'ยังไม่มี ISBN ใน book.json หรือยังไม่ได้รัน apply_isbn.py ({pdf})')
    d = fitz.open(pdf)
    if not any(f'ISBN (e-book) {isbn}' in d[i].get_text() for i in range(min(8, d.page_count))):
        sys.exit(f'ใน {pdf.name} ไม่พบบรรทัด "ISBN (e-book) {isbn}" ห้ามส่ง')
    with sync_playwright() as p:
        pg, msgs = page(p)
        pg.goto(f'{BASE}/ISBNReqElect/Edit/{edit_id}'); time.sleep(3)
        got = pg.eval_on_selector('#ISBNCode', 'e=>e.value')
        if got != isbn:
            sys.exit(f'หน้าส่งเป็น ISBN {got} ไม่ตรงกับ {isbn} ห้ามส่ง')
        pg.set_input_files('#PostPdfFileName', str(pdf)); time.sleep(1)
        pg.locator('form#form button[type=submit]').first.click()
        pg.wait_for_load_state('load', timeout=300000); time.sleep(3)
        t = txt(pg)
        i = t.find('สถานะการส่งสิ่งพิมพ์')
        print('URL', pg.url, '| dialogs', msgs)
        print(t[i:i + 400] if i >= 0 else t[:600])


if __name__ == '__main__':
    a = sys.argv[1:]
    {'chrome': lambda: cmd_chrome(), 'status': lambda: cmd_status(), 'fill': lambda: cmd_fill(a[1], '--dry' in a),
     'fix': lambda: cmd_fill(a[1], '--dry' in a, a[2]),
     'deposit': lambda: cmd_deposit(a[1], a[2]),
     'attach': lambda: cmd_attach(a[1]), 'submit': lambda: cmd_submit()}[a[0]]()
