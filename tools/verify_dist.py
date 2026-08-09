"""Verify the packaged zips, not the source tree.

    blender --background --factory-startup --python tools/verify_dist.py

Everything else tests `addon/`. This tests what is actually shipped: that each zip
extracts, registers, plates a mesh, and that the free edition really has fittings
withheld. Shipping a "free" build that quietly contains everything would be an
expensive mistake to discover after the fact.
"""
import glob
import os
import shutil
import sys
import tempfile
import zipfile

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "build", "dist")

_failures = []


def check(label, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {label}  {detail if not ok else ''}".rstrip())
    if not ok:
        _failures.append(label)


def load(zip_path, workdir):
    with zipfile.ZipFile(zip_path) as zf:
        assert "blender_manifest.toml" in zf.namelist(), "manifest must be at the root"
        zf.extractall(os.path.join(workdir, "bulkhead"))
    sys.path.insert(0, workdir)
    for mod in [m for m in sys.modules
                if m == "bulkhead" or m.startswith("bulkhead.")]:
        del sys.modules[mod]
    import bulkhead
    return bulkhead


def exercise(zip_path, expect_pro):
    name = os.path.basename(zip_path)
    print(f"\n=== {name} ===")
    workdir = tempfile.mkdtemp(prefix="bulkhead_dist_")
    try:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        mod = load(zip_path, workdir)
        mod.register()

        from bulkhead import edition
        check("edition tier is correct", edition.IS_PRO is expect_pro,
              f"IS_PRO={edition.IS_PRO}")
        check("fittings gated correctly", edition.HAS_FEATURES is expect_pro)

        bpy.ops.mesh.primitive_grid_add(x_subdivisions=2, y_subdivisions=2, size=2.0)
        obj = bpy.context.active_object
        check("plates a surface",
              bpy.ops.bulkhead.plate(seed=1, use_features=False) == {"FINISHED"})
        plain = len(obj.data.polygons)

        # Asking for fittings must only produce them in the licensed build.
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=2, y_subdivisions=2, size=2.0)
        obj = bpy.context.active_object
        bpy.ops.bulkhead.plate(seed=1, use_features=True, density=0.7)
        with_fittings = len(obj.data.polygons)
        check("fittings appear only when licensed",
              (with_fittings > plain) is expect_pro,
              f"{plain} -> {with_fittings}")

        mod.unregister()
        check("unregisters cleanly", True)
    except Exception as exc:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        check(f"{name} raised", False, str(exc))
    finally:
        if workdir in sys.path:
            sys.path.remove(workdir)
        shutil.rmtree(workdir, ignore_errors=True)


zips = sorted(glob.glob(os.path.join(DIST, "*.zip")))
if not zips:
    print("no zips in build/dist — run tools/build_addon.py first")
    sys.exit(1)

for path in zips:
    exercise(path, expect_pro="_free" not in os.path.basename(path))

print("\n" + "=" * 50)
if _failures:
    print(f"FAILED: {len(_failures)}")
    for f in _failures:
        print("  - " + f)
    sys.exit(1)
print("OK  both editions verified")
