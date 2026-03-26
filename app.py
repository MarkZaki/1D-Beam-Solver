from __future__ import annotations

import streamlit as st

from beam import Beam, SupportType
from plots import build_analysis_figures, build_model_figure
from solver import BeamAnalysisResult, evaluate_response_at, solve_beam
from utils import format_deflection, format_force, format_moment


def build_custom_beam(
    *,
    support_type: str,
    length: float,
    elasticity: float,
    inertia: float,
    point_loads: list[dict[str, float]],
    distributed_loads: list[dict[str, str | float]],
    applied_moments: list[dict[str, float]],
) -> Beam:
    beam = Beam(
        length=length,
        elasticity=elasticity,
        inertia=inertia,
        support_type=SupportType(support_type),
        name="Custom Beam",
    )
    for load in point_loads:
        beam.add_point_load(
            magnitude=load["magnitude"],
            position=load["position"],
        )
    for load in distributed_loads:
        beam.add_distributed_load(
            expression=str(load["expression"]),
            start=load["start"],
            end=load["end"],
        )
    for applied_moment in applied_moments:
        beam.add_applied_moment(
            magnitude=applied_moment["magnitude"],
            position=applied_moment["position"],
        )
    return beam


def main() -> None:
    st.set_page_config(
        page_title="1D Beam Solver",
        page_icon="B",
        layout="wide",
    )
    _inject_styles()

    st.markdown(
        """
        <section class="hero-shell">
          <p class="hero-kicker">Mechanics of Materials</p>
          <h1>1D Beam Solver Studio</h1>
          <p class="hero-copy">
            Build a custom beam, use signed point loads, define distributed loads as
            <code>w(x)</code> over any span, and inspect the physical model together with
            reactions, internal forces, and deflection.
          </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    beam, samples = _sidebar_configuration()
    if beam is None:
        st.stop()

    try:
        result = solve_beam(beam, samples=samples)
    except ValueError as error:
        st.error(str(error))
        st.stop()

    _render_metrics(result)
    _render_beam_model(result)
    _render_model_panels(result)
    _render_probe(result)
    _render_charts(result)


def _sidebar_configuration() -> tuple[Beam | None, int]:
    with st.sidebar:
        st.markdown("## Beam Setup")
        st.caption(
            "Use negative vertical loads for downward actions. "
            "For distributed loads, enter a signed expression in x such as "
            "`-250 - 20*x` or `-(250 + 20X)`."
        )

        samples = int(
            st.slider(
                "Diagram samples",
                min_value=201,
                max_value=2001,
                value=801,
                step=100,
            )
        )
        support_type = st.selectbox(
            "Support type",
            options=[SupportType.SIMPLY_SUPPORTED.value, SupportType.CANTILEVER.value],
            format_func=lambda value: value.replace("_", " ").title(),
        )
        length = st.number_input("Beam length L (m)", min_value=0.1, value=5.0, step=0.1)
        elasticity = st.number_input(
            "Elastic modulus E (Pa)",
            min_value=1_000.0,
            value=200_000_000_000.0,
            step=10_000_000_000.0,
            format="%.3e",
        )
        inertia = st.number_input(
            "Second moment of area I (m^4)",
            min_value=1e-9,
            value=8e-6,
            step=1e-6,
            format="%.6e",
        )

        point_count = int(st.number_input("Point load count", min_value=0, value=1, step=1))
        point_loads: list[dict[str, float]] = []
        if point_count:
            with st.expander("Point loads", expanded=True):
                for index in range(point_count):
                    point_loads.append(
                        {
                            "magnitude": st.number_input(
                                f"P{index + 1} magnitude (N)",
                                key=f"point_magnitude_{index}",
                                value=-10_000.0 if index == 0 else -5_000.0,
                                step=500.0,
                            ),
                            "position": st.number_input(
                                f"P{index + 1} position (m)",
                                key=f"point_position_{index}",
                                min_value=0.0,
                                max_value=float(length),
                                value=min(float(length), float(length) / 2.0),
                                step=max(float(length) / 100.0, 0.01),
                            ),
                        }
                    )

        udl_count = int(st.number_input("Distributed load count", min_value=0, value=0, step=1))
        distributed_loads: list[dict[str, str | float]] = []
        if udl_count:
            with st.expander("Distributed loads", expanded=True):
                for index in range(udl_count):
                    default_end = min(float(length), max(float(length) * 0.75, 0.2))
                    distributed_loads.append(
                        {
                            "expression": st.text_input(
                                f"w{index + 1}(x) in N/m",
                                key=f"udl_expression_{index}",
                                value="-2500",
                                help="Examples: -2500, -250 - 20*x, -(250 + 20X)",
                            ),
                            "start": st.number_input(
                                f"w{index + 1} start (m)",
                                key=f"udl_start_{index}",
                                min_value=0.0,
                                max_value=float(length),
                                value=0.0,
                                step=max(float(length) / 100.0, 0.01),
                            ),
                            "end": st.number_input(
                                f"w{index + 1} end (m)",
                                key=f"udl_end_{index}",
                                min_value=0.0,
                                max_value=float(length),
                                value=default_end,
                                step=max(float(length) / 100.0, 0.01),
                            ),
                        }
                    )

        moment_count = int(
            st.number_input("Applied moment count", min_value=0, value=0, step=1)
        )
        applied_moments: list[dict[str, float]] = []
        if moment_count:
            with st.expander("Applied moments", expanded=True):
                st.caption("Positive applied moments are drawn clockwise.")
                for index in range(moment_count):
                    applied_moments.append(
                        {
                            "magnitude": st.number_input(
                                f"M{index + 1} magnitude (N*m)",
                                key=f"moment_magnitude_{index}",
                                value=3_000.0,
                                step=250.0,
                            ),
                            "position": st.number_input(
                                f"M{index + 1} position (m)",
                                key=f"moment_position_{index}",
                                min_value=0.0,
                                max_value=float(length),
                                value=min(float(length), float(length) / 2.0),
                                step=max(float(length) / 100.0, 0.01),
                            ),
                        }
                    )

        try:
            beam = build_custom_beam(
                support_type=support_type,
                length=float(length),
                elasticity=float(elasticity),
                inertia=float(inertia),
                point_loads=point_loads,
                distributed_loads=distributed_loads,
                applied_moments=applied_moments,
            )
        except ValueError as error:
            st.error(str(error))
            return None, samples

        return beam, samples


def _render_metrics(result: BeamAnalysisResult) -> None:
    reaction_label = (
        "Right Reaction"
        if result.beam.support_type == SupportType.SIMPLY_SUPPORTED
        else "Fixed-End Moment"
    )
    reaction_value = (
        format_force(result.reactions.right_force)
        if result.beam.support_type == SupportType.SIMPLY_SUPPORTED
        else format_moment(result.reactions.fixed_end_moment)
    )

    columns = st.columns(4)
    columns[0].metric("Left Reaction", format_force(result.reactions.left_force))
    columns[1].metric(reaction_label, reaction_value)
    columns[2].metric("Max |Moment|", format_moment(result.max_abs_moment))
    columns[3].metric("Max |Deflection|", format_deflection(result.max_abs_deflection))


def _render_beam_model(result: BeamAnalysisResult) -> None:
    st.markdown("### Beam Model")
    st.pyplot(
        build_model_figure(result.beam, reactions=result.reactions),
        clear_figure=True,
        use_container_width=True,
    )


def _render_model_panels(result: BeamAnalysisResult) -> None:
    left_column, right_column = st.columns(2)

    with left_column:
        st.markdown("### Model Summary")
        st.markdown(
            f"""
            <div class="panel-card">
              <strong>Beam:</strong> {result.beam.name or "Custom Beam"}<br/>
              <strong>Support:</strong> {result.beam.support_type.value.replace("_", " ").title()}<br/>
              <strong>Length:</strong> {result.beam.length:.3f} m<br/>
              <strong>E:</strong> {result.beam.elasticity:.3e} Pa<br/>
              <strong>I:</strong> {result.beam.inertia:.6e} m^4
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right_column:
        st.markdown("### Load Summary")
        load_rows = _build_load_rows(result.beam)
        if load_rows:
            st.table(load_rows)
        else:
            st.info("No external loads are currently applied to the beam.")


def _render_probe(result: BeamAnalysisResult) -> None:
    st.markdown("### Response Probe")
    probe_position = st.slider(
        "Inspect response at position x (m)",
        min_value=0.0,
        max_value=float(result.beam.length),
        value=float(result.beam.length / 2.0),
        step=max(float(result.beam.length) / 200.0, 0.01),
    )
    response_point = evaluate_response_at(result, probe_position)

    probe_columns = st.columns(4)
    probe_columns[0].metric("Shear at x", format_force(response_point.shear))
    probe_columns[1].metric("Moment at x", format_moment(response_point.moment))
    probe_columns[2].metric("Slope at x", f"{response_point.slope:.6e} rad")
    probe_columns[3].metric(
        "Deflection at x",
        f"{response_point.deflection * 1_000.0:,.3f} mm",
    )


def _render_charts(result: BeamAnalysisResult) -> None:
    st.markdown("### Diagrams")
    figures = build_analysis_figures(result)
    tabs = st.tabs(["Shear", "Moment", "Deflection"])
    for tab, key in zip(tabs, ("shear", "moment", "deflection")):
        with tab:
            st.pyplot(figures[key], clear_figure=True, use_container_width=True)


def _build_load_rows(beam: Beam) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, load in enumerate(beam.point_loads, start=1):
        rows.append(
            {
                "Type": f"Point load {index}",
                "Magnitude": format_force(load.magnitude),
                "Location": f"{load.position:.3f} m",
            }
        )
    for index, load in enumerate(beam.distributed_loads, start=1):
        rows.append(
            {
                "Type": f"Distributed load {index}",
                "Magnitude": f"w(x) = {load.expression} N/m",
                "Location": f"{load.start:.3f} m to {load.end:.3f} m",
            }
        )
    for index, applied_moment in enumerate(beam.applied_moments, start=1):
        rows.append(
            {
                "Type": f"Applied moment {index}",
                "Magnitude": format_moment(applied_moment.magnitude),
                "Location": f"{applied_moment.position:.3f} m",
            }
        )
    return rows


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
          --beam-ink: #17324D;
          --beam-accent: #C75C34;
          --beam-surface: rgba(255, 253, 248, 0.94);
          --beam-border: rgba(23, 50, 77, 0.14);
          --beam-sidebar: rgba(247, 240, 228, 0.98);
          --beam-panel: rgba(255, 250, 242, 0.96);
        }

        .stApp {
          background:
            radial-gradient(circle at top left, rgba(199, 92, 52, 0.12), transparent 30%),
            linear-gradient(180deg, #f7f0e4 0%, #f3efe8 55%, #eef3f1 100%);
          color: var(--beam-ink);
        }

        .block-container {
          max-width: none;
          padding-top: 1.5rem;
          padding-left: 2.4rem;
          padding-right: 2.4rem;
          padding-bottom: 2rem;
        }

        .stMarkdown p,
        .stMarkdown li,
        .stMarkdown span,
        .stMarkdown strong,
        .stCaption,
        label,
        h1, h2, h3, h4, h5, h6 {
          color: var(--beam-ink) !important;
        }

        section[data-testid="stSidebar"] {
          background: var(--beam-sidebar);
          border-right: 1px solid var(--beam-border);
        }

        section[data-testid="stSidebar"] * {
          color: var(--beam-ink) !important;
        }

        .hero-shell {
          background: linear-gradient(135deg, rgba(255,255,255,0.86), rgba(255,247,235,0.94));
          border: 1px solid var(--beam-border);
          border-radius: 24px;
          padding: 1.6rem 1.8rem;
          margin-bottom: 1rem;
          box-shadow: 0 24px 55px rgba(23, 50, 77, 0.08);
        }

        .hero-shell h1 {
          font-family: Georgia, "Palatino Linotype", serif;
          font-size: 2.4rem;
          margin-bottom: 0.35rem;
          color: var(--beam-ink);
        }

        .hero-kicker {
          text-transform: uppercase;
          letter-spacing: 0.14em;
          color: var(--beam-accent);
          font-size: 0.76rem;
          margin-bottom: 0.4rem;
        }

        .hero-copy {
          font-size: 1rem;
          line-height: 1.55;
          max-width: 54rem;
          margin: 0;
        }

        .hero-copy code {
          background: rgba(23, 50, 77, 0.08);
          padding: 0.12rem 0.35rem;
          border-radius: 999px;
          color: var(--beam-ink);
        }

        div[data-testid="metric-container"] {
          background: var(--beam-surface);
          border: 1px solid var(--beam-border);
          border-radius: 18px;
          padding: 0.95rem 1rem;
          box-shadow: 0 10px 30px rgba(23, 50, 77, 0.06);
        }

        div[data-testid="metric-container"] * {
          color: var(--beam-ink) !important;
        }

        .panel-card {
          background: var(--beam-panel);
          border: 1px solid var(--beam-border);
          border-radius: 18px;
          padding: 1rem 1.1rem;
          box-shadow: 0 10px 30px rgba(23, 50, 77, 0.06);
          line-height: 1.65;
        }

        .stTable, .stDataFrame {
          background: var(--beam-panel);
          border-radius: 18px;
        }

        .stNumberInput input,
        .stTextInput input,
        .stTextArea textarea,
        div[data-baseweb="select"] > div,
        div[data-baseweb="base-input"] > div {
          background: rgba(255, 252, 245, 0.98) !important;
          color: var(--beam-ink) !important;
          border-color: rgba(23, 50, 77, 0.18) !important;
        }

        .stSlider [data-baseweb="slider"] *,
        .stRadio *,
        .stCheckbox *,
        .stSelectbox *,
        .stButton * {
          color: var(--beam-ink) !important;
        }

        .stTabs [data-baseweb="tab-list"] {
          gap: 0.55rem;
        }

        .stTabs button[role="tab"] {
          background: rgba(255, 252, 245, 0.96) !important;
          border: 1px solid var(--beam-border) !important;
          border-radius: 999px !important;
          padding-left: 1rem !important;
          padding-right: 1rem !important;
          color: var(--beam-ink) !important;
        }

        .stTabs button[role="tab"] * {
          color: var(--beam-ink) !important;
        }

        .stTabs button[role="tab"][aria-selected="true"] {
          background: #FBE6CC !important;
          border-color: #C75C34 !important;
          box-shadow: inset 0 0 0 1px rgba(199, 92, 52, 0.14);
        }

        .stTabs button[role="tab"][aria-selected="true"] *,
        .stTabs button[role="tab"][aria-selected="true"] p,
        .stTabs button[role="tab"][aria-selected="true"] span,
        .stTabs button[role="tab"][aria-selected="true"] div {
          color: var(--beam-ink) !important;
        }

        table, thead, tbody, tr, th, td {
          color: var(--beam-ink) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
