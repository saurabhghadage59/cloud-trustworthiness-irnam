"""Concession calculations for the IRNAM negotiation phase."""

from __future__ import annotations

from typing import Optional

from negotiation.models import STRATEGY_RHO


def calculate_concession(
    user_value: Optional[float] = None,
    provider_value: Optional[float] = None,
    *,
    negotiation_time: Optional[float] = None,
    degree_of_difference: Optional[float] = None,
    user_aggregate: Optional[float] = None,
    strategy: str = "win_win",
    rho: Optional[float] = None,
) -> float:
    """Compute concession.

    Backward-compatible behavior:
    calculate_concession(user_value, provider_value) returns the midpoint
    used by the original prototype.

    Paper behavior:
    theta = [((t + alpha) / 2) * (1 - Abar_UA(X))] ** rho
    where alpha is the degree of difference and rho is selected by strategy.
    """

    if (
        negotiation_time is None
        and degree_of_difference is None
        and user_aggregate is None
        and user_value is not None
        and provider_value is not None
    ):
        return (float(user_value) + float(provider_value)) / 2

    t = float(negotiation_time if negotiation_time is not None else 0.0)
    alpha = float(degree_of_difference if degree_of_difference is not None else 0.0)
    aggregate = float(user_aggregate if user_aggregate is not None else 0.0)
    effective_rho = float(rho if rho is not None else STRATEGY_RHO.get(strategy, 1.0))
    base = max(0.0, min(1.0, ((t + alpha) / 2) * (1 - aggregate)))
    return base**effective_rho


def concession_to_offer_value(user_value: float, provider_value: float, concession: float) -> float:
    """Move provider offer toward the user request by theta."""

    theta = max(0.0, min(1.0, concession))
    return float(provider_value) + (float(user_value) - float(provider_value)) * theta
