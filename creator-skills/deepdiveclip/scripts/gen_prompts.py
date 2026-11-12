# -*- coding: utf-8 -*-
# 20/10/2026 พรอมป์ภาพสมจริงคลิปเจาะลึกระบบ (ตัวอย่างชุดงานคลังและโรงงาน ต้องเขียนใหม่ให้ตรงระบบของคุณ)
import io, json
STYLE = ("Photorealistic documentary-style photograph, shot on a full-frame camera, natural cinematic lighting, muted olive and steel-blue color grade "
         "with warm highlights, shallow depth of field, Thai (Southeast Asian) military personnel where people appear, realistic hands and faces, "
         "generic olive-green camouflage uniforms with no insignia, no name tapes, no unit patches, no rank badges. "
         "Absolutely no text, no letters, no numbers, no logos, no flags, no watermark, no firearms, no weapons. "
         "Wide landscape 16:9 composition with generous darker empty space on the left third for headline text. Scene: ")
S = {
 'm01-base-dawn': "Wide high-angle view of a large military logistics base at dawn: long rows of warehouses, lines of olive-green cargo trucks without markings, light mist and long shadows, a few soldiers walking.",
 'm02-receive': "Receiving dock of a military supply depot: soldiers unloading olive-green hard equipment cases from a cargo truck, one soldier inspecting a case and recording its condition on a rugged tablet, overhead work lights.",
 'm03-rfid': "Close-up of a soldier's hand holding a rugged handheld RFID reader with a red scan beam aimed at a small tag on a sealed olive-green metal storage box on a steel rack, dim storeroom, bokeh lights behind.",
 'm04-bunker': "Interior of a concrete earth-covered storage bunker with neatly stacked sealed olive-green metal boxes on pallets in marked floor zones, one soldier counting stock with a rugged tablet, cool lights, long perspective.",
 'm05-issue': "Quartermaster issue counter: a soldier handing field equipment (helmet, boots, backpack) across the counter to another soldier who signs on a tablet, tall shelves of equipment behind.",
 'm06-fuel': "Military fuel supply point at sunset: an olive-green fuel tanker truck without markings and rows of stacked jerrycans, a soldier checking a flow meter and writing on a tablet, warm backlight.",
 'm07-rations': "Supply warehouse with pallets of boxed field rations and bottled water, a soldier scanning a box barcode with a handheld scanner to check its expiry, clean racks, soft light.",
 'm08-factory': "Defense industry factory: technicians in navy work uniforms assembling the steel hull of an armored vehicle (no weapons, no turret) on a production line, a quality inspector with a tablet in front, bright industrial light.",
 'm09-qc': "Quality control lab of a defense manufacturer: a technician measuring a machined metal component with a digital caliper next to a coordinate measuring machine, parts in neat trays with blank labels, clean white light.",
 'm10-motorpool': "Military motor pool maintenance bay: olive-green tactical trucks without markings with hoods open, mechanics in coveralls working on engines, one mechanic holding a rugged tablet, work lights, oil-stained concrete floor.",
 'm11-qr': "Close-up of a mechanic scanning a small QR sticker on the side of an olive-green armored vehicle (no markings) with a smartphone, shallow depth of field, workshop bokeh.",
 'm12-heli': "Aircraft maintenance hangar: technicians on work stands inspecting the rotor head of an olive-drab utility helicopter without markings, tool carts, bright hangar lights, polished floor reflections.",
 'm13-sensor': "Extreme close-up of a small industrial vibration sensor with a glowing green LED mounted on a large diesel generator engine, a mechanic's gloved hand nearby, cinematic macro, warm and cool light.",
 'm14-ops': "Military command operations room: Thai officers in camouflage uniforms standing before a large wall of screens showing abstract readiness charts, gauges and a dark map with glowing icons (no readable text), dim blue room.",
 'm15-archive': "Old military records archive: tall shelves packed with binders and thick manuals, a young soldier pulling out a binder, dust floating in shafts of light from a high window.",
 'm16-airgap': "Secure closed-network server room inside a hardened concrete facility: a soldier-technician with a laptop standing at a locked server rack with glowing lights, heavy steel door, cool blue light.",
 'm17-ask': "Officer at a desk in a secure office at night typing a question to an AI assistant on a monitor showing abstract text blocks and small highlighted source document cards (nothing readable), warm desk lamp, focused face.",
 'm18-simroom': "Military simulation training room: soldiers seated at computer stations facing a huge curved wraparound screen showing a realistic 3D rendered mountain road with a convoy of olive trucks, blue glow on faces.",
 'm19-vr': "A soldier wearing a VR headset in a training lab, hands raised holding motion controllers, an instructor watching monitors behind, soft blue light.",
 'm20-aar': "After-action review session: an instructor pointing at a large screen showing a top-down 3D replay of a training exercise with glowing movement trails of unit icons, soldiers seated watching in a dark classroom.",
 'm21-3dworld': "High-quality real-time 3D game engine render (CGI look, not a photo) of a virtual military depot compound at dusk with warehouses, olive trucks and small soldier characters, seen from a third-person camera above and behind, volumetric light.",
 'm22-pushup': "Outdoor military fitness test field in the morning: a row of soldiers doing push-ups on mats, a small camera on a tripod in the foreground aimed at them, an examiner holding a tablet, golden light.",
 'm23-situp': "A soldier doing sit-ups on a mat while a partner holds his feet, a tablet on a small stand in front of them recording, morning light on a training field.",
 'm24-run': "Soldiers running a 2 kilometre fitness test on a road at sunrise, a finish line with a small timing camera on a pole, long shadows, motion.",
 'm25-score': "Close-up of a tablet held by an examiner showing an abstract fitness dashboard with a human pose skeleton figure and bar charts (no readable text), soldiers blurred in the background on a field.",
 'm26-closing': "Wide cinematic shot at golden hour: soldiers and civilian engineers standing together in front of a large modern supply depot, looking at tablets and talking, warm light, lens flare.",
}
json.dump([{'id': k, 'prompt': STYLE + v} for k, v in S.items()], io.open('__PROJECT__/src/gen_prompts.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(S), 'prompts')
