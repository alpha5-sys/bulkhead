"""Greebles: the small hardware that sits on a plate.

Scattering boxes at random positions produces overlapping clutter that reads as
damage rather than machinery. Real hardware is bolted to a grid, set in from the
plate edge, and leaves clear runs of bare metal between fittings.

So placement is grid-occupancy rather than rejection sampling: features claim whole
cells, which makes overlap impossible by construction instead of by retrying, gives
the alignment that reads as manufactured, and terminates in bounded time.
"""
import random
from dataclasses import dataclass

BOX = "BOX"
VENT = "VENT"

KINDS = (BOX, VENT)

# A recessed fitting would need the plate's top face to carry a hole, and bmesh has
# no faces-with-holes. Faking it by drawing a well under a solid top renders as
# nothing at all, so recesses are left out rather than shipped broken. Height
# variation between plates already supplies the recessed channels artists want.


@dataclass(frozen=True)
class Feature:
    u0: float
    v0: float
    u1: float
    v1: float
    kind: str = BOX
    level: int = 1

    @property
    def width(self):
        return self.u1 - self.u0

    @property
    def height(self):
        return self.v1 - self.v0

    @property
    def area(self):
        return self.width * self.height


@dataclass
class FeatureParams:
    density: float = 0.35        # fraction of grid cells to try to fill
    cell: float = 0.045          # target cell size, in surface uv units
    margin: float = 0.14         # inset from the plate edge, as a fraction
    min_panel: float = 0.004     # plates smaller than this stay bare
    vent_chance: float = 0.22
    max_level: int = 2


def _sane(params):
    return FeatureParams(
        density=min(max(float(params.density), 0.0), 1.0),
        cell=min(max(float(params.cell), 1e-3), 0.5),
        # 0.5 insets half the plate from each side, which legitimately leaves no
        # room — the core reports that honestly by placing nothing. The UI slider
        # stops at 0.45 so it is not reachable by accident.
        margin=min(max(float(params.margin), 0.0), 0.5),
        min_panel=max(float(params.min_panel), 0.0),
        vent_chance=min(max(float(params.vent_chance), 0.0), 1.0),
        max_level=max(1, int(params.max_level)),
    )


# Footprints a fitting may claim, in cells. Mostly single cells, with the occasional
# longer unit so the plate does not read as uniform studs.
_FOOTPRINTS = ((1, 1), (1, 1), (1, 1), (2, 1), (1, 2), (2, 2), (3, 1), (1, 3))


def place(panel, params=None, seed=0, rng=None):
    """Place fittings on one plate. Deterministic for a given seed."""
    params = _sane(params or FeatureParams())
    rng = rng or random.Random(seed)

    if panel.area < params.min_panel or params.density <= 0.0:
        return []

    inset = params.margin * min(panel.width, panel.height)
    u0, v0 = panel.u0 + inset, panel.v0 + inset
    u1, v1 = panel.u1 - inset, panel.v1 - inset
    if u1 <= u0 or v1 <= v0:
        return []

    span_u, span_v = u1 - u0, v1 - v0
    nu = max(1, int(round(span_u / params.cell)))
    nv = max(1, int(round(span_v / params.cell)))
    cu, cv = span_u / nu, span_v / nv

    occupied = set()
    out = []
    # Bounded work: proportional to the grid, never a retry-until-it-fits loop.
    attempts = int(nu * nv * params.density) + 1

    for _ in range(attempts):
        ci = rng.randrange(nu)
        cj = rng.randrange(nv)
        fw, fh = _FOOTPRINTS[rng.randrange(len(_FOOTPRINTS))]
        if ci + fw > nu or cj + fh > nv:
            fw, fh = 1, 1

        cells = [(ci + a, cj + b) for a in range(fw) for b in range(fh)]
        if any(c in occupied for c in cells):
            continue
        occupied.update(cells)

        kind = VENT if rng.random() < params.vent_chance else BOX
        level = 1 + rng.randrange(params.max_level)

        # Shrink slightly inside the claimed cells so neighbouring fittings read as
        # separate objects rather than one welded mass.
        pad_u, pad_v = cu * 0.12, cv * 0.12
        out.append(Feature(
            u0 + ci * cu + pad_u, v0 + cj * cv + pad_v,
            u0 + (ci + fw) * cu - pad_u, v0 + (cj + fh) * cv - pad_v,
            kind, level))

    return out
