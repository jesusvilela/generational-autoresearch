# autoresearch on Hugging Face

Autonomous LLM pretraining research running entirely on [Hugging Face Jobs](https://huggingface.co/docs/hub/jobs). The harness keeps the atomic loop simple: modify one executable (`train.py`), run it remotely, measure one metric (`val_bpb`), and keep/discard changes.

Fork of [karpathy/autoresearch](https://github.com/karpathy/autoresearch), adapted for HF Jobs + mounted datasets + storage buckets.

---

## What this repo gives you

- **Single-file training target**: `train.py` is the only model program you mutate.
- **Agent operating contracts**:
  - `program.md` (single-agent loop)
  - `program_generational.md` (lineage + exactly-one-EPIC loop)
- **Generational helpers**:
  - `lineage.py` (registry + generation bootstrap)
  - `swarm.py` (candidate planning)
  - `ratify.py` (exactly-one winner gate)
  - `generation.py` (one-command generation bootstrap + plan output)

---

## Modes

### 1) Single-agent mode (`program.md`)

```
research -> edit train.py -> run HF Job -> score -> keep/discard
```

Use this when you want fastest iteration and minimal ceremony.

### 2) Generational mode (`program_generational.md`)

```
inherit -> swarm explore -> ratify exactly one EPIC -> compress memory -> spawn next generation
```

Use this when you want bounded generations and cumulative lineage memory.

---

## Quick start

### Prerequisites

- A Hugging Face account with Jobs access.
- CLI installed and authenticated.

```bash
# Install CLI
curl -LsSf https://hf.co/cli/install.sh | bash

# Login
hf auth login

# Confirm identity
author=$(hf auth whoami | head -n1)
echo "Running as: $author"
```

### Required mounts

- Dataset mount (`/data`):
  `hf://datasets/karpathy/climbmix-400b-shuffle:/data`
- Bucket mount (`/cache`) for tokenizer/checkpoints/logs:
  `hf://buckets/<your-username>/autoresearch-cache:/cache`

`train.py` auto-detects `/data` and `/cache/tokenizer` when available.

---

## Practical workflows (copy/paste)

### Workflow A — Baseline run + metric extraction

Use this first. It validates the environment and gives your baseline `val_bpb`.

```bash
hf jobs uv run \
  --flavor a100-large \
  --timeout 10m \
  --namespace <your-username> \
  -v hf://datasets/karpathy/climbmix-400b-shuffle:/data \
  -v hf://buckets/<your-username>/autoresearch-cache:/cache \
  train.py 2>&1 | tee run.log

# Pull the most recent validation score from logs
grep '^val_bpb:' run.log | tail -n1
```

### Workflow B — Single-agent autonomous loop

Prompt your coding agent:

```text
Read program.md and run the autoresearch loop. Keep only changes that improve val_bpb.
```

Recommended guardrails:

- Limit each run with `--timeout`.
- Commit only if `val_bpb` improves.
- Revert failed mutations quickly.

### Workflow C — One generational cycle (simplest path)

```bash
python generation.py start \
  --objective "Beat inherited baseline val_bpb or emit a failure EPIC" \
  --hypothesis "optimizer schedule retune for faster early gains" \
  --hypothesis "attention efficiency mutation under same memory envelope" \
  --hypothesis "simplify architecture while preserving quality" \
  --budget-tokens 100 \
  --max-candidates 4
```

Then:
1. Run planned candidates on HF Jobs.
2. Evaluate finalists against the inherited state.
3. Use `ratify.py` to adopt **exactly one** EPIC.
4. Record lineage delta for the next generation.

Notes:
- The planner deduplicates near-identical hypotheses.
- Candidate count is budget-aware (`budget_tokens`) and can be hard-capped (`--max-candidates`).

---

## Usability notes and common pitfalls

### 1) No `val_bpb` found in logs

- Confirm the job actually reached evaluation before timeout.
- Increase timeout from `10m` to `20m` for slower flavors.
- Verify dataset and cache mounts were attached correctly.

### 2) Reproducibility drift

- Compare candidates against the **same baseline conditions**.
- Re-run finalists once before adoption in generational mode.
- Record exact command, flavor, and timeout with each result.

### 3) Slow startup / missing tokenizer artifacts

- Ensure bucket mount path is correct and writable.
- Reuse `/cache` across runs to avoid repeated artifact rebuilds.

---

## Demos (image + video)

- Example 24-hour artifact bucket:  
  https://huggingface.co/buckets/mishig/autoresearch-results
- Progress image:  
  ![Example val_bpb progress over time](https://huggingface.co/buckets/mishig/autoresearch-results/resolve/progress.png)
- HF Jobs docs (UI and usage):  
  https://huggingface.co/docs/hub/jobs
- Hugging Face videos:  
  https://www.youtube.com/@HuggingFace/videos

---

## Resource index

| Resource | Purpose |
|---|---|
| [`train.py`](./train.py) | Executable training target mutated by the agent |
| [`program.md`](./program.md) | Single-agent operating constitution |
| [`program_generational.md`](./program_generational.md) | Generational EPIC contract |
| [`lineage.py`](./lineage.py) | Registry I/O and generation bootstrap |
| [`swarm.py`](./swarm.py) | Candidate planning and role layout |
| [`ratify.py`](./ratify.py) | Exactly-one-EPIC selection gate |
| [`generation.py`](./generation.py) | CLI to bootstrap generation and write candidate plan |
| [`lineage/registry.json`](./lineage/registry.json) | Current lineage head |

---

## Suggested prompts

Single-agent:

```text
Read program.md and kick off a new experiment branch.
```

Generational:

```text
Read program_generational.md and run one full generation. End only after ratifying exactly one EPIC.
```
