"""CLI for generational autoresearch. Commands: start, ratify, record."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from lineage import (
    GenerationRecord,
    bootstrap_generation,
    generation_dir,
    load_registry,
    next_generation_index,
    record_epic,
)
from ratify import Candidate, ratify_exactly_one
from swarm import build_generation_plan


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ── start ──────────────────────────────────────────────────────────────
    start = subparsers.add_parser("start", help="Bootstrap a new generation and write the candidate plan.")
    start.add_argument("--objective", required=True, help="Generation objective.")
    start.add_argument(
        "--hypothesis",
        action="append",
        dest="hypotheses",
        required=True,
        help="Candidate hypothesis (repeat for multiple).",
    )
    start.add_argument("--budget-tokens", type=int, default=100)
    start.add_argument("--max-candidates", type=int, default=None)
    start.add_argument("--registry-path", default="lineage/registry.json")

    # ── ratify ─────────────────────────────────────────────────────────────
    ratify = subparsers.add_parser("ratify", help="Select exactly one EPIC winner from evaluated candidates.")
    ratify.add_argument(
        "--candidates",
        required=True,
        help="JSON file with a list of evaluated Candidate objects.",
    )
    ratify.add_argument("--registry-path", default="lineage/registry.json")

    # ── record ─────────────────────────────────────────────────────────────
    record = subparsers.add_parser("record", help="Commit the ratified EPIC to the lineage registry.")
    record.add_argument("--claim", required=True, help="One-sentence description of what changed.")
    record.add_argument("--artifact", default="train.py", help="Adopted artifact path.")
    record.add_argument("--winner", default=None, help="Path to winner.json (auto-detected if omitted).")
    record.add_argument("--do-more", action="append", dest="do_more", default=[], metavar="TEXT")
    record.add_argument("--avoid", action="append", dest="avoid", default=[], metavar="TEXT")
    record.add_argument("--open-question", default="", metavar="TEXT")
    record.add_argument("--registry-path", default="lineage/registry.json")

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

    (root / "genesis.md").write_text(
        "\n".join([
            f"# Generation {generation} objective",
            "",
            f"- objective: {args.objective}",
            f"- seed_artifact: {registry.current_seed_artifact}",
            f"- budget_tokens: {args.budget_tokens}",
        ]) + "\n"
    )

    plan_path = root / "candidates" / "plan.json"
    plan_path.write_text(json.dumps(asdict(plan), indent=2) + "\n")

    print(f"generation={generation}")
    print(f"root={root}")
    print(f"plan={plan_path}")
    print(f"candidates={len(plan.candidate_plans)}")
    return 0


def _cmd_ratify(args: argparse.Namespace) -> int:
    registry_path = Path(args.registry_path)
    registry = load_registry(registry_path)
    generation = next_generation_index(registry)

    raw = json.loads(Path(args.candidates).read_text())
    candidates = [Candidate(**c) for c in raw]

    result = ratify_exactly_one(candidates)

    epic_dir = generation_dir(generation) / "epic"
    epic_dir.mkdir(parents=True, exist_ok=True)
    winner_path = epic_dir / "winner.json"
    winner_path.write_text(json.dumps(asdict(result.winner), indent=2) + "\n")

    print(f"winner={result.winner.candidate_id}")
    print(f"epic_type={result.winner.epic_type}")
    print(f"metric={result.winner.metric_value}")
    print(f"written={winner_path}")
    return 0


def _cmd_record(args: argparse.Namespace) -> int:
    registry_path = Path(args.registry_path)
    registry = load_registry(registry_path)
    generation = next_generation_index(registry)

    winner_path = Path(args.winner) if args.winner else generation_dir(generation) / "epic" / "winner.json"
    raw = json.loads(winner_path.read_text())

    rec = GenerationRecord(
        generation=generation,
        epic_type=raw["epic_type"],
        claim=args.claim,
        adopted_artifact=args.artifact,
        baseline_metric=raw["baseline_metric"],
        candidate_metric=raw["metric_value"],
        strict_improvement=raw["metric_value"] < raw["baseline_metric"],
        do_more_of=args.do_more,
        avoid=args.avoid,
        open_question=args.open_question,
    )

    record_epic(rec, registry_path)

    print(f"generation={generation}")
    print(f"epic_type={rec.epic_type}")
    print(f"artifact={rec.adopted_artifact}")
    return 0


def main() -> int:
    args = _parse_args()
    dispatch = {"start": _cmd_start, "ratify": _cmd_ratify, "record": _cmd_record}
    return dispatch[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
