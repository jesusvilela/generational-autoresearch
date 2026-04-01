# Generational Autoresearch

Autonomous LLM pretraining research running on [Hugging Face Jobs](https://huggingface.co/docs/hub/jobs). The harness runs in discrete **generations**: each inherits a proven artifact, explores a bounded set of experiments, and must ratify exactly one **EPIC** outcome before advancing to the next generation.

> Fork of [karpathy/autoresearch](https://github.com/karpathy/autoresearch), extended with generational lineage, swarm exploration, and ratification.

---

![val_bpb progress over 24 hours](https://huggingface.co/buckets/mishig/autoresearch-results/resolve/progress.png)

---

## How it works

Each generation is a bounded research cycle with a hard output contract:

1. **Inherit** — load the best artifact and compressed lineage memory from the previous generation
2. **Explore** — a swarm of role-based agents proposes and runs candidate experiments on HF Jobs
3. **Ratify** — exactly one candidate is adopted as the EPIC (Executable, Proven, Irreversible, Compounding) outcome
4. **Advance** — the adopted artifact and updated lineage become the seed for the next generation

The only file you edit is `train.py`. The only metric that matters is `val_bpb` (bits per byte on the validation set). Lower is better.

---

## Repository layout

```
train.py                    Self-contained training script (edit this)
generation.py               CLI: start / ratify / record
lineage.py                  Lineage registry and generation state helpers
swarm.py                    Role-based candidate planning
ratify.py                   Exactly-one-EPIC ratification gate
program.md                  Full operating constitution for the AI agent
lineage/
  registry.json             Append-only lineage index
templates/
  epic.md.j2                Canonical EPIC record template
  generation_report.md.j2   Generation summary template
results.tsv                 Experiment log (untracked by git)
```

---

## Prerequisites

- A Hugging Face account with [Jobs access](https://huggingface.co/docs/hub/jobs)
- The `hf` CLI installed and authenticated

```bash
# Install the HF CLI
curl -LsSf https://hf.co/cli/install.sh | bash

# Authenticate
hf auth login

# Verify
hf auth whoami
```

---

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/jesusvilela/generational-autoresearch
cd generational-autoresearch

# 2. Create an experiment branch (use today's date as the tag)
git checkout -b autoresearch/apr01

# 3. Create a results bucket (one-time, replace <username>)
hf buckets create <username>/autoresearch-results

# 4. Initialize the experiment log
printf 'commit\tval_bpb\tmemory_gb\tstatus\tpaper\tdescription\n' > results.tsv
```

---

## Running an experiment on HF Jobs

Every candidate experiment runs the same command. The script auto-detects the mounted volumes:

```bash
hf jobs uv run \
    --flavor a100-large \
    --timeout 10m \
    --namespace <your-username> \
    -v hf://datasets/karpathy/climbmix-400b-shuffle:/data \
    -v hf://buckets/<your-username>/autoresearch-cache:/cache \
    train.py 2>&1 | tee run.log
```

Extract the result:

```bash
grep "^val_bpb:" run.log
```

Full output format:

```
---
val_bpb:          0.997900
training_seconds: 300.1
total_seconds:    325.9
peak_vram_mb:     45060.2
mfu_percent:      39.80
total_tokens_M:   499.6
num_steps:        953
num_params_M:     50.3
depth:            8
```

---

## Generation CLI

Three commands drive one complete generation.

### `start` — bootstrap a generation workspace

Creates the generation directory, writes `genesis.md` with the objective, and builds `candidates/plan.json` with the swarm candidate list.

```bash
python generation.py start \
  --objective "Improve val_bpb by rethinking positional encoding" \
  --hypothesis "Replace learned absolute PE with RoPE" \
  --hypothesis "Remove PE entirely and rely on causal mask" \
  --hypothesis "Sinusoidal PE at half the embedding dimension" \
  --budget-tokens 100
```

Optional flags:

| Flag | Default | Description |
|---|---|---|
| `--max-candidates N` | unlimited | Hard cap on number of candidates to plan |
| `--registry-path PATH` | `lineage/registry.json` | Path to the lineage registry |

Output:

```
generation=0
root=lineage/gen_000
plan=lineage/gen_000/candidates/plan.json
candidates=3
```

---

### `ratify` — select exactly one EPIC winner

After running all candidate experiments and recording their results, write an `evaluated.json` file — a JSON array of evaluated candidates — then run ratification:

```bash
python generation.py ratify \
  --candidates lineage/gen_000/candidates/evaluated.json
```

The `evaluated.json` format (one object per candidate):

```json
[
  {
    "candidate_id": "cand_000",
    "epic_type": "code_change",
    "metric_value": 0.9921,
    "baseline_metric": 0.9979,
    "executable": true,
    "validated": true,
    "simplicity_score": 0.8,
    "leverage_score": 0.7,
    "robustness_score": 0.9,
    "note": "RoPE: clean swap, no regressions"
  },
  {
    "candidate_id": "cand_001",
    "epic_type": "code_change",
    "metric_value": 0.9985,
    "baseline_metric": 0.9979,
    "executable": true,
    "validated": true,
    "simplicity_score": 0.9,
    "leverage_score": 0.5,
    "robustness_score": 0.7,
    "note": "No PE: worse than baseline"
  }
]
```

Candidates are ranked by: improvement magnitude → robustness → simplicity → future leverage. The winner is written to `lineage/gen_000/epic/winner.json`. If no candidate strictly improves on the baseline, ratification fails — emit a failure EPIC via `record` instead.

Output:

```
winner=cand_000
epic_type=code_change
metric=0.9921
written=lineage/gen_000/epic/winner.json
```

---

### `record` — commit the EPIC to the lineage registry

Reads `winner.json` and appends the generation record to `lineage/registry.json`, advancing the seed artifact for the next generation.

```bash
python generation.py record \
  --claim "RoPE replaces learned absolute PE: -0.0058 val_bpb, -200 params, cleaner code" \
  --artifact train.py \
  --do-more "positional encoding ablations" \
  --do-more "RoPE hyperparameter sweep" \
  --avoid "learned absolute positional embeddings" \
  --open-question "Does RoPE scaling help beyond 2048 context?"
```

Optional flags:

| Flag | Default | Description |
|---|---|---|
| `--winner PATH` | auto-detected | Path to `winner.json` (defaults to current generation's epic dir) |
| `--do-more TEXT` | — | Guidance for future generations (repeat for multiple) |
| `--avoid TEXT` | — | Anti-patterns to avoid (repeat for multiple) |
| `--open-question TEXT` | — | Open research question to carry forward |
| `--registry-path PATH` | `lineage/registry.json` | Path to the lineage registry |

Output:

```
generation=0
epic_type=code_change
artifact=train.py
```

---

## Full generation walkthrough

```bash
# ── 1. Start generation 0 ──────────────────────────────────────────────────
python generation.py start \
  --objective "Establish baseline and explore positional encoding alternatives" \
  --hypothesis "Baseline: run train.py unmodified" \
  --hypothesis "RoPE instead of learned absolute PE" \
  --hypothesis "Muon optimizer instead of Adam"

# ── 2. Run each candidate on HF Jobs ──────────────────────────────────────
# (repeat for each hypothesis, saving logs as run_000.log, run_001.log, etc.)
hf jobs uv run \
    --flavor a100-large \
    --timeout 10m \
    --namespace <your-username> \
    -v hf://datasets/karpathy/climbmix-400b-shuffle:/data \
    -v hf://buckets/<your-username>/autoresearch-cache:/cache \
    train.py 2>&1 | tee run_001.log

# ── 3. Log results to results.tsv ─────────────────────────────────────────
# (tab-separated; do not commit this file)
# commit   val_bpb    memory_gb  status  paper       description
# a1b2c3d  0.997900   44.0       keep    -           baseline
# b2c3d4e  0.992100   44.1       keep    2503.08234  RoPE positional encoding
# c3d4e5f  0.998800   44.3       discard -           Muon: no improvement

# ── 4. Write evaluated.json and ratify ────────────────────────────────────
python generation.py ratify \
  --candidates lineage/gen_000/candidates/evaluated.json

# ── 5. Commit and save best files ─────────────────────────────────────────
git add train.py && git commit -m "gen_000: RoPE positional encoding"

hf buckets cp train.py    hf://buckets/<your-username>/autoresearch-results/best_train.py
hf buckets cp results.tsv hf://buckets/<your-username>/autoresearch-results/results.tsv

# ── 6. Record EPIC to lineage ─────────────────────────────────────────────
python generation.py record \
  --claim "RoPE replaces learned PE: -0.0058 val_bpb with simpler code" \
  --artifact train.py \
  --do-more "RoPE scaling experiments" \
  --avoid "learned absolute positional embeddings"

# ── 7. Advance to generation 1 ────────────────────────────────────────────
python generation.py start \
  --objective "Build on RoPE: explore attention and optimizer changes" \
  --hypothesis "..."
```

---

## Logging results

`results.tsv` is tab-separated (not comma-separated). **Do not commit it.**

```
commit	val_bpb	memory_gb	status	paper	description
a1b2c3d	0.997900	44.0	keep	-	baseline
b2c3d4e	0.992100	44.1	keep	2503.08234	RoPE positional encoding
c3d4e5f	0.998800	44.3	discard	-	Muon optimizer, no improvement
d4e5f6g	0.000000	0.0	crash	-	doubled width, OOM
```

Column reference:

| Column | Description |
|---|---|
| `commit` | 7-character git hash |
| `val_bpb` | Validation bits-per-byte (0.000000 for crashes) |
| `memory_gb` | `peak_vram_mb / 1024`, rounded to one decimal (0.0 for crashes) |
| `status` | `keep`, `discard`, or `crash` |
| `paper` | Paper ID that inspired the change, or `-` |
| `description` | Short description of the experiment |

---

## Research with `hf papers`

Before each experiment, search for relevant techniques:

```bash
# Search by topic
hf papers search "efficient transformer training"
hf papers search "rotary positional encoding"
hf papers search "optimizer pretraining"
hf papers search "small language model architecture"

# Read a paper in full
hf papers read 2104.09864
```

Log the paper ID in `results.tsv` when a paper directly inspires an experiment.

---

## Rules and constraints

**You can change:**
- Model architecture (layers, heads, width, attention variants)
- Optimizer and learning rate schedule
- Batch size and sequence handling
- Any part of the training loop

**You cannot change:**
- `evaluate_bpb` — this is the ground truth metric
- The dataloader, tokenizer, or constants (`MAX_SEQ_LEN`, `TIME_BUDGET`, `EVAL_TOKENS`)
- Dependencies beyond the inline UV metadata

**Simplicity criterion:** a marginal improvement that adds complex code is not worth it. Equal results with simpler code is a win. Removing code and keeping quality is the best outcome.

**VRAM:** soft constraint. Meaningful gains justify modest increases; significant blowups do not.

---

## Failure semantics

If no candidate improves the baseline, the generation still produces a failure EPIC:

- A negative-result codex (what definitely does not work)
- A pruning rule to avoid repeated waste in future generations
- A bug or failure taxonomy
- An evaluator improvement that prevents the same crash

Record it the same way: `python generation.py record --claim "..."`. Failure EPICs are first-class lineage assets.

---

## Resource index

| Resource | Purpose |
|---|---|
| [`karpathy/climbmix-400b-shuffle`](https://huggingface.co/datasets/karpathy/climbmix-400b-shuffle) | Training dataset, mounted read-only at `/data` |
| [HF Storage Buckets](https://huggingface.co/docs/hub/storage-buckets) | Mutable artifact storage, mounted at `/cache` |
| [HF Jobs](https://huggingface.co/docs/hub/jobs) | Remote GPU compute (A100, H200, etc.) |
| [`hf papers`](https://huggingface.co/docs/huggingface_hub/main/en/guides/cli#search-papers) | Research paper search and reading |

---

## Experiment results

| generation | commit | val_bpb | description |
|---|---|---|---|
| — | — | — | No runs yet |
