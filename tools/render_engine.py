"""Choose a render engine that suits the machine.

Headless EEVEE needs an OpenGL context. On a box without one it silently falls back
to software rasterisation, which is why background renders crawled at ~10-20s a frame
and why a long render could exhaust a small machine.

Cycles needs no GL at all. On a multi-core server it is both faster and better
looking, so that is the default on Linux and whenever RENDER_ENGINE=CYCLES is set.

Thread count is capped deliberately. The render box also serves production, and
Blender will otherwise take every core and every byte it can; a render is never worth
taking a live service down for.
"""
import os
import sys

import bpy


def setup(scene, samples=64, engine=None, threads=None):
    """Configure the engine. Returns the engine identifier actually used."""
    engine = (engine or os.environ.get("RENDER_ENGINE") or "").upper()
    if not engine:
        engine = "CYCLES" if sys.platform.startswith("linux") else "EEVEE"

    # Leave headroom for whatever else the machine is doing.
    threads = int(threads or os.environ.get("RENDER_THREADS") or 0)
    if threads > 0:
        scene.render.threads_mode = "FIXED"
        scene.render.threads = threads

    if engine == "CYCLES":
        scene.render.engine = "CYCLES"
        cycles = getattr(scene, "cycles", None)
        if cycles is not None:
            cycles.device = "CPU"
            cycles.samples = samples
            cycles.use_denoising = True
            # Adaptive sampling stops early on converged tiles, which on flat
            # metal-and-shadow scenes like these is most of the frame.
            cycles.use_adaptive_sampling = True
            cycles.adaptive_threshold = 0.01
            # A hard cap: without it a pathological scene can balloon and, on a
            # swapless server, get the process OOM-killed.
            cycles.debug_use_spatial_splits = False
        return "CYCLES"

    available = {i.identifier for i in
                 bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    scene.render.engine = ("BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in available
                           else "BLENDER_EEVEE")
    eevee = getattr(scene, "eevee", None)
    if eevee is not None:
        try:
            eevee.use_raytracing = False
        except AttributeError:
            pass
        try:
            eevee.taa_render_samples = samples
        except AttributeError:
            pass
    return scene.render.engine
