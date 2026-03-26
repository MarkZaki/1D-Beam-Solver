from __future__ import annotations

import tempfile
import unittest

from beam import Beam, SupportType
from plots import build_model_figure, save_analysis_plots
from solver import solve_beam


def build_plot_test_beam() -> Beam:
    beam = Beam(
        length=4.0,
        elasticity=200e9,
        inertia=8e-6,
        support_type=SupportType.SIMPLY_SUPPORTED,
        name="Plot Test Beam",
    )
    beam.add_point_load(magnitude=-10_000.0, position=2.0)
    return beam


class PlotGenerationTests(unittest.TestCase):
    def test_plot_files_are_created(self) -> None:
        result = solve_beam(build_plot_test_beam(), samples=401)

        with tempfile.TemporaryDirectory() as temp_dir:
            saved_paths = save_analysis_plots(result, output_dir=temp_dir, stem="verification")

            self.assertEqual(len(saved_paths), 3)
            for path in saved_paths:
                self.assertTrue(path.exists())
                self.assertGreater(path.stat().st_size, 0)

    def test_model_figure_can_render_beam_actions(self) -> None:
        beam = Beam(
            length=3.0,
            elasticity=210e9,
            inertia=6e-6,
            support_type=SupportType.CANTILEVER,
            name="Model Figure Test Beam",
        )
        beam.add_point_load(magnitude=-5_000.0, position=3.0)
        beam.add_distributed_load(expression="-250 - 20*x", start=0.5, end=2.2)
        beam.add_applied_moment(magnitude=1_500.0, position=1.5)
        result = solve_beam(beam, samples=401)

        figure = build_model_figure(result.beam, reactions=result.reactions)
        self.assertIsNotNone(figure)
        self.assertEqual(len(figure.axes), 1)


if __name__ == "__main__":
    unittest.main()
