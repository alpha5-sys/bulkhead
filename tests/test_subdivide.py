"""The panel layout algorithm.

What separates hard-surface panelling that reads as *designed* from panelling that
reads as noise is not the amount of detail — it is hierarchy, aligned seams, bounded
aspect ratios, and heights that land on a few machined levels rather than anywhere.
These tests assert those properties directly, because they are the product.
"""
import unittest

import _ctx  # noqa: F401
from bulkhead.core import subdivide
from bulkhead.core.subdivide import PanelParams


def overlap(a, b):
    """Area of intersection of two panels."""
    du = min(a.u1, b.u1) - max(a.u0, b.u0)
    dv = min(a.v1, b.v1) - max(a.v0, b.v0)
    return du * dv if du > 0 and dv > 0 else 0.0


class TestTiling(unittest.TestCase):
    """A panelled surface with holes or double-stacked plates is a broken mesh."""

    def test_panels_exactly_cover_the_surface(self):
        for seed in range(8):
            with self.subTest(seed=seed):
                panels = subdivide.layout(PanelParams(), seed)
                self.assertAlmostEqual(sum(p.area for p in panels), 1.0, places=9)

    def test_panels_never_overlap(self):
        for seed in range(6):
            panels = subdivide.layout(PanelParams(), seed)
            for i, a in enumerate(panels):
                for b in panels[i + 1:]:
                    self.assertEqual(overlap(a, b), 0.0,
                                     f"seed {seed}: {a} overlaps {b}")

    def test_panels_stay_inside_the_surface(self):
        for p in subdivide.layout(PanelParams(), 3):
            self.assertGreaterEqual(p.u0, -1e-12)
            self.assertGreaterEqual(p.v0, -1e-12)
            self.assertLessEqual(p.u1, 1.0 + 1e-12)
            self.assertLessEqual(p.v1, 1.0 + 1e-12)

    def test_every_panel_has_positive_area(self):
        for p in subdivide.layout(PanelParams(), 5):
            self.assertGreater(p.area, 0.0)


class TestQuality(unittest.TestCase):
    """The properties that make the output look machined instead of random."""

    def test_no_panel_is_a_sliver(self):
        params = PanelParams(min_size=0.10)
        for seed in range(8):
            for p in subdivide.layout(params, seed):
                self.assertGreaterEqual(p.width, params.min_size - 1e-9)
                self.assertGreaterEqual(p.height, params.min_size - 1e-9)

    def test_aspect_ratio_stays_bounded(self):
        """Always splitting the longer side is what stops plates becoming needles."""
        for seed in range(8):
            for p in subdivide.layout(PanelParams(), seed):
                self.assertLess(p.aspect, 6.0, f"seed {seed}: needle {p}")

    def test_layout_has_hierarchy_not_uniform_cells(self):
        """A grid of equal plates is the tell of a cheap generator."""
        for seed in range(6):
            areas = sorted(p.area for p in subdivide.layout(PanelParams(), seed))
            self.assertGreater(areas[-1] / areas[0], 2.0,
                               f"seed {seed}: plates are all the same size")

    def test_depth_never_exceeds_the_limit(self):
        params = PanelParams(max_depth=3)
        for p in subdivide.layout(params, 1):
            self.assertLessEqual(p.depth, params.max_depth)

    def test_deeper_limit_gives_more_panels(self):
        shallow = len(subdivide.layout(PanelParams(max_depth=2), 7))
        deep = len(subdivide.layout(PanelParams(max_depth=6), 7))
        self.assertGreater(deep, shallow)

    def test_seams_are_shared_not_jittered(self):
        """Recursive bisection means an internal seam spans its whole subtree, so
        every internal edge is shared by the panels on both sides of it. That is
        what makes the seams read as continuous runs rather than noise."""
        panels = subdivide.layout(PanelParams(), 2)
        us = [round(p.u0, 9) for p in panels] + [round(p.u1, 9) for p in panels]
        internal = [u for u in us if 1e-9 < u < 1.0 - 1e-9]
        for u in set(internal):
            self.assertGreaterEqual(internal.count(u), 2, f"orphan seam at u={u}")


class TestHeightLevels(unittest.TestCase):
    def test_levels_are_discrete_and_in_range(self):
        params = PanelParams(levels=4)
        for p in subdivide.layout(params, 4):
            self.assertIsInstance(p.level, int)
            self.assertGreaterEqual(p.level, 0)
            self.assertLess(p.level, params.levels)

    def test_most_panels_sit_flush(self):
        """Uniformly random heights look like a skyline. Real plating is mostly
        flush with occasional raised plates."""
        panels = subdivide.layout(PanelParams(levels=4, flush_bias=0.6), 11)
        flush = sum(1 for p in panels if p.level == 0)
        self.assertGreater(flush / len(panels), 0.35)

    def test_single_level_leaves_everything_flush(self):
        for p in subdivide.layout(PanelParams(levels=1), 6):
            self.assertEqual(p.level, 0)


class TestDeterminism(unittest.TestCase):
    def test_same_seed_gives_the_same_layout(self):
        a = subdivide.layout(PanelParams(), 42)
        b = subdivide.layout(PanelParams(), 42)
        self.assertEqual(a, b)

    def test_different_seeds_give_different_layouts(self):
        a = subdivide.layout(PanelParams(), 1)
        b = subdivide.layout(PanelParams(), 2)
        self.assertNotEqual(a, b)

    def test_no_dependence_on_global_random_state(self):
        import random
        random.seed(0)
        a = subdivide.layout(PanelParams(), 9)
        random.seed(12345)
        [random.random() for _ in range(50)]
        b = subdivide.layout(PanelParams(), 9)
        self.assertEqual(a, b)


class TestDegenerate(unittest.TestCase):
    def test_min_size_larger_than_surface_yields_one_panel(self):
        panels = subdivide.layout(PanelParams(min_size=2.0), 0)
        self.assertEqual(len(panels), 1)
        self.assertAlmostEqual(panels[0].area, 1.0, places=12)

    def test_zero_depth_yields_one_panel(self):
        self.assertEqual(len(subdivide.layout(PanelParams(max_depth=0), 0)), 1)

    def test_extreme_jitter_still_respects_min_size(self):
        params = PanelParams(split_jitter=0.99, min_size=0.12)
        for p in subdivide.layout(params, 3):
            self.assertGreaterEqual(p.width, params.min_size - 1e-9)
            self.assertGreaterEqual(p.height, params.min_size - 1e-9)

    def test_negative_or_silly_params_do_not_raise(self):
        for params in (PanelParams(max_depth=-5), PanelParams(min_size=-1.0),
                       PanelParams(levels=0), PanelParams(split_jitter=-3.0)):
            panels = subdivide.layout(params, 1)
            self.assertGreaterEqual(len(panels), 1)
            self.assertAlmostEqual(sum(p.area for p in panels), 1.0, places=9)


if __name__ == "__main__":
    unittest.main()
