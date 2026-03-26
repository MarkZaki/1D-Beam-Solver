from __future__ import annotations

from pathlib import Path

from matplotlib import patches

from beam import Beam, SupportType
from solver import BeamAnalysisResult, SupportReactions
from utils import linspace, slugify


def build_analysis_figures(result: BeamAnalysisResult) -> dict[str, object]:
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    palette = {
        "shear": "#C75C34",
        "moment": "#1F5E5B",
        "deflection": "#17324D",
    }
    plot_specs = (
        ("shear", result.shear_values, "Shear Force Diagram", "Shear Force (N)", True),
        (
            "moment",
            result.moment_values,
            "Bending Moment Diagram",
            "Bending Moment (N*m)",
            False,
        ),
        (
            "deflection",
            result.deflection_values,
            "Deflection Curve",
            "Deflection (m)",
            False,
        ),
    )

    figures: dict[str, object] = {}
    for suffix, y_values, title, ylabel, use_step in plot_specs:
        figure, axis = plt.subplots(figsize=(9, 4))
        figure.patch.set_facecolor("#FBF7EF")
        axis.set_facecolor("#FFFDFC")
        if use_step:
            axis.step(
                result.x_values,
                y_values,
                where="post",
                linewidth=2.4,
                color=palette[suffix],
            )
        else:
            axis.plot(
                result.x_values,
                y_values,
                linewidth=2.4,
                color=palette[suffix],
            )
        axis.axhline(0.0, color="#334155", linewidth=0.9)
        axis.set_title(title)
        axis.set_xlabel("Beam Position x (m)")
        axis.set_ylabel(ylabel)
        axis.grid(True, linestyle="--", linewidth=0.5, alpha=0.7)
        figure.tight_layout()
        figures[suffix] = figure

    return figures


def build_model_figure(
    beam: Beam,
    reactions: SupportReactions | None = None,
) -> object:
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    figure, axis = plt.subplots(figsize=(12, 4.2))
    figure.patch.set_facecolor("#FBF7EF")
    axis.set_facecolor("#FFFDFC")

    axis.plot(
        [0.0, beam.length],
        [0.0, 0.0],
        color="#17324D",
        linewidth=6,
        solid_capstyle="round",
    )

    _draw_supports(axis, beam)
    _draw_point_loads(axis, beam)
    _draw_distributed_loads(axis, beam)
    _draw_applied_moments(axis, beam)
    if reactions is not None:
        _draw_reactions(axis, beam, reactions)

    axis.set_xlim(-0.08 * beam.length, 1.08 * beam.length)
    axis.set_ylim(-2.0, 2.05)
    axis.set_title("Beam, Supports, and Applied Actions")
    axis.set_xlabel("Beam Position x (m)")
    axis.set_yticks([])
    axis.grid(True, axis="x", linestyle="--", linewidth=0.5, alpha=0.35)
    for spine in ("left", "right", "top"):
        axis.spines[spine].set_visible(False)

    figure.tight_layout()
    return figure


def save_analysis_plots(
    result: BeamAnalysisResult,
    output_dir: str = "generated_plots",
    stem: str | None = None,
) -> list[Path]:
    import matplotlib.pyplot as plt

    base_name = stem or slugify(result.beam.name or result.beam.support_type.value)
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    saved_paths: list[Path] = []
    for suffix, figure in build_analysis_figures(result).items():
        output_path = target_dir / f"{base_name}_{suffix}.png"
        figure.savefig(output_path, dpi=160)
        plt.close(figure)
        saved_paths.append(output_path)

    return saved_paths


def _draw_supports(axis, beam: Beam) -> None:
    if beam.support_type == SupportType.SIMPLY_SUPPORTED:
        left_support = patches.Polygon(
            [[0.0, -0.05], [-0.18, -0.48], [0.18, -0.48]],
            closed=True,
            facecolor="#DCE7E3",
            edgecolor="#17324D",
            linewidth=1.4,
        )
        axis.add_patch(left_support)
        for offset in (-0.1, 0.0, 0.1):
            axis.add_patch(
                patches.Circle(
                    (beam.length + offset, -0.38),
                    0.07,
                    facecolor="#DCE7E3",
                    edgecolor="#17324D",
                    linewidth=1.1,
                )
            )
        axis.add_patch(
            patches.Rectangle(
                (beam.length - 0.24, -0.31),
                0.48,
                0.06,
                facecolor="#17324D",
                edgecolor="#17324D",
            )
        )
    else:
        axis.add_patch(
            patches.Rectangle(
                (-0.26, -0.78),
                0.18,
                1.52,
                facecolor="#DCE7E3",
                edgecolor="#17324D",
                linewidth=1.5,
            )
        )
        for y_value in (-0.62, -0.34, -0.06, 0.22, 0.5):
            axis.plot(
                [-0.26, -0.08],
                [y_value, y_value + 0.18],
                color="#17324D",
                linewidth=1.0,
            )


def _draw_point_loads(axis, beam: Beam) -> None:
    for index, load in enumerate(beam.point_loads, start=1):
        is_downward = load.magnitude < 0.0
        start_y = 1.35 if is_downward else -1.25
        end_y = 0.16 if is_downward else -0.16
        axis.annotate(
            "",
            xy=(load.position, end_y),
            xytext=(load.position, start_y),
            arrowprops=dict(arrowstyle="-|>", lw=2.2, color="#C75C34"),
        )
        label_y = start_y + 0.12 if is_downward else start_y - 0.14
        axis.text(
            load.position,
            label_y,
            f"P{index}\n{load.magnitude:,.0f} N",
            ha="center",
            va="bottom" if is_downward else "top",
            color="#17324D",
            fontsize=9,
            fontweight="bold",
        )


def _draw_distributed_loads(axis, beam: Beam) -> None:
    for index, load in enumerate(beam.distributed_loads, start=1):
        sample_positions = linspace(load.start, load.end, 7)
        sample_values = [load.intensity_at(position) for position in sample_positions]
        max_abs_intensity = max(abs(value) for value in sample_values) or 1.0

        arrow_start_points: list[tuple[float, float]] = []
        for position, intensity in zip(sample_positions, sample_values):
            if abs(intensity) < 1e-9:
                continue

            is_downward = intensity < 0.0
            tip_y = 0.18 if is_downward else -0.18
            arrow_length = 0.45 + 0.55 * abs(intensity) / max_abs_intensity
            start_y = tip_y + arrow_length if is_downward else tip_y - arrow_length
            arrow_start_points.append((position, start_y))

            axis.annotate(
                "",
                xy=(position, tip_y),
                xytext=(position, start_y),
                arrowprops=dict(arrowstyle="-|>", lw=1.8, color="#B46A15"),
            )

        if arrow_start_points:
            axis.plot(
                [point[0] for point in arrow_start_points],
                [point[1] for point in arrow_start_points],
                color="#B46A15",
                linewidth=2.0,
            )
            average_intensity = sum(sample_values) / len(sample_values)
            label_y = (
                max(point[1] for point in arrow_start_points) + 0.12
                if average_intensity < 0.0
                else min(point[1] for point in arrow_start_points) - 0.18
            )
            axis.text(
                0.5 * (load.start + load.end),
                label_y,
                f"w{index}(x) = {load.expression}",
                ha="center",
                va="bottom" if average_intensity < 0.0 else "top",
                color="#17324D",
                fontsize=9,
                fontweight="bold",
            )


def _draw_applied_moments(axis, beam: Beam) -> None:
    for index, moment in enumerate(beam.applied_moments, start=1):
        center_y = 0.95
        if moment.magnitude >= 0.0:
            axis.add_patch(
                patches.Arc(
                    (moment.position, center_y),
                    0.62,
                    0.62,
                    theta1=40,
                    theta2=320,
                    linewidth=2.1,
                    color="#7A2E8E",
                )
            )
            axis.annotate(
                "",
                xy=(moment.position + 0.17, center_y + 0.24),
                xytext=(moment.position + 0.28, center_y - 0.03),
                arrowprops=dict(arrowstyle="-|>", lw=2.1, color="#7A2E8E"),
            )
        else:
            axis.add_patch(
                patches.Arc(
                    (moment.position, center_y),
                    0.62,
                    0.62,
                    theta1=220,
                    theta2=500,
                    linewidth=2.1,
                    color="#7A2E8E",
                )
            )
            axis.annotate(
                "",
                xy=(moment.position - 0.17, center_y + 0.24),
                xytext=(moment.position - 0.28, center_y - 0.03),
                arrowprops=dict(arrowstyle="-|>", lw=2.1, color="#7A2E8E"),
            )
        axis.text(
            moment.position,
            center_y + 0.5,
            f"M{index}\n{moment.magnitude:,.0f} N*m",
            ha="center",
            va="bottom",
            color="#17324D",
            fontsize=9,
            fontweight="bold",
        )


def _draw_reactions(axis, beam: Beam, reactions: SupportReactions) -> None:
    reaction_color = "#1F5E5B"
    if abs(reactions.left_force) > 1e-9:
        axis.annotate(
            "",
            xy=(0.0, 0.05 if reactions.left_force >= 0.0 else -0.05),
            xytext=(0.0, -1.35 if reactions.left_force >= 0.0 else 1.35),
            arrowprops=dict(arrowstyle="-|>", lw=2.0, color=reaction_color),
        )
        axis.text(
            0.0,
            -1.48 if reactions.left_force >= 0.0 else 1.48,
            f"R1 = {reactions.left_force:,.0f} N",
            ha="center",
            va="top" if reactions.left_force >= 0.0 else "bottom",
            color="#17324D",
            fontsize=9,
        )

    if beam.support_type == SupportType.SIMPLY_SUPPORTED and abs(reactions.right_force) > 1e-9:
        axis.annotate(
            "",
            xy=(beam.length, 0.05 if reactions.right_force >= 0.0 else -0.05),
            xytext=(beam.length, -1.35 if reactions.right_force >= 0.0 else 1.35),
            arrowprops=dict(arrowstyle="-|>", lw=2.0, color=reaction_color),
        )
        axis.text(
            beam.length,
            -1.48 if reactions.right_force >= 0.0 else 1.48,
            f"R2 = {reactions.right_force:,.0f} N",
            ha="center",
            va="top" if reactions.right_force >= 0.0 else "bottom",
            color="#17324D",
            fontsize=9,
        )

    if beam.support_type == SupportType.CANTILEVER and abs(reactions.fixed_end_moment) > 1e-9:
        anchor_x = 0.25
        center_y = -1.2
        axis.add_patch(
            patches.Arc(
                (anchor_x, center_y),
                0.52,
                0.52,
                theta1=40,
                theta2=320,
                linewidth=2.0,
                color=reaction_color,
            )
        )
        axis.annotate(
            "",
            xy=(anchor_x + 0.14, center_y + 0.21),
            xytext=(anchor_x + 0.23, center_y - 0.05),
            arrowprops=dict(arrowstyle="-|>", lw=2.0, color=reaction_color),
        )
        axis.text(
            anchor_x + 0.1,
            center_y - 0.4,
            f"M_fix = {reactions.fixed_end_moment:,.0f} N*m",
            ha="left",
            va="top",
            color="#17324D",
            fontsize=9,
        )
