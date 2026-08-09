"""Package Bulkhead into installable zips.

    python tools/build_addon.py

Produces both editions from the one source tree:

    build/dist/bulkhead-1.0.0.zip        paid edition
    build/dist/bulkhead_free-1.0.0.zip   free edition, for extensions.blender.org

Blender 4.2+ extension zips carry `blender_manifest.toml` at the archive root, not
inside a nested folder.
"""
import argparse
import os
import re
import shutil
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "addon", "bulkhead")
BUILD = os.path.join(ROOT, "build")
DIST = os.path.join(BUILD, "dist")

SKIP_DIRS = {"__pycache__", ".git"}
SKIP_SUFFIX = (".pyc", ".pyo", ".orig", ".rej")

EDITIONS = {
    # The paid edition takes the "_pro" id, not the plain one. The free edition is
    # what lives on extensions.blender.org, and that platform hosts only free GPL
    # add-ons -- calling it "Bulkhead Free" there is meaningless at best and reads as
    # an upsell tease at worst, which reviewers reject.
    #
    # The ids differ so the platform's auto-update can never quietly overwrite a
    # paying customer's build with the free one. The flip side is that both register
    # the same operator names, so having both installed at once clashes; the paid
    # listing and README say to remove the free edition first.
    "pro": {
        "id": "bulkhead_pro",
        "name": "Bulkhead Pro",
        "tagline": "Hull plating and greebles that look designed, not random",
    },
    "free": {
        "id": "bulkhead",
        "name": "Bulkhead",
        "tagline": "Hierarchical hull plating with aligned seams",
    },
}


def version():
    manifest = open(os.path.join(SRC, "blender_manifest.toml"), encoding="utf-8").read()
    match = re.search(r'^version\s*=\s*"([^"]+)"', manifest, re.M)
    if not match:
        raise SystemExit("no version in blender_manifest.toml")
    return match.group(1)


def stage(tier):
    """Copy the source into build/<tier>/ with that edition's flags baked in."""
    out = os.path.join(BUILD, tier)
    shutil.rmtree(out, ignore_errors=True)
    shutil.copytree(
        SRC, out,
        ignore=lambda d, names: [n for n in names
                                 if n in SKIP_DIRS or n.endswith(SKIP_SUFFIX)])

    meta = EDITIONS[tier]

    edition_py = os.path.join(out, "edition.py")
    text = open(edition_py, encoding="utf-8").read()
    text = re.sub(r'^TIER = ".*"$', f'TIER = "{tier}"', text, flags=re.M)
    open(edition_py, "w", encoding="utf-8").write(text)

    manifest_path = os.path.join(out, "blender_manifest.toml")
    text = open(manifest_path, encoding="utf-8").read()
    text = re.sub(r'^id = ".*"$', f'id = "{meta["id"]}"', text, flags=re.M)
    text = re.sub(r'^name = ".*"$', f'name = "{meta["name"]}"', text, flags=re.M)
    text = re.sub(r'^tagline = ".*"$', f'tagline = "{meta["tagline"]}"', text,
                  flags=re.M)
    open(manifest_path, "w", encoding="utf-8").write(text)

    # The extensions platform expects the licence text alongside the SPDX id in the
    # manifest, so it ships inside the zip rather than only living in the repo.
    licence = os.path.join(ROOT, "LICENSE")
    if os.path.exists(licence):
        shutil.copy2(licence, os.path.join(out, "LICENSE"))

    return out


def archive(staged, tier):
    os.makedirs(DIST, exist_ok=True)
    name = f'{EDITIONS[tier]["id"]}-{version()}.zip'
    path = os.path.join(DIST, name)

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for folder, dirs, files in os.walk(staged):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for filename in sorted(files):
                if filename.endswith(SKIP_SUFFIX):
                    continue
                full = os.path.join(folder, filename)
                # Manifest at the archive root is what makes it an extension.
                zf.write(full, os.path.relpath(full, staged))
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tier", choices=("pro", "free", "all"), default="all")
    args = parser.parse_args()

    tiers = ("pro", "free") if args.tier == "all" else (args.tier,)
    for tier in tiers:
        staged = stage(tier)
        path = archive(staged, tier)
        size = os.path.getsize(path) / 1024.0
        print(f"{tier:5}  {os.path.basename(path)}  ({size:.0f} KB)")

    print(f"\ndist: {DIST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
