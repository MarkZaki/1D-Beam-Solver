from __future__ import annotations

import unittest

from beam import Beam, SupportType
from solver import calculate_reactions, evaluate_moment, evaluate_response_at, solve_beam


def build_simply_supported_center_load_beam() -> Beam:
    beam = Beam(
        length=4.0,
        elasticity=200e9,
        inertia=8e-6,
        support_type=SupportType.SIMPLY_SUPPORTED,
        name="Simply Supported Center Load",
    )
    beam.add_point_load(magnitude=-10_000.0, position=2.0)
    return beam


def build_cantilever_end_load_beam() -> Beam:
    beam = Beam(
        length=3.0,
        elasticity=210e9,
        inertia=6e-6,
        support_type=SupportType.CANTILEVER,
        name="Cantilever End Load",
    )
    beam.add_point_load(magnitude=-5_000.0, position=3.0)
    return beam


def build_simply_supported_udl_beam() -> Beam:
    beam = Beam(
        length=5.0,
        elasticity=200e9,
        inertia=12e-6,
        support_type=SupportType.SIMPLY_SUPPORTED,
        name="Simply Supported Full Span UDL",
    )
    beam.add_distributed_load(expression="-3000", start=0.0, end=5.0)
    return beam


def build_cantilever_udl_beam() -> Beam:
    beam = Beam(
        length=2.5,
        elasticity=210e9,
        inertia=7e-6,
        support_type=SupportType.CANTILEVER,
        name="Cantilever Full Span UDL",
    )
    beam.add_distributed_load(expression="-2500", start=0.0, end=2.5)
    return beam


class SolverBehaviorTests(unittest.TestCase):
    def test_simply_supported_center_load_matches_reference_values(self) -> None:
        result = solve_beam(build_simply_supported_center_load_beam(), samples=1201)

        self.assertAlmostEqual(result.reactions.left_force, 5_000.0)
        self.assertAlmostEqual(result.reactions.right_force, 5_000.0)
        self.assertAlmostEqual(result.max_abs_moment, 10_000.0, places=5)
        self.assertAlmostEqual(
            result.max_abs_deflection,
            (10_000.0 * 4.0**3) / (48.0 * 200e9 * 8e-6),
            delta=5e-5,
        )

    def test_cantilever_end_load_matches_reference_values(self) -> None:
        result = solve_beam(build_cantilever_end_load_beam(), samples=1201)

        self.assertAlmostEqual(result.reactions.left_force, 5_000.0)
        self.assertAlmostEqual(result.reactions.fixed_end_moment, 15_000.0)
        self.assertAlmostEqual(result.max_abs_moment, 15_000.0, places=5)
        self.assertAlmostEqual(
            result.max_abs_deflection,
            (5_000.0 * 3.0**3) / (3.0 * 210e9 * 6e-6),
            delta=5e-5,
        )

    def test_full_span_udl_cases_match_reference_values(self) -> None:
        cases = (
            (
                build_simply_supported_udl_beam(),
                7_500.0,
                7_500.0,
                (3_000.0 * 5.0**2) / 8.0,
                5.0 * 3_000.0 * 5.0**4 / (384.0 * 200e9 * 12e-6),
            ),
            (
                build_cantilever_udl_beam(),
                6_250.0,
                0.0,
                (2_500.0 * 2.5**2) / 2.0,
                (2_500.0 * 2.5**4) / (8.0 * 210e9 * 7e-6),
            ),
        )

        for beam, left_reaction, right_reaction, max_moment, max_deflection in cases:
            with self.subTest(beam=beam.name):
                result = solve_beam(beam, samples=1201)
                self.assertAlmostEqual(result.reactions.left_force, left_reaction, places=5)
                self.assertAlmostEqual(result.reactions.right_force, right_reaction, places=5)
                self.assertAlmostEqual(result.max_abs_moment, max_moment, delta=0.2)
                self.assertAlmostEqual(
                    result.max_abs_deflection,
                    max_deflection,
                    delta=6e-5,
                )

    def test_linear_distributed_load_expression_supports_x_and_uppercase_x(self) -> None:
        beam = Beam(
            length=10.0,
            elasticity=200e9,
            inertia=9e-6,
            support_type=SupportType.SIMPLY_SUPPORTED,
            name="Linear Expression UDL",
        )
        beam.add_distributed_load(expression="-250 - 20X", start=2.0, end=6.0)

        result = solve_beam(beam, samples=1201)
        self.assertAlmostEqual(result.reactions.left_force, 781.3333333333, places=3)
        self.assertAlmostEqual(result.reactions.right_force, 538.6666666667, places=3)
        self.assertAlmostEqual(result.shear_values[-1], 0.0, places=4)

    def test_partial_span_udl_reactions_use_correct_resultant_and_centroid(self) -> None:
        beam = Beam(
            length=6.0,
            elasticity=200e9,
            inertia=9e-6,
            support_type=SupportType.SIMPLY_SUPPORTED,
        )
        beam.add_distributed_load(expression="-1000", start=1.0, end=3.0)

        reactions = calculate_reactions(beam)
        self.assertAlmostEqual(reactions.left_force, 1_333.3333333333, places=5)
        self.assertAlmostEqual(reactions.right_force, 666.6666666667, places=5)

    def test_bending_moment_is_zero_at_simple_supports(self) -> None:
        beam = build_simply_supported_center_load_beam()
        reactions = calculate_reactions(beam)

        self.assertAlmostEqual(evaluate_moment(beam, reactions, 0.0), 0.0, places=8)
        self.assertAlmostEqual(evaluate_moment(beam, reactions, beam.length), 0.0, places=8)

    def test_response_probe_interpolates_deflection_and_slope(self) -> None:
        result = solve_beam(build_simply_supported_center_load_beam(), samples=1201)
        response = evaluate_response_at(result, 2.0)

        self.assertAlmostEqual(response.position, 2.0, places=8)
        self.assertAlmostEqual(response.shear, -5_000.0, places=3)
        self.assertAlmostEqual(response.moment, 10_000.0, places=3)
        self.assertLess(response.deflection, 0.0)

    def test_applied_moment_changes_reactions_and_bending_jump(self) -> None:
        beam = Beam(
            length=4.0,
            elasticity=200e9,
            inertia=8e-6,
            support_type=SupportType.SIMPLY_SUPPORTED,
        )
        beam.add_applied_moment(magnitude=2_000.0, position=2.0)

        reactions = calculate_reactions(beam)
        self.assertAlmostEqual(reactions.left_force, -500.0, places=6)
        self.assertAlmostEqual(reactions.right_force, 500.0, places=6)
        self.assertAlmostEqual(evaluate_moment(beam, reactions, 1.0), -500.0, places=6)
        self.assertAlmostEqual(evaluate_moment(beam, reactions, 3.0), 500.0, places=6)


if __name__ == "__main__":
    unittest.main()
