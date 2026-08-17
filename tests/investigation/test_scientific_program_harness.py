"""Adversarial controls around arbitrary authored scientific source."""

# ruff: noqa: D103

from __future__ import annotations

import pytest

from research_agent.investigation import (
    ProgramInvocation,
    ProgramLimits,
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


def test_context_history_is_separate_exact_grant_and_access_record() -> None:
    source = VALID_SOURCE.replace(
        'return {"x": history("x")[-1]["value"]}',
        'return {"x": context_history("x")[-1]["value"]}',
    )
    harness = ScientificProgramHarness()

    result = harness.invoke(
        source,
        ProgramInvocation(
            "make_features",
            histories={"x": [{"value": 1.0}]},
            context_histories={"x": [{"value": 4.0}]},
        ),
    )

    assert result.value == {"x": 4.0}
    assert tuple((item.interface, item.field_id) for item in result.accesses) == (
        ("context_history", "x"),
    )


def test_undeclared_context_history_is_denied() -> None:
    source = VALID_SOURCE.replace(
        'return {"x": history("x")[-1]["value"]}',
        'return {"x": context_history("x")[-1]["value"]}',
    )

    with pytest.raises(ScientificProgramError, match="outside the exact invocation grant"):
        ScientificProgramHarness().invoke(
            source,
            ProgramInvocation("make_features", histories={"x": [{"value": 1.0}]}),
        )


def test_persistent_session_matches_one_shot_values_and_accesses_for_every_phase() -> None:
    harness = ScientificProgramHarness()
    invocations = (
        ProgramInvocation("make_features", histories={"x": [{"value": 4.0}]}),
        ProgramInvocation(
            "make_label",
            outcome=[{"value": 7.0}],
        ),
        ProgramInvocation(
            "fit",
            training=[{"label": 2.0}, {"label": 4.0}],
        ),
        ProgramInvocation(
            "predict",
            state={"mean": 3.0},
            features={"x": 11.0},
        ),
    )
    expected = tuple(harness.invoke(VALID_SOURCE, invocation) for invocation in invocations)

    with harness.session(VALID_SOURCE) as session:
        actual = tuple(session.invoke(invocation) for invocation in invocations)

    assert actual == expected


def test_persistent_session_reexecutes_source_in_a_fresh_namespace_for_every_call() -> None:
    source = """
STATE = {"calls": 0}

def make_features():
    STATE["calls"] = STATE["calls"] + 1
    return {"x": STATE["calls"] + 0.0 * history("x")[-1]["value"]}

def make_label():
    return outcome_path()[-1]["value"]

def fit():
    return {"mean": 0.0 * len(training_rows())}

def predict():
    return model_state()["mean"] + 0.0 * feature_values()["x"]
"""
    invocation = ProgramInvocation("make_features", histories={"x": [{"value": 9.0}]})

    with ScientificProgramHarness().session(source) as session:
        first = session.invoke(invocation)
        second = session.invoke(invocation)

    assert first.value == {"x": 1.0}
    assert second == first


def test_persistent_session_preserves_phase_denial_and_closes_after_timeout() -> None:
    outcome_seeking = VALID_SOURCE.replace(
        'return model_state()["mean"] + 0.0 * feature_values()["x"]',
        'return outcome_path()[-1]["value"]',
    )
    with (
        ScientificProgramHarness().session(outcome_seeking) as session,
        pytest.raises(ScientificProgramError, match="unavailable in predict"),
    ):
        session.invoke(ProgramInvocation("predict", state={"mean": 1.0}, features={"x": 2.0}))

    hanging = VALID_SOURCE.replace(
        'return {"mean": sum(row["label"] for row in training_rows()) / len(training_rows())}',
        "while True:\n        pass",
    )
    harness = ScientificProgramHarness(ProgramLimits(wall_time_seconds=0.05))
    session = harness.session(hanging)
    with pytest.raises(ScientificProgramError, match="wall-clock limit"):
        session.invoke(ProgramInvocation("fit", training=[{"label": 1.0}]))
    with pytest.raises(ScientificProgramError, match="session is closed"):
        session.invoke(ProgramInvocation("make_label", outcome=[{"value": 1.0}]))


def test_persistent_session_has_an_explicit_invocation_bound() -> None:
    harness = ScientificProgramHarness(ProgramLimits(max_session_invocations=2))
    invocation = ProgramInvocation("make_features", histories={"x": [{"value": 1.0}]})
    session = harness.session(VALID_SOURCE)

    assert session.invoke(invocation).value == {"x": 1.0}
    assert session.invoke(invocation).value == {"x": 1.0}
    with pytest.raises(ScientificProgramError, match="invocation limit"):
        session.invoke(invocation)
    with pytest.raises(ScientificProgramError, match="session is closed"):
        session.invoke(invocation)


def test_persistent_session_preserves_per_call_result_limit() -> None:
    source = VALID_SOURCE.replace(
        'return {"x": history("x")[-1]["value"]}',
        'return {"x": [history("x")[-1]["value"] for _ in range(100)]}',
    )
    harness = ScientificProgramHarness(ProgramLimits(max_result_bytes=32))

    with (
        harness.session(source) as session,
        pytest.raises(ScientificProgramError, match="result exceeds"),
    ):
        session.invoke(ProgramInvocation("make_features", histories={"x": [{"value": 1.0}]}))
