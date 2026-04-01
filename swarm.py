"""Swarm planning primitives for a bounded generation search."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


INNER_RING = ["Archivist", "Theorist", "Builder", "Judge", "Compressor"]
DEFAULT_OUTER_RING = [
    "paper-led explorer",
    "ablation explorer",
    "architecture explorer",
    "optimizer explorer",
    "simplification explorer",
    "adversarial skeptic",
]


@dataclass
class CandidatePlan:
    candidate_id: str
    owner_role: str
    hypothesis: str
    mutation_scope: str
    eval_plan: str


@dataclass
class GenerationPlan:
    generation: int
    objective: str
    budget_tokens: int
    inner_ring: list[str]
    candidate_plans: list[CandidatePlan]


def build_generation_plan(
    generation: int,
    objective: str,
    hypotheses: Iterable[str],
    budget_tokens: int,
) -> GenerationPlan:
    hypotheses_list = [h.strip() for h in hypotheses if h.strip()]
    if not hypotheses_list:
        raise ValueError("At least one hypothesis is required.")

    candidate_plans: list[CandidatePlan] = []
    for i, hypothesis in enumerate(hypotheses_list):
        role = DEFAULT_OUTER_RING[i % len(DEFAULT_OUTER_RING)]
        candidate_plans.append(
            CandidatePlan(
                candidate_id=f"cand_{i:03d}",
                owner_role=role,
                hypothesis=hypothesis,
                mutation_scope="train.py or harness logic",
                eval_plan="HF Job run + declared metric comparison + rerun for finalists",
            )
        )

    return GenerationPlan(
        generation=generation,
        objective=objective,
        budget_tokens=budget_tokens,
        inner_ring=INNER_RING.copy(),
        candidate_plans=candidate_plans,
    )
