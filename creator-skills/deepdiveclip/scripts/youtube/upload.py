# -*- coding: utf-8 -*-
# 21/10/2026 อัปคลิปรวม (คลิปแนะนำ + เจาะลึกหลายระบบ) ขึ้น YouTube ช่องของคุณ แบบ unlisted ผ่าน API
# ต้องตั้ง env YT_TOKEN = path ของ OAuth token (authorized user json) ที่มีสิทธิ์ youtube.upload
# อ่านชื่อ คำอธิบาย แท็ก จาก meta.json (UTF-8) · ติ๊กเนื้อหาสังเคราะห์เพราะมีภาพคนที่เจนด้วย AI แบบสมจริง
import io, json, os, sys, time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

meta = json.load(io.open(sys.argv[1], encoding='utf-8'))
creds = Credentials.from_authorized_user_file(os.environ.get('YT_TOKEN', 'token.json'))
yt = build('youtube', 'v3', credentials=creds, cache_discovery=False)

body = {
    'snippet': {'title': meta['title'], 'description': meta['description'], 'tags': meta['tags'],
                'categoryId': meta['categoryId'], 'defaultLanguage': 'th', 'defaultAudioLanguage': 'th'},
    'status': {'privacyStatus': meta['privacyStatus'], 'embeddable': True, 'selfDeclaredMadeForKids': False,
               'license': 'youtube', 'publicStatsViewable': True, 'containsSyntheticMedia': True},
}
media = MediaFileUpload(meta['file'], mimetype='video/mp4', chunksize=8 * 1024 * 1024, resumable=True)
req = yt.videos().insert(part='snippet,status', body=body, media_body=media)
resp = None
while resp is None:
    st, resp = req.next_chunk()
    if st: print(f'upload {int(st.progress() * 100)}%', flush=True)
vid = resp['id']
print('video id', vid, flush=True)
yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(meta['thumb'], mimetype='image/jpeg')).execute()
print('thumbnail set', flush=True)
time.sleep(5)
v = yt.videos().list(part='status,snippet,processingDetails', id=vid).execute()['items'][0]
print(json.dumps({'id': vid, 'privacy': v['status']['privacyStatus'], 'embeddable': v['status'].get('embeddable'),
                  'synthetic': v['status'].get('containsSyntheticMedia'), 'upload': v['status'].get('uploadStatus'),
                  'processing': v.get('processingDetails', {}).get('processingStatus')}))
io.open(sys.argv[1].replace('meta.json', 'uploaded.json'), 'w', encoding='utf-8').write(json.dumps({'id': vid, 'url': f'https://youtu.be/{vid}'}))
