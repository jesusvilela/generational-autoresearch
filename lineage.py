"""Lineage registry utilities for generational autoresearch.

This module intentionally stays lightweight and dependency-free so it can be
used in both local and HF Jobs environments.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Any


REGISTRY_PATH = Path("lineage/registry.json")


@dataclass
class GenerationRecord:
    generation: int
    epic_type: str
    claim: str
    adopted_artifact: str
    baseline_metric: float
    candidate_metric: float
    strict_improvement: bool
    do_more_of: list[str]
    avoid: list[str]
    open_question: str


@dataclass
class LineageRegistry:
    schema_version: int
    current_generation: int
    current_seed_artifact: str
    generations: list[dict[str, Any]]


DEFAULT_REGISTRY = LineageRegistry(
    schema_version=1,
    current_generation=-1,
    current_seed_artifact="train.py",
    generations=[],
)


def _ensure_registry_path(path: Path = REGISTRY_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_registry(path: Path = REGISTRY_PATH) -> LineageRegistry:
    if not path.exists():
        return DEFAULT_REGISTRY

    payload = json.loads(path.read_text())
    return LineageRegistry(
        schema_version=int(payload.get("schema_version", 1)),
        current_generation=int(payload.get("current_generation", -1)),
        current_seed_artifact=str(payload.get("current_seed_artifact", "train.py")),
        generations=list(payload.get("generations", [])),
    )


def save_registry(registry: LineageRegistry, path: Path = REGISTRY_PATH) -> None:
    _ensure_registry_path(path)
    path.write_text(json.dumps(asdict(registry), indent=2, sort_keys=True) + "\n")


def next_generation_index(registry: LineageRegistry) -> int:
    return registry.current_generation + 1


def record_epic(record: GenerationRecord, path: Path = REGISTRY_PATH) -> LineageRegistry:
    registry = load_registry(path)
    registry.generations.append(asdict(record))
    registry.current_generation = record.generation
    registry.current_seed_artifact = record.adopted_artifact
    save_registry(registry, path)
    return registry


def generation_dir(generation: int) -> Path:
    return Path("lineage") / f"gen_{generation:03d}"


def bootstrap_generation(generation: int, seed_artifact: str) -> Path:
    root = generation_dir(generation)
    for leaf in ("seed", "candidates", "epic", "memory"):
        (root / leaf).mkdir(parents=True, exist_ok=True)

    metadata = {
        "generation": generation,
        "seed_artifact": seed_artifact,
        "objective": "Beat inherited baseline or produce failure EPIC.",
    }
    (root / "genesis.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return root
