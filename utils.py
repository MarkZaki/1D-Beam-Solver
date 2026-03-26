from __future__ import annotations

import ast
import math
import re


_ALLOWED_BINARY_OPERATORS = {
    ast.Add: lambda left, right: left + right,
    ast.Sub: lambda left, right: left - right,
    ast.Mult: lambda left, right: left * right,
    ast.Div: lambda left, right: left / right,
    ast.Pow: lambda left, right: left**right,
}

_ALLOWED_UNARY_OPERATORS = {
    ast.UAdd: lambda value: value,
    ast.USub: lambda value: -value,
}

_ALLOWED_FUNCTIONS = {
    "abs": abs,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "exp": math.exp,
    "log": math.log,
}

_ALLOWED_CONSTANTS = {
    "e": math.e,
    "pi": math.pi,
}

_GAUSS_LEGENDRE_NODES = (
    -0.906179845938664,
    -0.5384693101056831,
    0.0,
    0.5384693101056831,
    0.906179845938664,
)

_GAUSS_LEGENDRE_WEIGHTS = (
    0.23692688505618908,
    0.47862867049936647,
    0.5688888888888889,
    0.47862867049936647,
    0.23692688505618908,
)


class ExpressionEvaluator:
    def __init__(self, expression: str) -> None:
        self.expression = normalize_expression(expression)
        try:
            parsed_expression = ast.parse(self.expression, mode="eval")
        except SyntaxError as error:
            raise ValueError(f"Invalid load expression '{expression}'.") from error

        _validate_expression_node(parsed_expression.body)
        self._expression_tree = parsed_expression.body

    def evaluate(self, x_value: float) -> float:
        return float(_evaluate_expression_node(self._expression_tree, x_value))


def normalize_expression(expression: str) -> str:
    normalized = expression.strip()
    if not normalized:
        raise ValueError("Load expression cannot be empty.")

    normalized = normalized.replace("^", "**")
    normalized = re.sub(r"(?<=\d)\s*(?=[xX(])", "*", normalized)
    normalized = re.sub(r"(?<=\))\s*(?=[xX\d(])", "*", normalized)
    normalized = re.sub(r"(?<=[xX])\s*(?=\()", "*", normalized)
    normalized = re.sub(r"(?<![A-Za-z0-9_])X(?![A-Za-z0-9_])", "x", normalized)
    return normalized


def linspace(start: float, stop: float, count: int) -> list[float]:
    if count < 2:
        raise ValueError("At least two sample points are required.")
    step = (stop - start) / (count - 1)
    return [start + index * step for index in range(count)]


def cumulative_trapezoid(x_values: list[float], y_values: list[float]) -> list[float]:
    if len(x_values) != len(y_values):
        raise ValueError("x and y arrays must have the same length.")
    if not x_values:
        return []

    cumulative = [0.0]
    for index in range(1, len(x_values)):
        delta_x = x_values[index] - x_values[index - 1]
        area = 0.5 * delta_x * (y_values[index] + y_values[index - 1])
        cumulative.append(cumulative[-1] + area)
    return cumulative


def interpolate_linear(x_values: list[float], y_values: list[float], target: float) -> float:
    if len(x_values) != len(y_values):
        raise ValueError("x and y arrays must have the same length.")
    if not x_values:
        raise ValueError("Interpolation requires at least one point.")
    if target <= x_values[0]:
        return y_values[0]
    if target >= x_values[-1]:
        return y_values[-1]

    for index in range(1, len(x_values)):
        left_x = x_values[index - 1]
        right_x = x_values[index]
        if target <= right_x:
            left_y = y_values[index - 1]
            right_y = y_values[index]
            span = right_x - left_x
            if span == 0.0:
                return right_y
            ratio = (target - left_x) / span
            return left_y + ratio * (right_y - left_y)

    return y_values[-1]


def integrate_function(
    function,
    start: float,
    end: float,
    subintervals: int = 8,
) -> float:
    if end <= start:
        return 0.0

    interval_width = (end - start) / subintervals
    integral = 0.0
    for interval_index in range(subintervals):
        left = start + interval_index * interval_width
        right = end if interval_index == subintervals - 1 else left + interval_width
        midpoint = 0.5 * (left + right)
        half_span = 0.5 * (right - left)

        for node, weight in zip(_GAUSS_LEGENDRE_NODES, _GAUSS_LEGENDRE_WEIGHTS):
            integral += weight * function(midpoint + half_span * node) * half_span

    return integral


def slugify(text: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
    return normalized or "beam_case"


def format_force(value: float) -> str:
    return f"{value:,.3f} N"


def format_moment(value: float) -> str:
    return f"{value:,.3f} N*m"


def format_deflection(value: float) -> str:
    return f"{value * 1_000.0:,.3f} mm"


def _validate_expression_node(node) -> None:
    if isinstance(node, ast.BinOp):
        if type(node.op) not in _ALLOWED_BINARY_OPERATORS:
            raise ValueError("Unsupported operator in load expression.")
        _validate_expression_node(node.left)
        _validate_expression_node(node.right)
        return

    if isinstance(node, ast.UnaryOp):
        if type(node.op) not in _ALLOWED_UNARY_OPERATORS:
            raise ValueError("Unsupported unary operator in load expression.")
        _validate_expression_node(node.operand)
        return

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_FUNCTIONS:
            raise ValueError("Unsupported function in load expression.")
        for argument in node.args:
            _validate_expression_node(argument)
        if node.keywords:
            raise ValueError("Keyword arguments are not supported in load expressions.")
        return

    if isinstance(node, ast.Name):
        if node.id not in {"x", *tuple(_ALLOWED_CONSTANTS)}:
            raise ValueError(f"Unknown symbol '{node.id}' in load expression.")
        return

    if isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float)):
            raise ValueError("Only numeric constants are allowed in load expressions.")
        return

    raise ValueError("Unsupported syntax in load expression.")


def _evaluate_expression_node(node, x_value: float) -> float:
    if isinstance(node, ast.BinOp):
        return _ALLOWED_BINARY_OPERATORS[type(node.op)](
            _evaluate_expression_node(node.left, x_value),
            _evaluate_expression_node(node.right, x_value),
        )

    if isinstance(node, ast.UnaryOp):
        return _ALLOWED_UNARY_OPERATORS[type(node.op)](
            _evaluate_expression_node(node.operand, x_value)
        )

    if isinstance(node, ast.Call):
        function = _ALLOWED_FUNCTIONS[node.func.id]
        arguments = [_evaluate_expression_node(argument, x_value) for argument in node.args]
        return function(*arguments)

    if isinstance(node, ast.Name):
        if node.id == "x":
            return x_value
        return _ALLOWED_CONSTANTS[node.id]

    return float(node.value)
