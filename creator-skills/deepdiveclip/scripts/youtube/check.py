# -*- coding: utf-8 -*-
# 21/10/2026 เช็กสถานะคลิปบน YouTube และตั้ง containsSyntheticMedia ถ้ายังไม่ติด
import json, os, sys
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
vid = sys.argv[1]
yt = build('youtube', 'v3', credentials=Credentials.from_authorized_user_file(os.environ.get('YT_TOKEN', 'token.json')), cache_discovery=False)
v = yt.videos().list(part='status,processingDetails,contentDetails,snippet', id=vid).execute()['items'][0]
st = v['status']
print(json.dumps({'privacy': st['privacyStatus'], 'synthetic': st.get('containsSyntheticMedia'), 'upload': st.get('uploadStatus'),
                  'processing': v.get('processingDetails', {}).get('processingStatus'), 'duration': v['contentDetails'].get('duration'),
                  'definition': v['contentDetails'].get('definition'), 'title': v['snippet']['title'][:60]}, ensure_ascii=False))
if len(sys.argv) > 2 and sys.argv[2] == 'fix' and not st.get('containsSyntheticMedia'):
    body = {'id': vid, 'status': {'privacyStatus': st['privacyStatus'], 'embeddable': st.get('embeddable', True), 'license': st.get('license', 'youtube'),
                                  'publicStatsViewable': st.get('publicStatsViewable', True), 'selfDeclaredMadeForKids': False, 'containsSyntheticMedia': True}}
    r = yt.videos().update(part='status', body=body).execute()
    print('updated synthetic ->', r['status'].get('containsSyntheticMedia'), 'privacy', r['status']['privacyStatus'])
