from __future__ import annotations

from dataclasses import dataclass

from beam import Beam, DistributedLoad, SupportType
from utils import (
    cumulative_trapezoid,
    integrate_function,
    interpolate_linear,
    linspace,
)


@dataclass(frozen=True)
class SupportReactions:
    left_force: float
    right_force: float = 0.0
    fixed_end_moment: float = 0.0


@dataclass(frozen=True)
class BeamAnalysisResult:
    beam: Beam
    reactions: SupportReactions
    x_values: list[float]
    shear_values: list[float]
    moment_values: list[float]
    slope_values: list[float]
    deflection_values: list[float]

    @property
    def max_abs_shear(self) -> float:
        return max(abs(value) for value in self.shear_values)

    @property
    def max_abs_moment(self) -> float:
        return max(abs(value) for value in self.moment_values)

    @property
    def max_abs_deflection(self) -> float:
        return max(abs(value) for value in self.deflection_values)


@dataclass(frozen=True)
class BeamResponsePoint:
    position: float
    shear: float
    moment: float
    slope: float
    deflection: float


def calculate_reactions(beam: Beam) -> SupportReactions:
    total_vertical_load = sum(load.magnitude for load in beam.point_loads)
    total_vertical_load += sum(
        _distributed_resultant(load, load.start, load.end) for load in beam.distributed_loads
    )

    total_moment_about_left = sum(
        load.magnitude * load.position for load in beam.point_loads
    )
    total_moment_about_left += sum(
        _distributed_first_moment_about_left(load, load.start, load.end)
        for load in beam.distributed_loads
    )
    total_moment_about_left -= sum(
        applied_moment.magnitude for applied_moment in beam.applied_moments
    )

    if beam.support_type == SupportType.SIMPLY_SUPPORTED:
        right_reaction = -total_moment_about_left / beam.length
        left_reaction = -total_vertical_load - right_reaction
        return SupportReactions(
            left_force=left_reaction,
            right_force=right_reaction,
        )

    if beam.support_type == SupportType.CANTILEVER:
        return SupportReactions(
            left_force=-total_vertical_load,
            fixed_end_moment=-total_moment_about_left,
        )

    raise ValueError(f"Unsupported support type: {beam.support_type}")


def evaluate_shear(beam: Beam, reactions: SupportReactions, position: float) -> float:
    position = _clamp_position(position, beam.length)
    shear = reactions.left_force

    for load in beam.point_loads:
        if load.position <= position:
            shear += load.magnitude

    for load in beam.distributed_loads:
        shear += _distributed_resultant(load, load.start, min(load.end, position))

    if beam.support_type == SupportType.SIMPLY_SUPPORTED and position >= beam.length:
        shear += reactions.right_force

    return shear


def evaluate_moment(beam: Beam, reactions: SupportReactions, position: float) -> float:
    position = _clamp_position(position, beam.length)
    moment = reactions.left_force * position - reactions.fixed_end_moment

    for load in beam.point_loads:
        if load.position <= position:
            moment += load.magnitude * (position - load.position)

    for load in beam.distributed_loads:
        moment += _distributed_moment_contribution(load, position)

    for applied_moment in beam.applied_moments:
        if applied_moment.position <= position:
            moment += applied_moment.magnitude

    return moment


def solve_beam(beam: Beam, samples: int = 401) -> BeamAnalysisResult:
    if samples < 11:
        raise ValueError("Use at least 11 samples for a stable diagram.")

    reactions = calculate_reactions(beam)
    x_values = _evaluation_positions(beam, samples)
    shear_values = [evaluate_shear(beam, reactions, x) for x in x_values]
    moment_values = [evaluate_moment(beam, reactions, x) for x in x_values]
    slope_values, deflection_values = _calculate_deflection(
        beam=beam,
        x_values=x_values,
        moment_values=moment_values,
    )

    return BeamAnalysisResult(
        beam=beam,
        reactions=reactions,
        x_values=x_values,
        shear_values=shear_values,
        moment_values=moment_values,
        slope_values=slope_values,
        deflection_values=deflection_values,
    )


def evaluate_response_at(
    result: BeamAnalysisResult,
    position: float,
) -> BeamResponsePoint:
    clamped_position = _clamp_position(position, result.beam.length)
    return BeamResponsePoint(
        position=clamped_position,
        shear=evaluate_shear(result.beam, result.reactions, clamped_position),
        moment=evaluate_moment(result.beam, result.reactions, clamped_position),
        slope=interpolate_linear(result.x_values, result.slope_values, clamped_position),
        deflection=interpolate_linear(
            result.x_values,
            result.deflection_values,
            clamped_position,
        ),
    )


def _calculate_deflection(
    beam: Beam,
    x_values: list[float],
    moment_values: list[float],
) -> tuple[list[float], list[float]]:
    flexural_rigidity = beam.elasticity * beam.inertia
    curvature_values = [moment / flexural_rigidity for moment in moment_values]
    curvature_integral = cumulative_trapezoid(x_values, curvature_values)
    double_integral = cumulative_trapezoid(x_values, curvature_integral)

    if beam.support_type == SupportType.SIMPLY_SUPPORTED:
        initial_slope = -double_integral[-1] / beam.length
    else:
        initial_slope = 0.0

    slope_values = [initial_slope + value for value in curvature_integral]
    deflection_values = [
        initial_slope * x + value for x, value in zip(x_values, double_integral)
    ]

    deflection_values[0] = 0.0
    if beam.support_type == SupportType.SIMPLY_SUPPORTED:
        deflection_values[-1] = 0.0

    return slope_values, deflection_values


def _evaluation_positions(beam: Beam, samples: int) -> list[float]:
    positions = linspace(0.0, beam.length, samples)
    positions.extend(load.position for load in beam.point_loads)
    positions.extend(applied_moment.position for applied_moment in beam.applied_moments)
    for load in beam.distributed_loads:
        positions.extend((load.start, load.end))
    return _unique_sorted_positions(positions)


def _unique_sorted_positions(values: list[float], tolerance: float = 1e-9) -> list[float]:
    sorted_values = sorted(values)
    unique_values: list[float] = []
    for value in sorted_values:
        if not unique_values or abs(value - unique_values[-1]) > tolerance:
            unique_values.append(value)
    return unique_values


def _distributed_resultant(load: DistributedLoad, start: float, end: float) -> float:
    return integrate_function(load.intensity_at, start, end)


def _distributed_first_moment_about_left(
    load: DistributedLoad,
    start: float,
    end: float,
) -> float:
    return integrate_function(lambda x_position: load.intensity_at(x_position) * x_position, start, end)


def _distributed_moment_contribution(load: DistributedLoad, position: float) -> float:
    active_end = min(load.end, position)
    if active_end <= load.start:
        return 0.0
    return integrate_function(
        lambda x_position: load.intensity_at(x_position) * (position - x_position),
        load.start,
        active_end,
    )


def _clamp_position(position: float, length: float) -> float:
    if position < 0.0:
        return 0.0
    if position > length:
        return length
    return position
