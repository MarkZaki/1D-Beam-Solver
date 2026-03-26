from __future__ import annotations

import unittest

from app import build_custom_beam


class AppHelpersTests(unittest.TestCase):
    def test_custom_beam_builder_accepts_signed_and_functional_loads(self) -> None:
        beam = build_custom_beam(
            support_type="simply_supported",
            length=6.0,
            elasticity=200e9,
            inertia=9e-6,
            point_loads=[
                {"magnitude": -8_000.0, "position": 2.0},
                {"magnitude": 4_000.0, "position": 4.5},
            ],
            distributed_loads=[
                {"expression": "-150 - 10*x", "start": 1.0, "end": 3.5},
            ],
            applied_moments=[
                {"magnitude": 2_000.0, "position": 3.0},
            ],
        )

        self.assertEqual(len(beam.point_loads), 2)
        self.assertEqual(len(beam.distributed_loads), 1)
        self.assertEqual(len(beam.applied_moments), 1)
        self.assertEqual(beam.distributed_loads[0].expression, "-150 - 10*x")


if __name__ == "__main__":
    unittest.main()
