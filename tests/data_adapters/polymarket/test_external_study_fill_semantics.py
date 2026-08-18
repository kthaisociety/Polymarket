"""Regression tests for canonical fill semantics in executable external studies."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

_STUDY = Path(__file__).parents[3] / "studies" / "polymarket-active-external-data-2026-08-18"
_ACQUISITIONS = ("acquire_brazil_fills.py", "acquire_hormuz_fills.py")
_ANALYSES = ("brazil_poll_analysis.py", "hormuz_weekly_analysis.py")
_SHARES = 100.0


def _assignment(path: Path, name: str) -> str:
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            value_node = node.value
            if (
                isinstance(value_node, ast.Call)
                and isinstance(value_node.func, ast.Attribute)
                and value_node.func.attr == "strip"
            ):
                value_node = value_node.func.value
            value = ast.literal_eval(value_node)
            assert isinstance(value, str)
            return value
    message = f"{name} was not found in {path}"
    raise AssertionError(message)


def _execute_function(
    path: Path,
) -> tuple[
    Callable[[str, str, str, int, int, float], tuple[float, float, float]],
    dict[str, object],
]:
    tree = ast.parse(path.read_text(), filename=str(path))
    function = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "execute"
    )
    namespace: dict[str, object] = {}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), "exec"), namespace)  # noqa: S102
    execute = cast(
        "Callable[[str, str, str, int, int, float], tuple[float, float, float]]",
        namespace["execute"],
    )
    return execute, namespace


@pytest.mark.parametrize("filename", _ACQUISITIONS)
def test_external_fill_acquisition_keeps_one_canonical_taker_row(filename: str) -> None:
    """Every retained fill corpus must contain one taker row per match."""
    query = _assignment(_STUDY / filename, "_QUERY")

    assert "raw->'topics' IS NULL" in query
    assert "right(raw->'topics'->>3, 40)" in query
    assert "lower(raw->>'address')" in query


@pytest.mark.parametrize("filename", _ANALYSES)
@pytest.mark.parametrize(
    ("fill_side", "direction", "action", "expected_price"),
    [
        ("BUY", "YES", "BUY", 0.6),
        ("SELL", "YES", "SELL", 0.6),
        ("SELL", "NO", "BUY", 0.4),
        ("BUY", "NO", "SELL", 0.4),
    ],
)
def test_external_analysis_interprets_taker_side_as_aggressor_side(
    filename: str,
    fill_side: str,
    direction: str,
    action: str,
    expected_price: float,
) -> None:
    """Aggressor side must map consistently to YES and complementary NO actions."""
    execute, namespace = _execute_function(_STUDY / filename)
    namespace.update(
        {
            "fill_time": [10],
            "fill_market": ["market"],
            "fill_side": [fill_side],
            "fill_price": [0.6],
            "fill_size": [_SHARES],
        }
    )

    notional, fees, filled = execute("market", direction, action, 0, 20, _SHARES)

    assert filled == _SHARES
    assert notional == pytest.approx(_SHARES * expected_price)
    assert fees == pytest.approx(_SHARES * 0.05 * expected_price * (1.0 - expected_price))
