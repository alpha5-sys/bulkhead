"""Build plating geometry from a layout.

Each selected quad becomes a patch of hull: the original face stays put as the
recessed floor that shows through the panel lines, and every plate is raised off it
as a prism. That is why the gaps read as machined seams rather than as holes.

Positions come from bilinear interpolation of the face corners, and the raise
direction from bilinear interpolation of the *vertex* normals, so plating follows a
curved hull instead of tenting off a flat average.
"""
import bmesh
from mathutils import Vector

from .core import features as feat
from .core import subdivide


def _bilinear(c, u, v):
    """Interpolate across a quad whose corners are in loop order."""
    a = c[0].lerp(c[1], u)
    b = c[3].lerp(c[2], u)
    return a.lerp(b, v)


def _bilinear_dir(n, u, v):
    a = n[0].lerp(n[1], u)
    b = n[3].lerp(n[2], u)
    out = a.lerp(b, v)
    return out.normalized() if out.length_squared > 1e-12 else Vector((0.0, 0.0, 1.0))


def _prism(bm, corners, normals, u0, v0, u1, v1, base_h, top_h,
           taper_u=0.0, taper_v=0.0):
    """One raised block spanning a uv rectangle. Returns its new faces.

    The top is inset slightly from the base, giving every plate a draft angle. That
    chamfer is what catches the key light along each edge and is the single largest
    difference between geometry that reads as machined plating and geometry that
    reads as floor tiles.

    Winding is correct by construction: u increases toward corner 1, v toward
    corner 3, so listing the top ring in uv order yields a face pointing along the
    surface normal, and each wall follows from it. `recalc_face_normals` must NOT be
    run over this: these prisms are open shells, and its heuristics flip them.
    """
    if u1 <= u0 or v1 <= v0:
        return []

    # Clamp the chamfer against *this* rectangle, not just against the face. A
    # world-space chamfer that is modest on a plate can be wider than half a vent
    # slat, and clamping it to the midpoint collapses the top face to a line, which
    # emits zero-area geometry.
    taper_u = min(taper_u, (u1 - u0) * 0.35)
    taper_v = min(taper_v, (v1 - v0) * 0.35)

    tu0, tu1 = u0 + taper_u, u1 - taper_u
    tv0, tv1 = v0 + taper_v, v1 - taper_v

    base_uvs = ((u0, v0), (u1, v0), (u1, v1), (u0, v1))
    top_uvs = ((tu0, tv0), (tu1, tv0), (tu1, tv1), (tu0, tv1))

    base, top = [], []
    for (bu, bv), (tu, tv) in zip(base_uvs, top_uvs):
        pb, db = _bilinear(corners, bu, bv), _bilinear_dir(normals, bu, bv)
        pt, dt = _bilinear(corners, tu, tv), _bilinear_dir(normals, tu, tv)
        base.append(bm.verts.new(pb + db * base_h))
        top.append(bm.verts.new(pt + dt * top_h))

    made = [bm.faces.new(top)]
    for i in range(4):
        j = (i + 1) % 4
        made.append(bm.faces.new((base[i], base[j], top[j], top[i])))
    for f in made:
        f.smooth = False
    return made


def _vent_slats(bm, corners, normals, f, base_h, top_h,
                taper_u=0.0, taper_v=0.0, count=4):
    """A vent is a run of thin slats, which reads instantly as hardware."""
    made = []
    along_u = (f.u1 - f.u0) >= (f.v1 - f.v0)
    span = (f.u1 - f.u0) if along_u else (f.v1 - f.v0)
    pitch = span / count
    for i in range(count):
        a = (f.u0 if along_u else f.v0) + i * pitch
        b = a + pitch * 0.55
        if along_u:
            made += _prism(bm, corners, normals, a, f.v0, b, f.v1, base_h, top_h,
                           taper_u, taper_v)
        else:
            made += _prism(bm, corners, normals, f.u0, a, f.v1, b, base_h, top_h,
                           taper_u, taper_v)
    return made


def plate_face(bm, face, settings, seed):
    """Panel a single quad. Returns the faces created."""
    if len(face.verts) != 4:
        return []

    corners = [v.co.copy() for v in face.verts]
    normals = [v.normal.copy() for v in face.verts]

    # Convert the world-space gap into uv, so seams keep a constant width whatever
    # size the face is. Without this, big faces get hairline seams and small faces
    # get chasms.
    du = (corners[1] - corners[0]).length or 1.0
    dv = (corners[3] - corners[0]).length or 1.0
    gap_u = min(settings.gap / du, 0.45)
    gap_v = min(settings.gap / dv, 0.45)
    chamfer_u = min(settings.chamfer / du, 0.2)
    chamfer_v = min(settings.chamfer / dv, 0.2)

    panels = subdivide.layout(settings.panel_params(), seed)
    made = []

    for index, panel in enumerate(panels):
        pu0, pv0 = panel.u0 + gap_u * 0.5, panel.v0 + gap_v * 0.5
        pu1, pv1 = panel.u1 - gap_u * 0.5, panel.v1 - gap_v * 0.5
        if pu1 <= pu0 or pv1 <= pv0:
            continue

        plate_top = settings.base_height + panel.level * settings.step_height
        made += _prism(bm, corners, normals, pu0, pv0, pu1, pv1, 0.0, plate_top,
                       chamfer_u, chamfer_v)

        if not settings.use_features:
            continue

        # Seeded per plate so that changing one plate's fittings does not reshuffle
        # every other plate on the model.
        import random
        rng = random.Random((seed * 1000003) ^ (index * 9176) ^ 0x9E3779B9)
        inner = subdivide.Panel(pu0, pv0, pu1, pv1)
        for f in feat.place(inner, settings.feature_params(), rng=rng):
            top = plate_top + f.level * settings.feature_height
            if f.kind == feat.VENT:
                made += _vent_slats(bm, corners, normals, f, plate_top, top,
                                    chamfer_u, chamfer_v)
            else:
                made += _prism(bm, corners, normals, f.u0, f.v0, f.u1, f.v1,
                               plate_top, top, chamfer_u, chamfer_v)

    return made


def plate_object(obj, settings, seed, selected_only=True):
    """Panel an object's faces in place. Returns (faces_panelled, faces_skipped)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    bm.normal_update()

    targets = [f for f in bm.faces if f.select] if selected_only else list(bm.faces)
    if selected_only and not targets:
        targets = list(bm.faces)

    made, skipped = [], 0
    for face in targets:
        if len(face.verts) != 4:
            skipped += 1
            continue
        made += plate_face(bm, face, settings, seed)

    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return len(targets) - skipped, skipped
