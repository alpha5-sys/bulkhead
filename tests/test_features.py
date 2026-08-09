"""Greeble placement.

Overlapping fittings read as damage rather than machinery, and a rejection-sampling
placer can loop for a long time on a crowded plate. Grid occupancy fixes both; these
tests hold it to that.
"""
import unittest

import _ctx  # noqa: F401
from bulkhead.core import features
from bulkhead.core.features import FeatureParams
from bulkhead.core.subdivide import Panel

PLATE = Panel(0.1, 0.2, 0.7, 0.9)


def overlap(a, b):
    du = min(a.u1, b.u1) - max(a.u0, b.u0)
    dv = min(a.v1, b.v1) - max(a.v0, b.v0)
    return du * dv if du > 0 and dv > 0 else 0.0


class TestPlacement(unittest.TestCase):
    def test_features_never_overlap(self):
        for seed in range(10):
            got = features.place(PLATE, FeatureParams(density=1.0), seed)
            for i, a in enumerate(got):
                for b in got[i + 1:]:
                    self.assertEqual(overlap(a, b), 0.0, f"seed {seed}")

    def test_features_stay_inside_the_plate(self):
        for seed in range(10):
            for f in features.place(PLATE, FeatureParams(density=1.0), seed):
                self.assertGreaterEqual(f.u0, PLATE.u0 - 1e-12)
                self.assertGreaterEqual(f.v0, PLATE.v0 - 1e-12)
                self.assertLessEqual(f.u1, PLATE.u1 + 1e-12)
                self.assertLessEqual(f.v1, PLATE.v1 + 1e-12)

    def test_features_respect_the_edge_margin(self):
        params = FeatureParams(margin=0.2, density=1.0)
        inset = params.margin * min(PLATE.width, PLATE.height)
        for f in features.place(PLATE, params, 1):
            self.assertGreaterEqual(f.u0, PLATE.u0 + inset - 1e-9)
            self.assertLessEqual(f.u1, PLATE.u1 - inset + 1e-9)

    def test_all_features_have_positive_area(self):
        for f in features.place(PLATE, FeatureParams(density=1.0), 2):
            self.assertGreater(f.area, 0.0)

    def test_kinds_are_known(self):
        for f in features.place(PLATE, FeatureParams(density=1.0), 3):
            self.assertIn(f.kind, features.KINDS)

    def test_vents_can_be_forced(self):
        got = features.place(PLATE, FeatureParams(density=1.0, vent_chance=1.0), 4)
        self.assertTrue(got)
        for f in got:
            self.assertEqual(f.kind, features.VENT)

    def test_raised_fittings_go_above_the_plate(self):
        got = features.place(PLATE, FeatureParams(density=1.0, vent_chance=0.0), 5)
        self.assertTrue(got)
        for f in got:
            self.assertGreater(f.level, 0)


class TestDensity(unittest.TestCase):
    def test_zero_density_places_nothing(self):
        self.assertEqual(features.place(PLATE, FeatureParams(density=0.0), 1), [])

    def test_more_density_places_more(self):
        low = len(features.place(PLATE, FeatureParams(density=0.15), 6))
        high = len(features.place(PLATE, FeatureParams(density=0.95), 6))
        self.assertGreater(high, low)

    def test_tiny_plates_stay_bare(self):
        speck = Panel(0.0, 0.0, 0.01, 0.01)
        self.assertEqual(features.place(speck, FeatureParams(density=1.0), 1), [])


class TestDeterminism(unittest.TestCase):
    def test_same_seed_same_result(self):
        p = FeatureParams(density=0.8)
        self.assertEqual(features.place(PLATE, p, 21), features.place(PLATE, p, 21))

    def test_no_dependence_on_global_random_state(self):
        import random
        p = FeatureParams(density=0.8)
        random.seed(0)
        a = features.place(PLATE, p, 7)
        random.seed(999)
        [random.random() for _ in range(30)]
        self.assertEqual(a, features.place(PLATE, p, 7))


class TestDegenerate(unittest.TestCase):
    def test_margin_that_eats_the_plate_places_nothing(self):
        self.assertEqual(features.place(PLATE, FeatureParams(margin=0.5), 1), [])

    def test_silly_params_do_not_raise(self):
        for p in (FeatureParams(density=-2.0), FeatureParams(cell=0.0),
                  FeatureParams(cell=-1.0), FeatureParams(max_level=0),
                  FeatureParams(margin=-1.0)):
            features.place(PLATE, p, 1)

    def test_terminates_on_a_crowded_plate(self):
        """Grid occupancy means bounded work; a retry loop would not guarantee it."""
        params = FeatureParams(density=1.0, cell=0.004)
        got = features.place(Panel(0.0, 0.0, 1.0, 1.0), params, 1)
        self.assertGreater(len(got), 0)


if __name__ == "__main__":
    unittest.main()
