# autoresearch on Hugging Face

Autonomous LLM pretraining research running entirely on [Hugging Face infrastructure](https://huggingface.co/docs/hub/jobs). An AI agent iterates on a training script — modifying architecture, optimizer, hyperparameters — while reading recent papers via [`hf papers`](https://huggingface.co/docs/huggingface_hub/main/en/guides/cli#search-papers) for ideas. No local GPU needed. You only need a Hugging Face account.

Fork of [karpathy/autoresearch](https://github.com/karpathy/autoresearch), adapted to run on HF Jobs with mounted datasets and storage buckets.

*See an [example 24-hour run on A100](https://huggingface.co/buckets/mishig/autoresearch-results) — experiment artifacts including results, best models, and the full agent chat transcript are all saved to the bucket.*

![Example val_bpb progress over time](https://huggingface.co/buckets/mishig/autoresearch-results/resolve/progress.png)

## Modes

This repo supports two modes:

1. **Single-agent autoresearch (`program.md`)**
   - Minimal baseline loop: research → edit `train.py` → run HF Job → score → keep/discard.
2. **Generational autoresearch (`program_generational.md`)**
   - Lineage loop: inherit → swarm exploration → ratify exactly one EPIC → compress memory → spawn next generation.

The original atomic unit stays unchanged: `train.py` + HF Jobs + `val_bpb`.

## Core files

- **`train.py`** — self-contained training script (model, optimizer, dataloader, evaluation).
- **`program.md`** — single-agent operating constitution.
- **`program_generational.md`** — generation contract + EPIC adoption rules.
- **`lineage.py`** — lineage registry/state helpers.
- **`swarm.py`** — role-based candidate planning for bounded generation search.
- **`ratify.py`** — exactly-one-EPIC ratification gate.
- **`lineage/registry.json`** — lineage index seed.

## Quick start

```bash
# 1) Install the HF CLI
curl -LsSf https://hf.co/cli/install.sh | bash

# 2) Login
hf auth login

# 3) Sanity check
author=$(hf auth whoami | head -n1)
echo "Running as: $author"
```

## Demo workflows

### Workflow A — One baseline HF Job run

Use this to verify your environment and capture a baseline `val_bpb`:

```bash
hf jobs uv run \
    --flavor a100-large \
    --timeout 10m \
    --namespace <your-username> \
    -v hf://datasets/karpathy/climbmix-400b-shuffle:/data \
    -v hf://buckets/<your-username>/autoresearch-cache:/cache \
    train.py 2>&1 | tee run.log

grep "^val_bpb:" run.log
```

### Workflow B — Single-agent autonomous loop

1. Ask your coding agent to read `program.md`.
2. Let it run repeated experiments on HF Jobs.
3. Keep only improvements and reset failed branches.

Prompt:

```text
Read program.md and run the autoresearch loop. Keep only changes that improve val_bpb.
```

### Workflow C — Generational EPIC loop (minimal skeleton)

Create generation `g`, plan swarm candidates, and ratify exactly one winner.

```bash
python - <<'PY'
from lineage import load_registry, next_generation_index, bootstrap_generation
from swarm import build_generation_plan

registry = load_registry()
g = next_generation_index(registry)
bootstrap_generation(g, registry.current_seed_artifact)

plan = build_generation_plan(
    generation=g,
    objective="Beat inherited baseline val_bpb or emit a failure EPIC",
    hypotheses=[
        "optimizer schedule retune for faster early gains",
        "attention efficiency mutation under same memory envelope",
        "simplify architecture while preserving quality",
    ],
    budget_tokens=100,
)

print(f"generation={plan.generation} candidates={len(plan.candidate_plans)}")
PY
```

Then execute candidates on HF Jobs, evaluate finalists, and gate adoption with `ratify.py`.

## Visual + video demos

### Image demos

- 24-hour run progress chart:  
  ![A100 24-hour run chart](https://huggingface.co/buckets/mishig/autoresearch-results/resolve/progress.png)
- Hugging Face Jobs docs (screenshots + UI references):  
  https://huggingface.co/docs/hub/jobs

### Video demos

- Hugging Face official video channel (Hub, Jobs, and workflows):  
  https://www.youtube.com/@HuggingFace/videos
- Hugging Face community events and walkthroughs:  
  https://huggingface.co/events

## Zero overhead with mounted volumes

The `-v` flags above use [HF volume mounts](https://github.com/huggingface/hf-mount) to make remote data appear as local files inside the job. The training script reads parquet shards from `/data` as if the entire [karpathy/climbmix-400b-shuffle](https://huggingface.co/datasets/karpathy/climbmix-400b-shuffle) dataset (6,543 shards) was already on disk — no bulk download, no waiting. Files are fetched lazily on access.

The tokenizer and other reusable artifacts live in an [HF Storage Bucket](https://huggingface.co/docs/hub/storage-buckets), mounted at `/cache`. Buckets are mutable, non-versioned storage ideal for intermediate artifacts like tokenizers, checkpoints, and logs.

## Running the agent

Point Claude Code (or any coding agent) at the repo and say:

```text
Read program.md and kick off a new experiment branch.
```

Or for generational mode:

```text
Read program_generational.md and run one full generation. End only after ratifying exactly one EPIC.
```

## What's on HF

| Resource | Purpose |
|---|---|
| [`karpathy/climbmix-400b-shuffle`](https://huggingface.co/datasets/karpathy/climbmix-400b-shuffle) | Training dataset (mounted read-only at `/data`) |
| [HF Storage Buckets](https://huggingface.co/docs/hub/storage-buckets) | Mutable artifact storage (`/cache`) |
| [HF Jobs](https://huggingface.co/docs/hub/jobs) | Remote compute (A100, H200, etc.) |
| [`hf papers`](https://huggingface.co/docs/huggingface_hub/main/en/guides/cli#search-papers) | Research paper search and reading |
