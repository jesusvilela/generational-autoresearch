"""CLI helpers to simplify running one bounded research generation."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from lineage import bootstrap_generation, load_registry, next_generation_index
from swarm import build_generation_plan


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start", help="Bootstrap a new generation and write plan files.")
    start.add_argument("--objective", required=True, help="Generation objective.")
    start.add_argument(
        "--hypothesis",
        action="append",
        dest="hypotheses",
        required=True,
        help="Candidate hypothesis (repeat this flag for multiple hypotheses).",
    )
    start.add_argument("--budget-tokens", type=int, default=100, help="Planning budget.")
    start.add_argument(
        "--max-candidates",
        type=int,
        default=None,
        help="Optional hard cap on number of candidate experiments.",
    )
    start.add_argument(
        "--registry-path",
        default="lineage/registry.json",
        help="Path to lineage registry JSON.",
    )
    return parser.parse_args()


def _cmd_start(args: argparse.Namespace) -> int:
    registry_path = Path(args.registry_path)
    registry = load_registry(registry_path)
    generation = next_generation_index(registry)
    root = bootstrap_generation(generation, registry.current_seed_artifact)

    plan = build_generation_plan(
        generation=generation,
        objective=args.objective,
        hypotheses=args.hypotheses,
        budget_tokens=args.budget_tokens,
        max_candidates=args.max_candidates,
    )

    genesis_md = root / "genesis.md"
    genesis_md.write_text(
        "\n".join(
            [
                f"# Generation {generation} objective",
                "",
                f"- objective: {args.objective}",
                f"- seed_artifact: {registry.current_seed_artifact}",
                f"- budget_tokens: {args.budget_tokens}",
            ]
        )
        + "\n"
    )

    plan_path = root / "candidates" / "plan.json"
    plan_path.write_text(json.dumps(asdict(plan), indent=2) + "\n")

    print(f"generation={generation}")
    print(f"root={root}")
    print(f"plan={plan_path}")
    print(f"candidates={len(plan.candidate_plans)}")
    return 0


def main() -> int:
    args = _parse_args()
    if args.command == "start":
        return _cmd_start(args)
    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
