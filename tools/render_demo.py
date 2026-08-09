"""Render the demo animation.

    blender --background --factory-startup --python tools/render_demo.py

A slow orbit with a hard raking key. Panelling is depth, and depth only reads when
the light moves across it — a static hero shot flattens exactly the chamfers and
height steps that the product is selling.
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "addon"))

FRAMES = int(os.environ.get("BULKHEAD_FRAMES", 60))
W = int(os.environ.get("BULKHEAD_W", 960))
H = int(os.environ.get("BULKHEAD_H", 540))
SAMPLES = int(os.environ.get("BULKHEAD_SAMPLES", 64))
OUT = os.environ.get("BULKHEAD_OUT", os.path.join(ROOT, "build", "demo", "frames"))
os.makedirs(OUT, exist_ok=True)

import bulkhead  # noqa: E402

bpy.ops.wm.read_factory_settings(use_empty=True)
bulkhead.register()

scene = bpy.context.scene
scene.render.fps = 24


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
world.node_tree.nodes["Background"].inputs[0].default_value = (0.015, 0.018, 0.024, 1)
scene.world = world

key = bpy.data.lights.new("Key", "AREA")
key.energy, key.size = 1500.0, 3.0
ko = bpy.data.objects.new("Key", key)
ko.location, ko.rotation_euler = (4.0, -3.0, 3.2), (0.95, 0.15, 0.92)
scene.collection.objects.link(ko)

rim = bpy.data.lights.new("Rim", "AREA")
rim.energy, rim.size, rim.color = 700.0, 4.0, (0.45, 0.62, 1.0)
ro = bpy.data.objects.new("Rim", rim)
ro.location, ro.rotation_euler = (-4.5, 3.5, 2.2), (1.15, 0.0, -2.25)
scene.collection.objects.link(ro)

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 50.0
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

# A slab, plated once. The animation is camera and light, not regeneration: the
# point is that this is one piece of geometry that holds up under a moving light.
bpy.ops.mesh.primitive_grid_add(x_subdivisions=3, y_subdivisions=3, size=4.0)
obj = bpy.context.active_object
obj.data.materials.append(material("Steel", (0.26, 0.28, 0.31, 1.0), 0.32, 0.9))
bpy.ops.bulkhead.plate(seed=12, use_features=True, density=0.45, max_depth=5,
                       min_size=0.06, gap=0.02, chamfer=0.005, base_height=0.03,
                       step_height=0.028, feature_height=0.022, cell=0.055,
                       vent_chance=0.28)
print(f"plated: {len(obj.data.polygons)} faces")

sys.path.insert(0, HERE)
import render_engine  # noqa: E402

scene.render.resolution_x, scene.render.resolution_y = W, H
scene.render.image_settings.file_format = "PNG"
engine = render_engine.setup(scene, samples=SAMPLES)
print(f"engine: {engine}")

RADIUS, HEIGHT = 5.2, 3.0

for frame in range(FRAMES):
    t = frame / FRAMES
    angle = math.tau * t

    cam.location = (RADIUS * math.sin(angle), -RADIUS * math.cos(angle), HEIGHT)
    # Aim at the origin: yaw follows the orbit, pitch from the camera's height.
    cam.rotation_euler = (math.atan2(math.hypot(cam.location[0], cam.location[1]),
                                     HEIGHT), 0.0, angle)

    # Counter-rotate the key a little so the raking direction keeps changing
    # instead of riding along with the camera.
    lift = math.radians(18.0) * math.sin(angle * 2.0)
    ko.location = (4.0 * math.cos(angle * 0.5 + 0.4),
                   -3.0 * math.cos(angle * 0.5),
                   3.2 + lift)
    ko.rotation_euler = (0.95 + lift, 0.15, 0.92 + angle * 0.5)

    bpy.context.view_layer.update()
    scene.render.filepath = os.path.join(OUT, f"f{frame:04d}.png")
    bpy.ops.render.render(write_still=True)
    if frame % 15 == 0:
        print(f"  frame {frame}/{FRAMES}")

print(f"frames in {OUT}")
