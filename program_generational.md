# generational autoresearch

This document extends `program.md` from a single endless hill-climber into a bounded, lineage-based research harness.

## Core idea

Each generation must output **exactly one EPIC** outcome, then hand that forward.

- **Executable**: runnable artifact or operationally usable process
- **Proven**: validated on declared eval (`val_bpb` by default)
- **Irreversible**: adopted into lineage state
- **Compounding**: increases future search/build/verification capability

## Generation recursion

Let `S_g` be adopted system state at generation `g`, `K_g` be lineage memory, and `EPIC_g` be the ratified outcome.

- `G_1 = H(S_0, K_0)`
- `G_{g+1} = H(S_g, K_g)`
- `S_g = adopt(EPIC_g)`

`H` is the base hf-autoresearch harness (research, modify, run HF job, evaluate), now wrapped by generation state + swarm + ratification.

## Inputs per generation

Each generation receives:

1. inherited best executable artifact (typically `train.py`)
2. lineage registry and prior deltas
3. fixed compute budget
4. fixed trial cap or deadline
5. one declared target metric and baseline

## Output contract (hard)

A generation is complete **iff** it produces exactly one adopted artifact from one of:

1. merged code change
2. merged harness/orchestration change
3. canonicalized principle/taxonomy
4. canonicalized evaluation/failure framework

Forbidden terminal outputs:

- several promising directions
- top-k ideas
- dashboard only
- unratified pile of experiments

## Topology

- **Inner ring** (high-trust): Archivist, Theorist, Builder, Judge, Compressor
- **Outer ring** (disposable explorers): paper-led, ablation, architecture, optimizer, simplification, skeptic

Outer ring proposes candidates; inner ring selects one EPIC.

## Budgeting default

- 10% inheritance + memory load
- 20% hypothesis generation
- 50% execution/evaluation
- 10% replication on finalists
- 10% compression + ratification

## Adoption rule

A candidate is ratifiable when all conditions hold:

1. executable or operationally usable
2. validated on declared eval
3. strict domination on >=1 important axis vs inherited state
4. simple enough to preserve
5. compressible into reusable lineage memory

Tie-break order:

1. correctness
2. improvement magnitude
3. robustness across reruns
4. simplicity
5. future leverage

## Files added by this harness extension

- `lineage.py`: registry + generation state IO helpers
- `swarm.py`: role assignment and bounded candidate planning
- `ratify.py`: hard gate for exactly-one-EPIC selection
- `templates/epic.md.j2`: canonical EPIC record template
- `templates/generation_report.md.j2`: generation summary template
- `lineage/registry.json`: append-only lineage index

## Suggested runbook for generation g

1. materialize generation workspace from inherited seed
2. define objective (`genesis.md`) with explicit baseline and success threshold
3. spawn swarm role contexts and candidate plan
4. execute bounded experiments on HF Jobs
5. compare finalists with replication budget
6. ratify exactly one EPIC (or one failure EPIC)
7. adopt EPIC into lineage state
8. write `epic.md`, `lineage_delta.json`, `generation_report.md`
9. spawn generation `g+1` from adopted state + compressed memory

## Failure semantics

Generation failure still requires one EPIC when possible:

- negative-result codex
- pruning rule for future search
- bug/failure taxonomy
- evaluator improvement that prevents repeated waste

Failure EPICs are first-class lineage assets.
