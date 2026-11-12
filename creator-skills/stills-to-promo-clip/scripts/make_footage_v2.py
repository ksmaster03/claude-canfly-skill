"""Footage v2: every still becomes a depth-displaced 3D relief, filmed with a moving perspective camera.

  blender.exe -b --python make_footage_v2.py -- <render|test> [id-filter ...]

Needs hires/<id>.png and depth/<id>.npy from prep_stills.py.
  render -> frames_v2/<id>/f_####.jpg for every frame (finish with post_footage.py)
  test   -> test_v2/<id>_a.jpg / _b.jpg: first and last frame only, to check for stretching

What makes it read as filmed rather than a slide:
  * parallax: geometry is pushed toward the camera along the original view rays, so the picture is
    identical from the home position and near objects slide against far ones as the camera moves
  * the red laser pixels pulse and the whole picture breathes slightly (keyed value nodes)
  * a sparse field of dust specks floats in front, at real depth
  * a little handheld rotation, lens distortion + chromatic dispersion and bloom in the compositor
"""
import bpy, sys, os, glob, math, random
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["test"]
MODE, ONLY = argv[0], argv[1:]
FPS = 24
FAR, HALF_W, HALF_H = 10.0, 8.0, 4.5      # far plane: 16 x 9 units, 10 units from the home camera
RELIEF = 0.45                             # nearest geometry sits at FAR / (1 + RELIEF)
GW, GH = 384, 216
FRAMES = {"s10": 168}                     # ending runs long under the call to action
DEFAULT_FRAMES = 96
# camera path per shot: (x, y, forward) at start and end. Edges stay out of frame while
# |x| <= 0.8*forward and |y| <= 0.45*forward (see assert below).
MOVES = {
    "s01": ((0.0, 0.0, 0.15), (0.0, 0.1, 1.3)),
    "s02": ((-0.5, 0.0, 0.8), (0.5, 0.05, 1.0)),
    "s03": ((0.3, 0.0, 0.5), (-0.3, 0.05, 1.2)),
    "s04": ((-0.6, 0.0, 0.9), (0.4, 0.0, 0.9)),
    "s05": ((0.0, 0.0, 0.2), (0.2, 0.1, 1.2)),
    "s06": ((0.6, 0.0, 0.9), (-0.5, 0.0, 0.9)),
    "s07": ((-0.7, -0.05, 1.0), (0.6, 0.0, 1.0)),
    "s08": ((0.0, 0.0, 0.2), (0.5, -0.2, 1.6)),
    "s09": ((0.6, 0.0, 1.4), (0.0, 0.0, 0.3)),
    "s10": ((0.0, 0.2, 1.2), (0.0, 0.0, 0.1)),
}

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = "FootageV2"
r = scene.render
r.engine = "CYCLES"
cy = scene.cycles
cy.device = "CPU"
cy.samples = 6
cy.use_adaptive_sampling = False
cy.use_denoising = False
cy.max_bounces = 0
cy.transparent_max_bounces = 8
r.resolution_x, r.resolution_y, r.resolution_percentage, r.fps = 1920, 1080, 100, FPS
r.use_persistent_data = True
scene.view_settings.view_transform = "Standard"
world = bpy.data.worlds.new("black")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0
scene.world = world

stills = sorted(glob.glob(os.path.join(HERE, "hires", "s*.png")))
plan, f = [], 1
for p in stills:
    sid = os.path.basename(p)[:-4]
    n = FRAMES.get(sid[:3], DEFAULT_FRAMES)
    plan.append((sid, p, f, f + n - 1))
    f += n
TOTAL = f - 1
scene.frame_start, scene.frame_end = 1, TOTAL

# ---- shared flicker signals, keyed on a node group so every material reads the same values ----
rnd = random.Random(11)
grp = bpy.data.node_groups.new("MP_Flicker", "ShaderNodeTree")
grp.interface.new_socket("Laser", in_out="OUTPUT", socket_type="NodeSocketFloat")
grp.interface.new_socket("Breathe", in_out="OUTPUT", socket_type="NodeSocketFloat")
g_out = grp.nodes.new("NodeGroupOutput")
v_laser, v_breathe = grp.nodes.new("ShaderNodeValue"), grp.nodes.new("ShaderNodeValue")
grp.links.new(v_laser.outputs[0], g_out.inputs["Laser"])
grp.links.new(v_breathe.outputs[0], g_out.inputs["Breathe"])
for fr in range(1, TOTAL + 3, 3):
    # lasers: mostly a steady glow with occasional dips and hot flashes
    k = rnd.random()
    v_laser.outputs[0].default_value = -0.35 if k < 0.12 else (0.9 if k > 0.9 else rnd.uniform(0.05, 0.35))
    v_laser.outputs[0].keyframe_insert("default_value", frame=fr)
for fr in range(1, TOTAL + 8, 8):
    v_breathe.outputs[0].default_value = rnd.uniform(-0.025, 0.025)
    v_breathe.outputs[0].keyframe_insert("default_value", frame=fr)


def still_material(sid, path):
    m = bpy.data.materials.new("M_" + sid)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N = nt.nodes.new
    tex = N("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path)
    tex.interpolation = "Cubic"
    tex.extension = "EXTEND"
    sep = N("ShaderNodeSeparateColor")
    mx = N("ShaderNodeMath"); mx.operation = "MAXIMUM"
    sub = N("ShaderNodeMath"); sub.operation = "SUBTRACT"
    red = N("ShaderNodeMath"); red.operation = "MULTIPLY"; red.inputs[1].default_value = 3.0; red.use_clamp = True
    fl = N("ShaderNodeGroup"); fl.node_tree = grp
    mul = N("ShaderNodeMath"); mul.operation = "MULTIPLY"
    add1 = N("ShaderNodeMath"); add1.operation = "ADD"
    add2 = N("ShaderNodeMath"); add2.operation = "ADD"; add2.inputs[1].default_value = 1.0
    em = N("ShaderNodeEmission")
    out = N("ShaderNodeOutputMaterial")
    L = nt.links.new
    L(tex.outputs["Color"], sep.inputs[0])
    L(sep.outputs[1], mx.inputs[0]); L(sep.outputs[2], mx.inputs[1])
    L(sep.outputs[0], sub.inputs[0]); L(mx.outputs[0], sub.inputs[1])   # R - max(G, B): laser-red pixels
    L(sub.outputs[0], red.inputs[0])
    L(red.outputs[0], mul.inputs[0]); L(fl.outputs["Laser"], mul.inputs[1])
    L(mul.outputs[0], add1.inputs[0]); L(fl.outputs["Breathe"], add1.inputs[1])
    L(add1.outputs[0], add2.inputs[0])
    L(tex.outputs["Color"], em.inputs["Color"]); L(add2.outputs[0], em.inputs["Strength"])
    L(em.outputs[0], out.inputs["Surface"])
    return m


def relief_mesh(sid, path):
    d = np.load(os.path.join(HERE, "depth", sid + ".npy"))            # (260, 462), 1 = near
    from_y = np.linspace(0, d.shape[0] - 1, GH + 1)
    from_x = np.linspace(0, d.shape[1] - 1, GW + 1)
    yi, xi = np.clip(from_y.round().astype(int), 0, d.shape[0] - 1), np.clip(from_x.round().astype(int), 0, d.shape[1] - 1)
    dg = d[yi][:, xi][::-1]                                            # row 0 = bottom of the picture
    u, v = np.meshgrid(np.linspace(0, 1, GW + 1), np.linspace(0, 1, GH + 1))
    k = 1.0 / (1.0 + RELIEF * dg)                                      # scale along the view ray
    verts = np.stack([(u - 0.5) * 2 * HALF_W * k, (v - 0.5) * 2 * HALF_H * k, -FAR * k], -1).reshape(-1, 3)
    idx = np.arange((GW + 1) * (GH + 1)).reshape(GH + 1, GW + 1)
    faces = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]], -1).reshape(-1, 4)
    me = bpy.data.meshes.new("relief_" + sid)
    me.from_pydata(verts.tolist(), [], faces.tolist())
    uvl = me.uv_layers.new(name="UVMap")
    uvs = np.stack([u, v], -1).reshape(-1, 2)
    loops = np.zeros(len(me.loops), dtype=np.int32)
    me.loops.foreach_get("vertex_index", loops)
    uvl.data.foreach_set("uv", uvs[loops].ravel())
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    ob = bpy.data.objects.new("relief_" + sid, me)
    scene.collection.objects.link(ob)
    me.materials.append(still_material(sid, path))
    return ob


# ---- camera ----
cd = bpy.data.cameras.new("Cam")
cd.sensor_width = 36.0
cd.lens = 18.0 * FAR / HALF_W           # home view frames the far plane exactly
cd.clip_start, cd.clip_end = 0.05, 100
cam = bpy.data.objects.new("Cam", cd)
scene.collection.objects.link(cam)
scene.camera = cam

shots = []
for sid, path, f0, f1 in plan:
    ob = relief_mesh(sid, path)
    a, b = MOVES[sid[:3]]
    for fr, (x, y, fw) in ((f0, a), (f1, b)):
        assert abs(x) <= 0.8 * fw * 0.95 + 1e-9 and abs(y) <= 0.45 * fw * 0.95 + 1e-9, (sid, x, y, fw)
        cam.location = (x, y, -fw)
        cam.keyframe_insert("location", frame=fr)
    scene.timeline_markers.new(sid, frame=f0)
    shots.append((sid, ob, f0, f1))
cam.rotation_euler = (0, 0, 0)
cam.keyframe_insert("rotation_euler", frame=1)


def fcurves_of(idblock):
    ad = idblock.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    curves = list(getattr(act, "fcurves", []) or [])
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for bag in getattr(strip, "channelbags", []):
                curves += list(bag.fcurves)
    return curves


for fc in fcurves_of(cam):
    for kp in fc.keyframe_points:
        kp.interpolation = "LINEAR"
    if fc.data_path == "rotation_euler" and fc.array_index in (0, 1):   # handheld: tiny pan/tilt wander
        nm = fc.modifiers.new("NOISE")
        nm.strength, nm.scale, nm.phase = 0.0035, 34.0, 13.0 * (fc.array_index + 1)
for nt in (grp,):
    for fc in fcurves_of(nt):
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"

# ---- dust specks at real depth ----
rnd = random.Random(5)
dv, df = [], []
for _ in range(140):
    z = -rnd.uniform(2.2, 6.0)
    x, y = rnd.uniform(-0.8, 0.8) * -z * 1.2, rnd.uniform(-0.45, 0.45) * -z * 1.3
    s = rnd.uniform(0.008, 0.02)
    i = len(dv)
    dv += [(x - s, y - s, z), (x + s, y - s, z), (x + s, y + s, z), (x - s, y + s, z)]
    df.append((i, i + 1, i + 2, i + 3))
dme = bpy.data.meshes.new("dust")
dme.from_pydata(dv, [], df)
duv = dme.uv_layers.new(name="UVMap")           # each speck gets its own 0..1 square for a soft round falloff
duv.data.foreach_set("uv", [c for _ in df for c in (0, 0, 1, 0, 1, 1, 0, 1)])
dust = bpy.data.objects.new("dust", dme)
scene.collection.objects.link(dust)
dm = bpy.data.materials.new("M_dust")
dm.use_nodes = True
nt = dm.node_tree
nt.nodes.clear()
em, tr, mix, out = (nt.nodes.new(n) for n in ("ShaderNodeEmission", "ShaderNodeBsdfTransparent", "ShaderNodeMixShader", "ShaderNodeOutputMaterial"))
em.inputs["Color"].default_value = (0.75, 0.85, 1.0, 1)
em.inputs["Strength"].default_value = 0.55
tc, mp, gr, ml = (nt.nodes.new(n) for n in ("ShaderNodeTexCoord", "ShaderNodeMapping", "ShaderNodeTexGradient", "ShaderNodeMath"))
mp.inputs["Location"].default_value = (-0.5, -0.5, 0)
mp.inputs["Scale"].default_value = (2, 2, 2)
gr.gradient_type = "QUADRATIC_SPHERE"
ml.operation = "MULTIPLY"
ml.inputs[1].default_value = 0.22
nt.links.new(tc.outputs["UV"], mp.inputs["Vector"]); nt.links.new(mp.outputs[0], gr.inputs["Vector"])
nt.links.new(gr.outputs["Fac"], ml.inputs[0]); nt.links.new(ml.outputs[0], mix.inputs[0])
nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], out.inputs["Surface"])
dme.materials.append(dm)
for sid, ob, f0, f1 in shots:           # drift restarts on each cut so the field never empties
    dust.location = (rnd.uniform(-0.3, 0.3), -0.15, 0)
    dust.keyframe_insert("location", frame=f0)
    dust.location = (dust.location.x + rnd.uniform(-0.25, 0.25), 0.2, 0)
    dust.keyframe_insert("location", frame=f1)
for fc in fcurves_of(dust):
    for kp in fc.keyframe_points:
        kp.interpolation = "LINEAR"

# ---- lens: slight barrel distortion with dispersion, then bloom ----
try:
    ng = bpy.data.node_groups.new("MP_Lens", "CompositorNodeTree")
    ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl, ld, gl, go = (ng.nodes.new(n) for n in ("CompositorNodeRLayers", "CompositorNodeLensdist", "CompositorNodeGlare", "NodeGroupOutput"))
    for k, v in (("Distortion", 0.012), ("Dispersion", 0.011), ("Fit", True)):
        if k in ld.inputs: ld.inputs[k].default_value = v
    for k, v in (("Type", "Bloom"), ("Quality", "High"), ("Threshold", 0.92), ("Strength", 0.22), ("Size", 0.35)):
        if k in gl.inputs: gl.inputs[k].default_value = v
    ng.links.new(rl.outputs["Image"], ld.inputs["Image"])
    ng.links.new(ld.outputs["Image"], gl.inputs["Image"])
    ng.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = ng
    print("compositor ok; lens inputs:", [i.name for i in ld.inputs])
except Exception as e:
    print("compositor skipped:", repr(e))

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "footage_v02.blend"))

s = r.image_settings
if hasattr(s, "media_type"):
    s.media_type = "IMAGE"
s.file_format = "JPEG"
s.quality = 96
for sid, ob, f0, f1 in shots:
    if ONLY and not any(o in sid for o in ONLY):
        continue
    for other in shots:
        other[1].hide_render = other[1] is not ob
    if MODE == "test":
        for tag, fr in (("a", f0), ("b", f1)):
            scene.frame_set(fr)
            r.filepath = os.path.join(HERE, "test_v2", f"{sid}_{tag}.jpg")
            bpy.ops.render.render(write_still=True)
        print("TEST", sid)
        continue
    import time
    t0 = time.time()
    for fr in range(f0, f1 + 1):
        fp = os.path.join(HERE, "frames_v2", sid, f"f_{fr - f0 + 1:04d}.jpg")
        if os.path.exists(fp):
            continue                    # resume after an interrupted run
        scene.frame_set(fr)
        r.filepath = fp
        bpy.ops.render.render(write_still=True)
    print(f"SHOT {sid}: {f1-f0+1} frames in {time.time()-t0:.0f}s")
print("ALL DONE")
