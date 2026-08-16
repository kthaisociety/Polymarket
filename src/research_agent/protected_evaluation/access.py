"""Exact permit-to-protected-view binding with denial-before-resolution."""

from __future__ import annotations

from threading import RLock
from typing import TYPE_CHECKING

from research_agent.protected_evaluation._identity import scientific_identity
from research_agent.protected_evaluation.records import (
    AuthorizedProtectedDataView,
    BacktestDenial,
    BacktestPermit,
    BacktestRequest,
    DenialCode,
    ProtectedResourceScope,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from research_agent.protected_evaluation.governance import PermitRegistry

BindingResult = AuthorizedProtectedDataView | BacktestDenial


class ProtectedViewBinder:
    """Consume exact permits idempotently and never broaden their authority."""

    def __init__(
        self,
        *,
        permits: PermitRegistry,
        clock: Callable[[], datetime],
        current_environment_ref: str,
        current_policy_ref: str,
    ) -> None:
        """Initialize a permit-consumption registry."""
        self._clock = clock
        self._permits = permits
        self._environment_ref = current_environment_ref
        self._policy_ref = current_policy_ref
        self._lock = RLock()
        self._views: dict[str, AuthorizedProtectedDataView] = {}

    def authoritative(self, view: AuthorizedProtectedDataView) -> bool:
        """Return whether this exact view was issued by this binder."""
        with self._lock:
            return self._views.get(view.permit_id) == view

    def views(self) -> tuple[AuthorizedProtectedDataView, ...]:
        """Return the immutable issued-view snapshot for audit and retry checks."""
        with self._lock:
            return tuple(self._views.values())

    def bind(
        self,
        *,
        permit: BacktestPermit | BacktestDenial,
        request: BacktestRequest,
        requested_scope: ProtectedResourceScope,
        caller_id: str,
        resolve_exact_resource: Callable[[ProtectedResourceScope], str],
    ) -> BindingResult:
        """Validate all metadata before resolving the protected resource identity."""
        if isinstance(permit, BacktestDenial):
            return permit
        with self._lock:
            mismatch = (
                self._permits.get(permit.permit_id) != permit
                or permit.request_id != request.request_id
                or permit.frozen_system_id != request.frozen_system_id
                or permit.system_id != request.system_id
                or permit.scenario_ref != request.scenario_ref
                or permit.requester_id != caller_id
                or permit.scope != requested_scope
                or request.protected_scope != requested_scope
                or permit.policy_ref != requested_scope.policy_ref
                or requested_scope.environment_ref != self._environment_ref
                or requested_scope.policy_ref != self._policy_ref
                or request.environment_ref != self._environment_ref
            )
            prior = self._views.get(permit.permit_id)
            if prior is not None:
                if not mismatch and prior.caller_id == caller_id and prior.scope == requested_scope:
                    return prior
                return self._deny(
                    request.request_id,
                    permit.authority_id,
                    DenialCode.PERMIT_ALREADY_CONSUMED,
                )
            if mismatch:
                return self._deny(
                    request.request_id, permit.authority_id, DenialCode.PERMIT_MISMATCH
                )
            resource_binding_ref = resolve_exact_resource(requested_scope)
            bound_at = self._clock()
            view = AuthorizedProtectedDataView(
                view_id=scientific_identity(
                    "protected-view",
                    (
                        ("permit_id", permit.permit_id),
                        ("request_id", request.request_id),
                        ("scope_id", requested_scope.scope_id),
                        ("resource_binding_ref", resource_binding_ref),
                        ("caller_id", caller_id),
                    ),
                ),
                permit_id=permit.permit_id,
                request_id=request.request_id,
                frozen_system_id=request.frozen_system_id,
                scenario_ref=request.scenario_ref,
                scope=requested_scope,
                resource_binding_ref=resource_binding_ref,
                caller_id=caller_id,
                bound_at=bound_at,
            )
            self._views[permit.permit_id] = view
            return view

    def _deny(self, request_id: str, authority_id: str, code: DenialCode) -> BacktestDenial:
        denied_at = self._clock()
        return BacktestDenial(
            denial_id=scientific_identity(
                "view-denial",
                (
                    ("request_id", request_id),
                    ("authority_id", authority_id),
                    ("code", code.value),
                ),
            ),
            request_id=request_id,
            code=code,
            message="Protected view binding was denied by exact metadata checks.",
            authority_id=authority_id,
            denied_at=denied_at,
        )


__all__ = ["BindingResult", "ProtectedViewBinder"]
