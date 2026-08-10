"""Render the store assets the extensions platform requires.

  featured.png  1920x1080, 16:9 (the platform minimum is 1920 wide).
  icon.png      256x256, rendered at 1024 and downsampled.

Unlike Conduit (a capability shot) or Scuff (a before/after), Bulkhead's output is
the payoff on its own — so the hero is a single plated panel under a hard raking
key. What has to read is *hierarchy*: large plates, medium ones and small ones, with
seams running in continuous lines. That is the claim, so the light is angled to make
every seam and chamfer catch.

The icon is a plated block on the same slate field Conduit and Scuff use, framed down
the body diagonal exactly as Scuff's is, so the three read as one product line in a
grid of tiles.
"""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "addon"))
sys.path.insert(0, HERE)

OUT = os.environ.get("BULKHEAD_OUT", os.path.join(ROOT, "build", "store"))
os.makedirs(OUT, exist_ok=True)
SAMPLES = int(os.environ.get("BULKHEAD_SAMPLES", 96))

import bulkhead  # noqa: E402
import render_engine  # noqa: E402

BRAND = (0.055, 0.075, 0.115, 1.0)


def material(name, base, rough, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes["Principled BSDF"]
    n.inputs["Base Color"].default_value = base
    n.inputs["Roughness"].default_value = rough
    n.inputs["Metallic"].default_value = metal
    return m


def render(path, w, h):
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = w, h
    scene.render.image_settings.file_format = "PNG"
    render_engine.setup(scene, samples=SAMPLES)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"  wrote {path} ({w}x{h})")


# --------------------------------------------------------------------- featured
bpy.ops.wm.read_factory_settings(use_empty=True)
bulkhead.register()
scene = bpy.context.scene

world = bpy.data.worlds.new("W")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.014, 0.017, 0.023, 1)
scene.world = world

# Hard, low key: plating is depth, and depth only reads when light crosses it at an
# angle. A soft frontal light flattens exactly the chamfers being sold.
key = bpy.data.lights.new("Key", "AREA")
key.energy, key.size = 1600.0, 3.0
ko = bpy.data.objects.new("Key", key)
ko.location, ko.rotation_euler = (4.5, -3.5, 3.4), (0.92, 0.18, 0.90)
scene.collection.objects.link(ko)

rim = bpy.data.lights.new("Rim", "AREA")
rim.energy, rim.size, rim.color = 700.0, 5.0, (0.46, 0.63, 1.0)
ro = bpy.data.objects.new("Rim", rim)
ro.location, ro.rotation_euler = (-5.0, 3.5, 2.0), (1.18, 0.0, -2.25)
scene.collection.objects.link(ro)

# Close and low, aimed at the origin from (3.2, -3.6, 2.0):
# rot_x = atan2(hypot(3.2,3.6), 2.0) = 1.178, rot_z = atan2(3.2, 3.6) = 0.727.
#
# Two reasons for the low angle. A near-top-down view flattens the height steps,
# which are half of what is being sold. And at this distance the slab overflows the
# frame, so it reads as a section of a larger hull rather than a small tile floating
# in empty space.
cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 45.0
cam = bpy.data.objects.new("Cam", cam_data)
cam.location = (3.2, -3.6, 2.0)
cam.rotation_euler = (1.178, 0.0, 0.727)
scene.collection.objects.link(cam)
scene.camera = cam

bpy.ops.mesh.primitive_grid_add(x_subdivisions=3, y_subdivisions=3, size=4.0)
slab = bpy.context.active_object
slab.data.materials.append(material("Steel", (0.30, 0.32, 0.35, 1.0), 0.33, 0.9))
bpy.ops.bulkhead.plate(seed=12, use_features=True, density=0.42, max_depth=5,
                       min_size=0.07, gap=0.02, chamfer=0.005, base_height=0.03,
                       step_height=0.03, feature_height=0.022, cell=0.055,
                       vent_chance=0.3)
print(f"plated slab: {len(slab.data.polygons)} faces")

print("featured:")
render(os.path.join(OUT, "featured.png"), 1920, 1080)


# ------------------------------------------------------------------------- icon
bpy.ops.wm.read_factory_settings(use_empty=True)
bulkhead.unregister()
bulkhead.register()
scene = bpy.context.scene

bpy.ops.mesh.primitive_plane_add(size=40.0, location=(0.0, 8.0, 0.0),
                                 rotation=(1.5708, 0.0, 0.0))
bg = bpy.data.materials.new("Backdrop")
bg.use_nodes = True
nt = bg.node_tree
nt.nodes.remove(nt.nodes["Principled BSDF"])
emit = nt.nodes.new("ShaderNodeEmission")
emit.inputs[0].default_value = BRAND
nt.links.new(emit.outputs[0], nt.nodes["Material Output"].inputs[0])
bpy.context.active_object.data.materials.append(bg)

world = bpy.data.worlds.new("IconW")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = BRAND
scene.world = world

k = bpy.data.lights.new("K", "AREA")
k.energy, k.size = 1300.0, 4.0
ko = bpy.data.objects.new("K", k)
ko.location, ko.rotation_euler = (4.0, -4.0, 5.0), (0.66, 0.2, 0.78)
scene.collection.objects.link(ko)

f = bpy.data.lights.new("F", "AREA")
f.energy, f.size, f.color = 480.0, 6.0, (0.62, 0.76, 1.0)
fo = bpy.data.objects.new("F", f)
fo.location, fo.rotation_euler = (-4.0, -3.0, 0.5), (1.45, 0.0, -0.9)
scene.collection.objects.link(fo)

# Same framing as Scuff's icon: ortho down the body diagonal at 3.55, which leaves
# margin around a size-2 block (its diagonal silhouette spans about 2.83).
icam_data = bpy.data.cameras.new("IconCam")
icam_data.type = "ORTHO"
icam_data.ortho_scale = 3.55
icam = bpy.data.objects.new("IconCam", icam_data)
icam.location = (6.0, -6.0, 6.0)
icam.rotation_euler = (0.955, 0.0, 0.785)
scene.collection.objects.link(icam)
scene.camera = icam

bpy.ops.mesh.primitive_cube_add(size=2.0)
cube = bpy.context.active_object
cube.data.materials.append(material("IconSteel", (0.76, 0.79, 0.85, 1.0), 0.31, 0.35))
# Far coarser than the hero: at 256px a fine plate is a smudge, so the tile shows a
# handful of big plates at clearly different heights instead.
bpy.ops.bulkhead.plate(seed=6, use_features=True, density=0.3, max_depth=3,
                       min_size=0.18, gap=0.035, chamfer=0.012, base_height=0.05,
                       step_height=0.055, levels=3, feature_height=0.04, cell=0.16,
                       vent_chance=0.35)
print(f"icon block: {len(cube.data.polygons)} faces")

if os.environ.get("BULKHEAD_FEATURED_ONLY") != "1":
    print("icon (rendered at 1024, downsampled to 256):")
    render(os.path.join(OUT, "icon_1024.png"), 1024, 1024)
