"""Panel layout by recursive bisection.

The naive way to greeble a surface is to subdivide it into a grid and randomly
extrude cells. That reads as noise, and it is why most generated panelling looks
generated. Real plating reads as *designed*, and four properties are doing that work:

1. **Hierarchy** — a few large plates, more medium ones, many small ones. Recursion
   with a per-depth stopping chance produces that distribution naturally; a grid
   cannot produce it at all.
2. **Aligned seams** — recursive bisection means every internal seam spans its whole
   subtree, so panel lines run as continuous straight runs instead of jittering.
   This falls out of the algorithm rather than being patched on afterwards.
3. **Bounded aspect** — always bisecting the longer side keeps plates near-square.
   The legal split interval below enforces it exactly rather than hoping for it.
4. **Discrete heights** — plates land on a few machined levels, mostly flush. Give
   every plate its own random height and the result looks like a city skyline.

Pure Python, no `bpy`: the layout is the product, so it is tested directly.
"""
import random
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Panel:
    u0: float
    v0: float
    u1: float
    v1: float
    depth: int = 0
    level: int = 0

    @property
    def width(self):
        return self.u1 - self.u0

    @property
    def height(self):
        return self.v1 - self.v0

    @property
    def area(self):
        return self.width * self.height

    @property
    def aspect(self):
        w, h = self.width, self.height
        if w <= 0.0 or h <= 0.0:
            return float("inf")
        return max(w / h, h / w)

    @property
    def center(self):
        return (0.5 * (self.u0 + self.u1), 0.5 * (self.v0 + self.v1))


@dataclass
class PanelParams:
    max_depth: int = 4
    min_depth: int = 1
    min_size: float = 0.08
    max_aspect: float = 4.0
    split_jitter: float = 0.18
    stop_chance: float = 0.25
    levels: int = 3
    flush_bias: float = 0.55


def _sane(params):
    """Clamp user input into a workable range instead of raising at them."""
    return PanelParams(
        max_depth=max(0, int(params.max_depth)),
        min_depth=max(0, int(params.min_depth)),
        min_size=min(max(float(params.min_size), 1e-4), 0.5),
        max_aspect=max(1.0, float(params.max_aspect)),
        split_jitter=min(max(float(params.split_jitter), 0.0), 0.45),
        stop_chance=min(max(float(params.stop_chance), 0.0), 1.0),
        levels=max(1, int(params.levels)),
        flush_bias=min(max(float(params.flush_bias), 0.0), 1.0),
    )


def _legal_split(span, other, params):
    """The interval of split fractions that violates neither constraint.

    Splitting `span` at t yields pieces of size t*span and (1-t)*span, each paired
    with `other`. Requiring both to clear min_size and to stay under max_aspect:

        min_size/span              <= t <= 1 - min_size/span
        other/(max_aspect*span)    <= t <= 1 - other/(max_aspect*span)

    Returns (lo, hi), or None when no split can satisfy both.
    """
    if span <= 0.0:
        return None
    by_size = params.min_size / span
    by_aspect = other / (params.max_aspect * span)
    lo = max(by_size, by_aspect)
    hi = 1.0 - lo
    return (lo, hi) if lo < hi else None


def _split(rect, params, rng, out):
    if rect.depth >= params.max_depth:
        out.append(rect)
        return

    # Bisect the longer side; that single choice is what keeps plates from
    # degenerating into needles as the recursion deepens.
    along_u = rect.width >= rect.height
    span, other = (rect.width, rect.height) if along_u else (rect.height, rect.width)

    interval = _legal_split(span, other, params)
    if interval is None:
        # The long side cannot take a split — try the short one before giving up.
        along_u = not along_u
        span, other = (rect.width, rect.height) if along_u else (rect.height,
                                                                 rect.width)
        interval = _legal_split(span, other, params)
        if interval is None:
            out.append(rect)
            return

    # Stopping early at varying depths is what produces the size hierarchy.
    if rect.depth >= params.min_depth and rng.random() < params.stop_chance:
        out.append(rect)
        return

    lo, hi = interval
    t = 0.5 + rng.uniform(-params.split_jitter, params.split_jitter)
    t = min(max(t, lo), hi)

    d = rect.depth + 1
    if along_u:
        mid = rect.u0 + rect.width * t
        _split(Panel(rect.u0, rect.v0, mid, rect.v1, d), params, rng, out)
        _split(Panel(mid, rect.v0, rect.u1, rect.v1, d), params, rng, out)
    else:
        mid = rect.v0 + rect.height * t
        _split(Panel(rect.u0, rect.v0, rect.u1, mid, d), params, rng, out)
        _split(Panel(rect.u0, mid, rect.u1, rect.v1, d), params, rng, out)


def _level_for(params, rng):
    """Mostly flush, occasionally raised, higher steps progressively rarer."""
    if params.levels <= 1:
        return 0
    if rng.random() < params.flush_bias:
        return 0
    # The exponent skews the draw toward the lower steps, so a level-3 plate is a
    # rare accent rather than a third of the surface.
    step = int(rng.random() ** 1.7 * (params.levels - 1))
    return min(1 + step, params.levels - 1)


def layout(params=None, seed=0):
    """Panel the unit square. Deterministic for a given seed."""
    params = _sane(params or PanelParams())
    rng = random.Random(seed)

    panels = []
    _split(Panel(0.0, 0.0, 1.0, 1.0), params, rng, panels)
    return [replace(p, level=_level_for(params, rng)) for p in panels]
