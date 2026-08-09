"""Which features this build ships.

Bulkhead is published as two builds from one source tree: a free edition on the
Blender Extensions platform, which is where discovery happens, and a full edition
that is sold. `tools/build_addon.py` rewrites TIER when it packages the free build.

Licensing, stated plainly: a Blender add-on links Blender's Python API and is
therefore GPL, and this one is GPL-3.0-or-later like every other add-on sold for
Blender. The paid edition is not, and cannot be, DRM'd — what is sold is the build,
the updates and the support, exactly as the rest of the Blender add-on market works.
"""

TIER = "pro"

IS_PRO = TIER == "pro"

# Free ships the part that carries the whole look: hierarchical plating with aligned
# seams and machined height steps. It is a real tool, not a crippled demo.
HAS_FEATURES = IS_PRO
HAS_PRESETS = IS_PRO

LABEL = "Bulkhead Pro" if IS_PRO else "Bulkhead"
