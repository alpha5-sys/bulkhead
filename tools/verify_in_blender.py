"""Headless integration check.

    blender --background --factory-startup --python tools/verify_in_blender.py

The layout maths is unit tested; this covers what only exists inside Blender —
registration, the operator, and whether the geometry it emits is actually valid mesh
rather than merely present. It renders at the end because this product is judged by
eye, and a face count proves nothing about whether the plating looks designed.
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "addon"))

OUT = os.path.join(ROOT, "build", "verify")
os.makedirs(OUT, exist_ok=True)

_failures = []
_checks = 0


def check(label, ok, detail=""):
    global _checks
    _checks += 1
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  {detail}" if not ok else ""))
    if not ok:
        _failures.append(f"{label} {detail}")


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def slab(subdivisions=0, size=2.0):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=2 + subdivisions,
                                    y_subdivisions=2 + subdivisions, size=size)
    return bpy.context.active_object


print("\n=== registering ===")
import bulkhead  # noqa: E402
from bulkhead import mesh  # noqa: E402
from bulkhead.core import subdivide  # noqa: E402

bulkhead.register()
print("registered")


# --------------------------------------------------------------------- plating
print("\n=== plating a quad ===")
reset()
bulkhead.unregister()
bulkhead.register()

obj = slab()
before = len(obj.data.polygons)
res = bpy.ops.bulkhead.plate(seed=0, use_features=False)
check("operator reports finished", res == {"FINISHED"}, str(res))
after = len(obj.data.polygons)
check("geometry was created", after > before, f"{before} -> {after}")

verts = [v.co for v in obj.data.vertices]
check("no NaN or infinite coordinates",
      all(all(math.isfinite(c) for c in v) for v in verts))

areas = [p.area for p in obj.data.polygons]
check("no degenerate faces", min(areas) > 1e-12, f"min area {min(areas):.3e}")
check("every face is a quad", all(len(p.vertices) == 4 for p in obj.data.polygons))

zs = [v.co.z for v in obj.data.vertices]
check("plates stand off the surface", max(zs) > 1e-6, f"max z {max(zs):.5f}")


# ------------------------------------------------------------- height levels
print("\n=== machined height steps ===")
reset(); bulkhead.unregister(); bulkhead.register()
obj = slab()
bpy.ops.bulkhead.plate(seed=3, use_features=False, levels=3,
                       base_height=0.05, step_height=0.05)
tops = sorted({round(v.co.z, 5) for v in obj.data.vertices if v.co.z > 1e-6})
check("plate tops land on a few discrete levels", 1 <= len(tops) <= 4, f"{tops}")


# ----------------------------------------------------------------- fittings
print("\n=== fittings ===")
reset(); bulkhead.unregister(); bulkhead.register()
obj = slab()
bpy.ops.bulkhead.plate(seed=1, use_features=False)
plain = len(obj.data.polygons)

reset(); bulkhead.unregister(); bulkhead.register()
obj = slab()
bpy.ops.bulkhead.plate(seed=1, use_features=True, density=0.6)
greebled = len(obj.data.polygons)
check("fittings add geometry", greebled > plain, f"{plain} -> {greebled}")
check("fittings produce no degenerate faces",
      min(p.area for p in obj.data.polygons) > 1e-12)


# -------------------------------------------------------------- determinism
print("\n=== determinism ===")
def plate_and_hash(seed):
    reset(); bulkhead.unregister(); bulkhead.register()
    o = slab()
    bpy.ops.bulkhead.plate(seed=seed, use_features=True)
    return tuple(round(c, 6) for v in o.data.vertices for c in v.co)

a, b = plate_and_hash(7), plate_and_hash(7)
check("same seed gives identical geometry", a == b)
check("different seeds give different geometry", a != plate_and_hash(8))


# ------------------------------------------------------------ non-quad input
print("\n=== non-quad input ===")
reset(); bulkhead.unregister(); bulkhead.register()
bpy.ops.mesh.primitive_cone_add(vertices=8)   # triangles + an ngon cap
cone = bpy.context.active_object
faces_before = len(cone.data.polygons)
res = bpy.ops.bulkhead.plate(seed=0)
check("non-quad mesh is refused cleanly, not crashed",
      res in ({"CANCELLED"}, {"FINISHED"}), str(res))
check("nothing was corrupted",
      all(all(math.isfinite(c) for c in v.co) for v in cone.data.vertices))

reset(); bulkhead.unregister(); bulkhead.register()
bpy.ops.mesh.primitive_cube_add()
cube = bpy.context.active_object
check("a cube (all quads) plates fine",
      bpy.ops.bulkhead.plate(seed=2, use_features=True) == {"FINISHED"})


# ------------------------------------------------------------- curved surface
print("\n=== curved surface ===")
reset(); bulkhead.unregister(); bulkhead.register()
bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1.5)
sphere = bpy.context.active_object
bpy.ops.object.shade_smooth()
res = bpy.ops.bulkhead.plate(seed=5, use_features=True, base_height=0.03,
                             step_height=0.03, gap=0.03, feature_height=0.02)
check("plates a curved hull", res == {"FINISHED"}, str(res))
radii = [v.co.length for v in sphere.data.vertices]
check("plating follows the curvature outward", min(radii) > 1.2,
      f"min radius {min(radii):.3f}")


# --------------------------------------------------------------- performance
print("\n=== performance ===")
import time  # noqa: E402
reset(); bulkhead.unregister(); bulkhead.register()
obj = slab(subdivisions=6)     # 64 quads
t0 = time.perf_counter()
bpy.ops.bulkhead.plate(seed=0, use_features=True, density=0.5)
ms = (time.perf_counter() - t0) * 1000.0
print(f"  64 quads, fittings on: {ms:.0f} ms, "
      f"{len(obj.data.polygons)} faces out")
check("no pathological slowdown", ms < 20000.0, f"{ms:.0f} ms")


# -------------------------------------------------------------------- render
print("\n=== render ===")
reset(); bulkhead.unregister(); bulkhead.register()

scene = bpy.context.scene
try:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
except TypeError:
    scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 1000, 640
scene.render.image_settings.file_format = "PNG"
try:
    scene.eevee.use_raytracing = False
    scene.eevee.taa_render_samples = 24
except AttributeError:
    pass


def material(name, base, rough, metal):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes["Principled BSDF"]
    n.inputs["Base Color"].default_value = base
    n.inputs["Roughness"].default_value = rough
    n.inputs["Metallic"].default_value = metal
    return m


world = bpy.data.worlds.new("W")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.02, 0.023, 0.03, 1)
scene.world = world

key = bpy.data.lights.new("Key", "AREA")
key.energy, key.size = 900.0, 5.0
ko = bpy.data.objects.new("Key", key)
ko.location, ko.rotation_euler = (3.5, -3.5, 5.0), (0.62, 0.25, 0.72)
scene.collection.objects.link(ko)

rim = bpy.data.lights.new("Rim", "AREA")
rim.energy, rim.size, rim.color = 600.0, 4.0, (0.5, 0.68, 1.0)
ro = bpy.data.objects.new("Rim", rim)
ro.location, ro.rotation_euler = (-4.0, 3.0, 2.0), (1.2, 0.0, -2.2)
scene.collection.objects.link(ro)

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 55.0
cam = bpy.data.objects.new("Cam", cam_data)
cam.location = (2.6, -3.4, 2.5)
cam.rotation_euler = (0.95, 0.0, 0.66)
scene.collection.objects.link(cam)
scene.camera = cam

steel = material("Steel", (0.30, 0.32, 0.35, 1.0), 0.34, 0.9)

obj = slab(size=3.0)
obj.data.materials.append(steel)
bpy.ops.bulkhead.plate(seed=4, use_features=True, density=0.5, max_depth=6,
                       min_size=0.05, gap=0.018, chamfer=0.005,
                       base_height=0.03, step_height=0.028,
                       feature_height=0.02, cell=0.05)
scene.render.filepath = os.path.join(OUT, "plating.png")
bpy.ops.render.render(write_still=True)
check("plating render written", os.path.exists(scene.render.filepath))

# Plating only, so the panel hierarchy can be judged without fittings on top.
# Swap the object rather than resetting the file: read_factory_settings frees the
# world, lights and camera datablocks, and reusing them afterwards is a dangling
# reference.
bpy.data.objects.remove(obj, do_unlink=True)
obj = slab(size=3.0)
obj.data.materials.append(steel)
bpy.ops.bulkhead.plate(seed=4, use_features=False, max_depth=6, min_size=0.05,
                       gap=0.02, chamfer=0.006, base_height=0.035,
                       step_height=0.032)
scene.render.filepath = os.path.join(OUT, "plates-only.png")
bpy.ops.render.render(write_still=True)
check("plates-only render written", os.path.exists(scene.render.filepath))


print("\n" + "=" * 58)
if _failures:
    print(f"FAILED  {len(_failures)} of {_checks}")
    for f in _failures:
        print("  - " + f)
    sys.exit(1)
print(f"OK  all {_checks} checks passed")
print(f"renders in {OUT}")
