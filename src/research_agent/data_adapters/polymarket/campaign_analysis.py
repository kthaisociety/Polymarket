"""Bind exact Polymarket corpus sources to the enforced campaign authority."""

# ruff: noqa: EM101, TRY003

from __future__ import annotations

import ast
from collections import OrderedDict
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from research_agent.exploration import CampaignAnalysis, DataAccessRequest, EvidenceTier

if TYPE_CHECKING:
    from research_agent.data_adapters.polymarket.corpus_analysis import (
        PolymarketDevelopmentAnalysis,
    )
    from research_agent.exploration import AuthorizedDataView

_READ_ARG_COUNT = 2


@dataclass(frozen=True, slots=True)
class CampaignInputView:
    """Value-free identity and schema of one registered campaign input view."""

    view_id: str
    dataset_ref: str
    environment_ref: str
    field_ids: frozenset[str]


def build_polymarket_campaign_analysis(  # noqa: PLR0913
    *,
    analysis_id: str,
    family: str,
    source: str,
    development_analysis: PolymarketDevelopmentAnalysis,
    evidence_tier: EvidenceTier,
    required_accesses: tuple[tuple[str, str], ...] | None = None,
) -> CampaignAnalysis:
    """Freeze authored bytes and their least-authority corpus capabilities."""
    return build_polymarket_campaign_analysis_for_views(
        analysis_id=analysis_id,
        family=family,
        source=source,
        views=tuple(
            CampaignInputView(
                view_id=view.view_id,
                dataset_ref=view.dataset_ref,
                environment_ref=view.environment_ref,
                field_ids=frozenset(view.fields),
            )
            for view in _views_by_id(development_analysis).values()
        ),
        expected_harness_binding_identity=development_analysis.harness.binding_identity,
        evidence_tier=evidence_tier,
        required_accesses=required_accesses,
    )


def build_polymarket_campaign_analysis_for_views(  # noqa: PLR0913
    *,
    analysis_id: str,
    family: str,
    source: str,
    views: tuple[CampaignInputView, ...],
    expected_harness_binding_identity: str,
    evidence_tier: EvidenceTier,
    required_accesses: tuple[tuple[str, str], ...] | None = None,
) -> CampaignAnalysis:
    """Freeze a source from registered value-free view identities before data loading."""
    accesses = required_accesses or literal_read_accesses(source)
    if not accesses:
        raise ValueError("Polymarket campaign source must consume a registered corpus field")
    views_by_id = {view.view_id: view for view in views}
    if len(views_by_id) != len(views):
        raise ValueError("campaign input view identities must be unique")
    fields_by_view: OrderedDict[str, list[str]] = OrderedDict()
    for view_id, field_id in accesses:
        view = views_by_id.get(view_id)
        if view is None or field_id not in view.field_ids:
            raise ValueError("campaign source requests a field absent from its registered views")
        fields = fields_by_view.setdefault(view_id, [])
        if field_id not in fields:
            fields.append(field_id)
    required_unique = tuple(dict.fromkeys(accesses))
    dataset_refs = tuple(dict.fromkeys(views_by_id[view].dataset_ref for view, _ in accesses))
    environment_refs = tuple(
        dict.fromkeys(views_by_id[view].environment_ref for view, _ in accesses)
    )
    return CampaignAnalysis(
        analysis_id=analysis_id,
        family=family,
        source=source,
        data_access=tuple(
            DataAccessRequest(view_id, tuple(field_ids))
            for view_id, field_ids in fields_by_view.items()
        ),
        required_actual_accesses=required_unique,
        expected_dataset_refs=dataset_refs,
        expected_environment_refs=environment_refs,
        expected_harness_binding_identity=expected_harness_binding_identity,
        evidence_tier=evidence_tier,
    )


def literal_read_accesses(source: str) -> tuple[tuple[str, str], ...]:
    """Extract exact literal ``read(view, field)`` calls in authored source order."""
    tree = ast.parse(source)
    calls = sorted(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "read"
        ),
        key=lambda node: (node.lineno, node.col_offset),
    )
    accesses: list[tuple[str, str]] = []
    for call in calls:
        if (
            len(call.args) != _READ_ARG_COUNT
            or call.keywords
            or not all(
                isinstance(argument, ast.Constant) and isinstance(argument.value, str)
                for argument in call.args
            )
        ):
            raise ValueError("dynamic read calls require explicit campaign access declarations")
        view_argument, field_argument = call.args
        view_value = cast("str", cast("ast.Constant", view_argument).value)
        field_value = cast("str", cast("ast.Constant", field_argument).value)
        accesses.append((view_value, field_value))
    return tuple(accesses)


def standard_polymarket_campaign_views(partition_id: str) -> tuple[CampaignInputView, ...]:
    """Describe standard corpus views without loading their potentially large values."""
    from research_agent.data_adapters.polymarket.corpus_analysis import (  # noqa: PLC0415
        polymarket_development_view_specs,
    )

    return tuple(
        CampaignInputView(view_id, dataset_ref, environment_ref, frozenset(field_ids))
        for view_id, dataset_ref, environment_ref, field_ids in polymarket_development_view_specs(
            partition_id
        )
    )


def _views_by_id(
    analysis: PolymarketDevelopmentAnalysis,
) -> dict[str, AuthorizedDataView]:
    return {
        view.view_id: view
        for view in (
            analysis.price_view,
            analysis.outcome_view,
            *analysis.registered_event_views,
        )
    }


__all__ = [
    "CampaignInputView",
    "build_polymarket_campaign_analysis",
    "build_polymarket_campaign_analysis_for_views",
    "literal_read_accesses",
    "standard_polymarket_campaign_views",
]
