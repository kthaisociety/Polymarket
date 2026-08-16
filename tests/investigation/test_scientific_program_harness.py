"""Adversarial controls around arbitrary authored scientific source."""

# ruff: noqa: D103

from __future__ import annotations

import pytest

from research_agent.investigation import (
    ProgramInvocation,
    ScientificProgramError,
    ScientificProgramHarness,
)

VALID_SOURCE = """
def make_features():
    return {"x": history("x")[-1]["value"]}

def make_label():
    return outcome_path()[-1]["value"]

def fit():
    return {"mean": sum(row["label"] for row in training_rows()) / len(training_rows())}

def predict():
    return model_state()["mean"] + 0.0 * feature_values()["x"]
"""


def test_host_and_introspection_interfaces_are_denied_before_execution() -> None:
    harness = ScientificProgramHarness()
    forbidden = VALID_SOURCE.replace(
        'return {"x": history("x")[-1]["value"]}',
        'return {"x": open("/etc/passwd").read()}',
    )

    with pytest.raises(ScientificProgramError, match="unavailable"):
        harness.invoke(
            forbidden,
            ProgramInvocation("make_features", histories={"x": []}),
        )


def test_fit_and_prediction_cannot_read_outcomes_or_other_phase_channels() -> None:
    harness = ScientificProgramHarness()
    outcome_seeking = VALID_SOURCE.replace(
        'return model_state()["mean"] + 0.0 * feature_values()["x"]',
        'return outcome_path()[-1]["value"]',
    )

    with pytest.raises(ScientificProgramError, match="unavailable in predict"):
        harness.invoke(
            outcome_seeking,
            ProgramInvocation("predict", state={"mean": 1.0}, features={"x": 2.0}),
        )


def test_actual_capability_accesses_come_from_harness_not_authored_claims() -> None:
    result = ScientificProgramHarness().invoke(
        VALID_SOURCE,
        ProgramInvocation(
            "make_features",
            histories={"x": [{"value": 4.0}]},
        ),
    )

    assert result.value == {"x": 4.0}
    assert tuple((item.interface, item.field_id) for item in result.accesses) == (("history", "x"),)
