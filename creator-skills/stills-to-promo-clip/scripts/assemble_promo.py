"""Cut the promo in Blender's sequencer: footage clips + text/motion overlay frames + music.

Run headless:
  blender.exe -b --python assemble_promo.py

Needs ../footage/clips_v2/*.mp4 (make_footage_v2.py + post_footage.py), overlay/ov_####.png
(capture_overlay.mjs) and music.wav (mix_music.py).
"""
import bpy, os

HERE = os.path.dirname(os.path.abspath(__file__))
CLIPS = os.path.join(HERE, "..", "footage", "clips_v2")
FPS = 24
# (clip, start second, length seconds, frames skipped at the head of the 4 s clip)
CUT = [
    ("s01_vault_hall", 0, 4, 0),
    ("s02_hero_laptop", 4, 2, 24),
    ("s07_laser_walk", 6, 2, 24),
    ("s08_fingerprint", 8, 2, 40),
    ("s09_offline_ai", 10, 2, 0),
    ("s04_person_a", 12, 3, 12),
    ("s05_person_b", 15, 3, 12),
    ("s06_person_c", 18, 3, 12),
    ("s03_team", 21, 4, 0),
    ("s10_mission_complete", 25, 7, 0),      # v2 ending clip is 7 s long, no freeze frame needed
]
TOTAL = 32 * FPS

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = "Promo"
r = scene.render
r.resolution_x, r.resolution_y, r.resolution_percentage, r.fps = 1920, 1080, 100, FPS
scene.frame_start, scene.frame_end = 1, TOTAL
scene.view_settings.view_transform = "Standard"
se = scene.sequence_editor_create()
strips = se.strips if hasattr(se, "strips") else se.sequences

for name, start, length, skip in CUT:
    s = strips.new_movie(name, os.path.join(CLIPS, name + ".mp4"), 1, 1)
    s.frame_offset_start = skip
    s.frame_final_duration = length * FPS
    s.frame_start = start * FPS + 1 - skip

ov_dir = os.path.join(HERE, "overlay")
frames = sorted(f for f in os.listdir(ov_dir) if f.endswith(".png"))
ov = strips.new_image("overlay", os.path.join(ov_dir, frames[0]), 3, 1)
for f in frames[1:]:
    ov.elements.append(f)
ov.frame_final_duration = len(frames)
ov.blend_type = "ALPHA_OVER"
ov.alpha_mode = "STRAIGHT"

strips.new_sound("music", os.path.join(HERE, "music.wav"), 4, 1)

s = r.image_settings
if hasattr(s, "media_type"):
    s.media_type = "VIDEO"
s.file_format = "FFMPEG"
f = r.ffmpeg
f.format, f.codec = "MPEG4", "H264"
f.constant_rate_factor, f.ffmpeg_preset, f.gopsize = "HIGH", "GOOD", 12
f.audio_codec, f.audio_bitrate, f.audio_mixrate, f.audio_channels = "AAC", 192, 44100, "STEREO"
r.filepath = os.path.join(HERE, "MissionPossible_promo_v02.mp4")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "promo_v02.blend"))
bpy.ops.render.render(animation=True)
print("PROMO ->", r.filepath, len(frames), "overlay frames")
