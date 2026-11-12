import bpy, sys, time, os

out_dir = sys.argv[sys.argv.index("--") + 1]
scene = bpy.context.scene
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'

# Cycles device options visible on this machine
try:
    cp = bpy.context.preferences.addons['cycles'].preferences
    for t in ('OPTIX', 'CUDA', 'HIP', 'ONEAPI', 'METAL'):
        try:
            cp.compute_device_type = t
            cp.get_devices()
            devs = [(d.name, d.type) for d in cp.devices if d.type != 'CPU']
            print("CYCLES_DEVICES %s=%s" % (t, devs))
        except Exception as e:
            print("CYCLES_DEVICES %s unavailable (%s)" % (t, type(e).__name__))
    cp.compute_device_type = 'NONE'
except Exception as e:
    print("CYCLES_PREFS_ERROR", e)

engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
print("ENGINES", engines)

def run(engine, label, samples=None):
    try:
        scene.render.engine = engine
        if engine == 'CYCLES':
            scene.cycles.device = 'CPU'
            scene.cycles.samples = samples
            scene.cycles.use_denoising = True
        scene.render.filepath = os.path.join(out_dir, label + ".png")
        t = time.time()
        bpy.ops.render.render(write_still=True)
        ok = os.path.isfile(scene.render.filepath)
        print("RESULT %s seconds=%.1f file_written=%s" % (label, time.time() - t, ok))
    except Exception as e:
        print("RESULT %s FAILED %s: %s" % (label, type(e).__name__, e))

eevee = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in engines else 'BLENDER_EEVEE_NEXT'
run(eevee, "eevee")
run('CYCLES', "cycles_cpu_64", 64)
run('CYCLES', "cycles_cpu_256", 256)
