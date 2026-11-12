# ตรวจผู้ขายกับ web service ฟรีของกรมสรรพากร: จด VAT ไหม (รายสาขา) · เลขมีอยู่จริงไหม · ออก e-Tax ได้ไหม
#   python -I rd_check.py 0000000000000            ตรวจสำนักงานใหญ่ (สาขา 0)
#   python -I rd_check.py 0000000000000 1          ตรวจสาขาที่ 00001
#   python -I rd_check.py 0000000000000 --branches out.csv   ดึงทุกสาขาเป็น CSV (เฉพาะบริษัทที่สาขาไม่มาก)
#   python -I rd_check.py 0000000000000 --json     พิมพ์ผลเป็น JSON
# ต้องมี defusedxml (pip install defusedxml) · ไม่ต้องสมัคร ผู้ใช้/รหัสผ่านคือ anonymous ตามที่กรมประกาศ
import csv, json, socket, sys, time, urllib.error, urllib.request
import defusedxml.ElementTree as ET  # กัน XXE และ entity expansion
sys.stdout.reconfigure(encoding='utf-8')

# ทาง IPv6 ของ rdws.rd.go.th ต่อไม่ติดจากบางเครือข่าย ถ้าไม่บังคับ IPv4 จะค้างราว 21 วินาทีทุกคำขอ
_gai = socket.getaddrinfo
socket.getaddrinfo = lambda *a, **k: [r for r in _gai(*a, **k) if r[0] == socket.AF_INET]

VAT = 'https://rdws.rd.go.th/serviceRD3/vatserviceRD3.asmx'
TIN = 'https://rdws.rd.go.th/serviceRD3/checktinpinservice.asmx'
ETAX = 'https://etaxws.rd.go.th/etaxapi/services/checkRegstration'
SOAP = 'application/soap+xml; charset=utf-8'
AUTH = '<{p}:username>anonymous</{p}:username><{p}:password>anonymous</{p}:password>'


def post(url, body, ctype, timeout):
    req = urllib.request.Request(url, data=body.encode('utf-8'), headers={'Content-Type': ctype, 'User-Agent': 'rd-vat-check/1.0'})
    t = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8', 'replace'), round((time.time() - t) * 1000)


def envelope(ns_prefix, ns_uri, inner):
    return ('<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:%s="%s"><soap:Header/><soap:Body>%s</soap:Body></soap:Envelope>'
            % (ns_prefix, ns_uri, inner))


def columns(xml):
    """ผลทุกฟิลด์เป็นอาร์เรย์ anyType หนึ่งค่าต่อหนึ่งแถว (หนึ่งสาขา) ตัดตัว v นำหน้าชื่อฟิลด์"""
    out = {}
    for el in ET.fromstring(xml).iter():
        kids = [k for k in el if k.tag.endswith('anyType')]
        if kids:
            out[el.tag.split('}')[-1][1:]] = [' '.join((k.text or '').split()) for k in kids]
    return out


def clean(v):
    return '' if v in ('-', '') else v


def be_to_iso(d):
    """วันที่จด VAT ของกรมเป็นปี พ.ศ. เช่น 2550-04-04"""
    try:
        y, m, dd = d.split('-'); return '%04d-%s-%s' % (int(y) - 543, m, dd)
    except ValueError:
        return d


def check_vat(tin, branch):
    inner = ('<vat:Service>' + AUTH.format(p='vat') + '<vat:TIN>%s</vat:TIN><vat:Name></vat:Name><vat:ProvinceCode>0</vat:ProvinceCode>'
             '<vat:BranchNumber>%s</vat:BranchNumber><vat:AmphurCode>0</vat:AmphurCode></vat:Service>') % (tin, int(branch))
    xml, ms = post(VAT, envelope('vat', 'https://rdws.rd.go.th/serviceRD3/vatserviceRD3', inner), SOAP, 15)
    c = columns(xml)
    if 'msgerr' in c or not c.get('NID'):
        return {'found': False, 'ms': ms, 'message': c.get('msgerr', [''])[0].replace('<br>', '/')}
    addr = ' '.join(x for x in (clean(c.get(k, [''])[0]) for k in ('BuildingName', 'FloorNumber', 'RoomNumber', 'VillageName', 'HouseNumber')) if x)
    for k, label in (('MooNumber', 'หมู่ '), ('SoiName', 'ซอย '), ('StreetName', 'ถนน ')):
        if clean(c.get(k, [''])[0]): addr += ' ' + label + c[k][0]
    addr += ' ' + ' '.join(clean(c.get(k, [''])[0]) for k in ('Thambol', 'Amphur', 'Province', 'PostCode'))
    return {'found': True, 'ms': ms, 'tin': c['NID'][0], 'branch': int(c['BranchNumber'][0]),
            'name': ' '.join((clean(c['titleName'][0]) + ' ' + c['Name'][0]).split()),
            'branchName': ' '.join((clean(c['BranchTitleName'][0]) + ' ' + c['BranchName'][0]).split()),
            'address': ' '.join(addr.split()), 'vatSince': be_to_iso(c['BusinessFirstDate'][0])}


def check_tin(tin):
    inner = '<chec:ServiceTIN>' + AUTH.format(p='chec') + '<chec:TIN>%s</chec:TIN></chec:ServiceTIN>' % tin
    xml, ms = post(TIN, envelope('chec', 'https://rdws.rd.go.th/serviceRD3/checktinpinservice', inner), SOAP, 15)
    c = columns(xml)
    if 'MessageErr' in c:
        return {'exists': False, 'ms': ms, 'message': c['MessageErr'][0].replace('<br>', '/')}
    return {'exists': c.get('IsExist', [''])[0] == 'Yes', 'digitOk': c.get('DigitOk', [''])[0] == 'True', 'ms': ms}


def check_etax(tin):
    # ชื่อฟิลด์ต้องเป็น taxNo และส่งเป็น JSON เท่านั้น ครั้งแรกของแต่ละเลขช้าราว 10 วินาที
    txt, ms = post(ETAX, json.dumps({'taxNo': tin}), 'application/json', 25)
    j = json.loads(txt); d = j.get('data') or {}
    return {'code': j.get('code'), 'ms': ms, 'isVat': d.get('isVat'), 'approved': d.get('registerDatetime'),
            'ended': d.get('endDatetime'), 'channel': d.get('channelType')}


def verdict(vat, branch_hq, tin):
    if vat.get('found'):
        return 'PASS', 'จด VAT ตั้งแต่ %s' % vat['vatSince']
    if branch_hq and branch_hq.get('found'):
        return 'FAIL', 'จด VAT แต่ไม่มีเลขสาขานี้ในทะเบียน'
    if tin and tin.get('exists'):
        return 'FAIL', 'มีเลขผู้เสียภาษี แต่ไม่พบการจด VAT'
    return 'FAIL', 'เลขผู้เสียภาษีไม่มีอยู่จริง'


def export_branches(tin, path):
    inner = '<vat:ServiceArr>' + AUTH.format(p='vat') + '<vat:TINs><vat:string>%s</vat:string></vat:TINs></vat:ServiceArr>' % tin
    xml, ms = post(VAT, envelope('vat', 'https://rdws.rd.go.th/serviceRD3/vatserviceRD3', inner), SOAP, 60)
    c = columns(xml)
    if 'msgerr' in c: sys.exit('RD: ' + c['msgerr'][0])
    keys = [k for k in ('NID', 'BranchNumber', 'BranchTitleName', 'BranchName', 'BuildingName', 'RoomNumber', 'FloorNumber', 'VillageName',
                        'HouseNumber', 'MooNumber', 'Yaek', 'SoiName', 'StreetName', 'Thambol', 'Amphur', 'Province', 'PostCode', 'BusinessFirstDate') if k in c]
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f); w.writerow(keys)
        for i in range(len(c['NID'])): w.writerow([c[k][i] for k in keys])
    print('wrote %s: %d branches, %d ms' % (path, len(c['NID']), ms))


def main(argv):
    if not argv or len(argv[0]) != 13 or not argv[0].isdigit():
        print('usage: rd_check.py <TIN 13 หลัก> [branch] [--branches out.csv] [--json]'); sys.exit(2)
    tin = argv[0]
    if '--branches' in argv:
        return export_branches(tin, argv[argv.index('--branches') + 1])
    branch = next((a for a in argv[1:] if a.isdigit()), '0')
    res = {'tin': tin, 'branchAsked': int(branch)}
    try:
        res['vat'] = check_vat(tin, branch)
        hq = check_vat(tin, 0) if not res['vat']['found'] and int(branch) != 0 else None
        tn = check_tin(tin) if not res['vat']['found'] and not (hq and hq['found']) else None
        if hq: res['vatHeadOffice'] = hq
        if tn: res['tinCheck'] = tn
        res['verdict'], res['reason'] = verdict(res['vat'], hq, tn)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        res['verdict'], res['reason'] = 'PENDING', 'ระบบของกรมไม่ตอบ (%s) ลองใหม่หรือตรวจด้วยมือ' % e
    try:
        res['etax'] = check_etax(tin)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        res['etax'] = {'error': str(e)}
    if '--json' in argv:
        print(json.dumps(res, ensure_ascii=False, indent=2)); return
    v = res.get('vat', {})
    print('%s  %s' % (res['verdict'], res['reason']))
    if v.get('found'):
        print('  %s · สาขา %d %s\n  %s' % (v['name'], v['branch'], v['branchName'], v['address']))
    e = res['etax']
    print('  e-Tax: %s' % (('อนุมัติ %s ช่องทาง %s' % (e['approved'], e['channel'])) if e.get('code') == 'T001' and e.get('approved')
                           else e.get('code') or e.get('error')))


if __name__ == '__main__':
    main(sys.argv[1:])
