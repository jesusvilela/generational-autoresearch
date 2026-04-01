"""Ratification gate for exactly-one-EPIC adoption."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass
class Candidate:
    candidate_id: str
    epic_type: str
    metric_value: float
    baseline_metric: float
    executable: bool
    validated: bool
    simplicity_score: float
    leverage_score: float
    robustness_score: float
    important_axis_win: bool = False
    note: str = ""


@dataclass
class RatificationResult:
    winner: Candidate
    rationale: str


class RatificationError(ValueError):
    """Raised when generation cannot ratify one valid EPIC."""


def _utility(candidate: Candidate) -> tuple[float, float, float, float]:
    # Lower metric_value is better (val_bpb).
    improvement = candidate.baseline_metric - candidate.metric_value
    return (
        improvement,
        candidate.robustness_score,
        candidate.simplicity_score,
        candidate.leverage_score,
    )


def ratify_exactly_one(candidates: Sequence[Candidate]) -> RatificationResult:
    def _is_eligible(candidate: Candidate) -> bool:
        metric_win = candidate.metric_value < candidate.baseline_metric
        return candidate.executable and candidate.validated and (
            metric_win or candidate.important_axis_win
        )

    eligible = [
        c
        for c in candidates
        if _is_eligible(c)
    ]

    if not eligible:
        raise RatificationError(
            "No ratifiable winner found. Emit a single failure EPIC that prunes search space."
        )

    ranked = sorted(eligible, key=_utility, reverse=True)
    winner = ranked[0]

    if len(ranked) > 1 and _utility(ranked[1]) == _utility(winner):
        raise RatificationError(
            "Top candidates are tied under utility ordering; run tie-break eval before ratification."
        )

    rationale = (
        "Winner selected by utility order: improvement, robustness, simplicity, leverage. "
        "Eligibility requires executable + validated + (metric improvement OR important-axis win). "
        f"Picked {winner.candidate_id} ({winner.epic_type})."
    )
    return RatificationResult(winner=winner, rationale=rationale)
