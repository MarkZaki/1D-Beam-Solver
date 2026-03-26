from __future__ import annotations

import argparse

from beam import Beam, SupportType
from plots import save_analysis_plots
from solver import solve_beam
from utils import format_deflection, format_force, format_moment


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze a custom 1D beam definition.")
    parser.add_argument(
        "--support-type",
        default=SupportType.SIMPLY_SUPPORTED.value,
        choices=[SupportType.SIMPLY_SUPPORTED.value, SupportType.CANTILEVER.value],
        help="Beam support type.",
    )
    parser.add_argument("--length", type=float, default=5.0, help="Beam length in meters.")
    parser.add_argument(
        "--elasticity",
        type=float,
        default=200e9,
        help="Elastic modulus E in Pa.",
    )
    parser.add_argument(
        "--inertia",
        type=float,
        default=8e-6,
        help="Second moment of area I in m^4.",
    )
    parser.add_argument(
        "--point-load",
        action="append",
        default=[],
        metavar="MAGNITUDE:POSITION",
        help="Signed point load as magnitude:position. Use negative values for downward loads.",
    )
    parser.add_argument(
        "--udl",
        action="append",
        default=[],
        metavar="EXPRESSION:START:END",
        help=(
            "Distributed load as expression:start:end, where expression is w(x) in N/m. "
            "Example: \"-250 - 20*x:1:3\""
        ),
    )
    parser.add_argument(
        "--moment",
        action="append",
        default=[],
        metavar="MAGNITUDE:POSITION",
        help="Applied moment as magnitude:position with positive magnitude clockwise.",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=801,
        help="Number of x locations used to sample the beam response.",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Save shear, moment, and deflection plots to disk.",
    )
    parser.add_argument(
        "--output-dir",
        default="generated_plots",
        help="Directory for generated plots when --plot is used.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        beam = Beam(
            length=args.length,
            elasticity=args.elasticity,
            inertia=args.inertia,
            support_type=args.support_type,
            name="CLI Beam",
        )
        for point_load in args.point_load:
            magnitude, position = _parse_pair(point_load, "--point-load")
            beam.add_point_load(magnitude=magnitude, position=position)
        for udl in args.udl:
            expression, start, end = _parse_udl(udl)
            beam.add_distributed_load(expression=expression, start=start, end=end)
        for applied_moment in args.moment:
            magnitude, position = _parse_pair(applied_moment, "--moment")
            beam.add_applied_moment(magnitude=magnitude, position=position)
    except ValueError as error:
        parser.error(str(error))

    result = solve_beam(beam, samples=args.samples)

    print("Custom Beam Analysis")
    print(f"Support type: {beam.support_type.value}")
    print(f"Length: {beam.length:.3f} m")
    print()
    print("Reactions")
    print(f"  Left vertical reaction: {format_force(result.reactions.left_force)}")
    if beam.support_type.value == SupportType.SIMPLY_SUPPORTED.value:
        print(f"  Right vertical reaction: {format_force(result.reactions.right_force)}")
    else:
        print(f"  Fixed-end moment: {format_moment(result.reactions.fixed_end_moment)}")
    print()
    print("Peak response")
    print(f"  Max |shear|: {format_force(result.max_abs_shear)}")
    print(f"  Max |moment|: {format_moment(result.max_abs_moment)}")
    print(f"  Max |deflection|: {format_deflection(result.max_abs_deflection)}")

    if args.plot:
        saved_paths = save_analysis_plots(result, output_dir=args.output_dir, stem="cli_beam")
        print()
        print("Saved plots")
        for path in saved_paths:
            print(f"  {path}")

    return 0


def _parse_pair(value: str, option_name: str) -> tuple[float, float]:
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError(f"{option_name} expects MAGNITUDE:POSITION.")
    return float(parts[0]), float(parts[1])


def _parse_udl(value: str) -> tuple[str, float, float]:
    parts = value.rsplit(":", 2)
    if len(parts) != 3:
        raise ValueError("--udl expects EXPRESSION:START:END.")
    return parts[0], float(parts[1]), float(parts[2])


if __name__ == "__main__":
    raise SystemExit(main())
