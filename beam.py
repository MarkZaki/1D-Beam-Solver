from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from utils import ExpressionEvaluator


class SupportType(str, Enum):
    SIMPLY_SUPPORTED = "simply_supported"
    CANTILEVER = "cantilever"


@dataclass(frozen=True)
class PointLoad:
    magnitude: float
    position: float

    def __post_init__(self) -> None:
        if self.position < 0.0:
            raise ValueError("Point load position must be non-negative.")


@dataclass(frozen=True)
class DistributedLoad:
    expression: str
    start: float
    end: float
    _evaluator: ExpressionEvaluator = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.start < 0.0 or self.end < 0.0:
            raise ValueError("Distributed load positions must be non-negative.")
        if self.end <= self.start:
            raise ValueError("Distributed load end must be greater than start.")

        evaluator = ExpressionEvaluator(str(self.expression))
        object.__setattr__(self, "expression", evaluator.expression)
        object.__setattr__(self, "_evaluator", evaluator)

    def intensity_at(self, position: float) -> float:
        return self._evaluator.evaluate(position)


@dataclass(frozen=True)
class AppliedMoment:
    magnitude: float
    position: float

    def __post_init__(self) -> None:
        if self.position < 0.0:
            raise ValueError("Applied moment position must be non-negative.")


@dataclass
class Beam:
    length: float
    elasticity: float
    inertia: float
    support_type: SupportType | str
    point_loads: list[PointLoad] = field(default_factory=list)
    distributed_loads: list[DistributedLoad] = field(default_factory=list)
    applied_moments: list[AppliedMoment] = field(default_factory=list)
    name: str = ""

    def __post_init__(self) -> None:
        self.support_type = SupportType(self.support_type)
        if self.length <= 0.0:
            raise ValueError("Beam length must be greater than zero.")
        if self.elasticity <= 0.0:
            raise ValueError("Elasticity must be greater than zero.")
        if self.inertia <= 0.0:
            raise ValueError("Second moment of area must be greater than zero.")

        for load in self.point_loads:
            self._validate_position(load.position)
        for load in self.distributed_loads:
            self._validate_position(load.start)
            self._validate_position(load.end)
        for applied_moment in self.applied_moments:
            self._validate_position(applied_moment.position)

    def _validate_position(self, position: float) -> None:
        if position < 0.0 or position > self.length:
            raise ValueError(
                f"Load position {position} must lie within the beam length {self.length}."
            )

    def add_point_load(self, magnitude: float, position: float) -> None:
        self._validate_position(position)
        self.point_loads.append(PointLoad(magnitude=magnitude, position=position))

    def add_distributed_load(
        self,
        expression: str | float,
        start: float,
        end: float,
    ) -> None:
        self._validate_position(start)
        self._validate_position(end)
        self.distributed_loads.append(
            DistributedLoad(expression=str(expression), start=start, end=end)
        )

    def add_applied_moment(self, magnitude: float, position: float) -> None:
        self._validate_position(position)
        self.applied_moments.append(
            AppliedMoment(magnitude=magnitude, position=position)
        )
