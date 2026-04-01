<h1 align="center">Generational Autoresearch</h1>

<p align="center">
  Autonomous LLM pretraining research on Hugging Face infrastructure.<br>
  Each generation inherits a proven model, explores bounded experiments, and ratifies exactly one compounding improvement.
</p>

<p align="center">
  <a href="https://huggingface.co/docs/hub/jobs"><img src="https://img.shields.io/badge/runs%20on-HF%20Jobs-FFD21E?logo=huggingface&logoColor=black" alt="HF Jobs"></a>
  <img src="https://img.shields.io/badge/metric-val__bpb-4A90D9" alt="metric: val_bpb">
  <img src="https://img.shields.io/badge/GPU-A100%20%7C%20H200-76B900?logo=nvidia&logoColor=white" alt="GPU">
  <img src="https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+">
</p>

---

<p align="center">
  <img src="https://huggingface.co/buckets/mishig/autoresearch-results/resolve/progress.png" alt="val_bpb progress over 24 hours" width="720">
</p>

---

## How it works

Each run is structured as a sequence of **generations**. A generation is a bounded research cycle with a hard output contract — it cannot end without producing one ratified outcome.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Generation  g                               │
│                                                                     │
│   Inherit              Explore                Ratify   Advance      │
│  ─────────         ─────────────────         ───────  ─────────     │
│  train.py   ──▶   outer-ring swarm    ──▶   one EPIC  ──▶  g+1     │
│  registry          runs HF Jobs              adopted               │
│                    scores candidates                                │
└─────────────────────────────────────────────────────────────────────┘
```

**EPIC** is the adoption standard. A candidate must be all four:

| Letter | Meaning |
|:---:|---|
| **E** | Executable — runnable artifact or operationally usable process |
| **P** | Proven — validated on the declared eval (`val_bpb`) |
| **I** | Irreversible — adopted into lineage state, not tentative |
| **C** | Compounding — increases future search or build capability |

The only file you edit is `train.py`. The only metric that matters is `val_bpb` (bits per byte, lower is better, 5-minute time budget).

---

## Repository layout

```
generational-autoresearch/
│
├── train.py                     ← the only file you edit
├── generation.py                ← CLI: start · ratify · record
├── lineage.py                   ← registry and generation state helpers
├── swarm.py                     ← role-based candidate planning
├── ratify.py                    ← exactly-one-EPIC ratification gate
├── program.md                   ← operating constitution for the AI agent
│
├── lineage/
│   └── registry.json            ← append-only lineage index
│
├── templates/
│   ├── epic.md.j2               ← canonical EPIC record template
│   └── generation_report.md.j2  ← generation summary template
│
└── results.tsv                  ← experiment log (untracked by git)
```

---

## Prerequisites

- A Hugging Face account with [Jobs access](https://huggingface.co/docs/hub/jobs)
- The `hf` CLI installed and authenticated

```bash
# Install
curl -LsSf https://hf.co/cli/install.sh | bash

# Authenticate
hf auth login

# Verify
hf auth whoami
```

---

## Setup

```bash
# 1. Clone
git clone https://github.com/jesusvilela/generational-autoresearch
cd generational-autoresearch

# 2. Create an experiment branch  (tag = today's date)
git checkout -b autoresearch/apr01

# 3. Create a results bucket  (one-time per account)
hf buckets create <username>/autoresearch-results

# 4. Initialize the experiment log
printf 'commit\tval_bpb\tmemory_gb\tstatus\tpaper\tdescription\n' > results.tsv
```

---

## Running a candidate on HF Jobs

Every experiment runs the same command. `train.py` auto-detects the mounted volumes:

```bash
hf jobs uv run \
    --flavor   a100-large \
    --timeout  10m \
    --namespace <your-username> \
    -v hf://datasets/karpathy/climbmix-400b-shuffle:/data \
    -v hf://buckets/<your-username>/autoresearch-cache:/cache \
    train.py 2>&1 | tee run.log
```

Extract the key metric:

```bash
grep "^val_bpb:" run.log
```

<details>
<summary>Full output format</summary>

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

</details>

---

## Generation CLI

Three verbs drive one complete generation: **start → ratify → record**.

---

### `start` — bootstrap a generation workspace

Creates the generation directory, writes `genesis.md`, and builds `candidates/plan.json`.

```bash
python generation.py start \
  --objective "Improve val_bpb by rethinking positional encoding" \
  --hypothesis "Replace learned absolute PE with RoPE" \
  --hypothesis "Remove PE entirely and rely on causal mask" \
  --hypothesis "Sinusoidal PE at half the embedding dimension" \
  --budget-tokens 100
```

| Flag | Default | Description |
|---|---|---|
| `--objective TEXT` | required | Generation objective |
| `--hypothesis TEXT` | required (repeat) | One candidate hypothesis per flag |
| `--budget-tokens N` | `100` | Planning token budget |
| `--max-candidates N` | unlimited | Hard cap on planned candidates |
| `--registry-path PATH` | `lineage/registry.json` | Lineage registry location |

```
generation=0
root=lineage/gen_000
plan=lineage/gen_000/candidates/plan.json
candidates=3
```

---

### `ratify` — select exactly one EPIC winner

After running all candidates and scoring them, write `evaluated.json` — a JSON array of evaluated candidate objects — then run ratification:

```bash
python generation.py ratify \
  --candidates lineage/gen_000/candidates/evaluated.json
```

**`evaluated.json` schema:**

```json
[
  {
    "candidate_id":    "cand_000",
    "epic_type":       "code_change",
    "metric_value":    0.9921,
    "baseline_metric": 0.9979,
    "executable":      true,
    "validated":       true,
    "simplicity_score":  0.8,
    "leverage_score":    0.7,
    "robustness_score":  0.9,
    "note": "RoPE: clean swap, no regressions on two reruns"
  },
  {
    "candidate_id":    "cand_001",
    "epic_type":       "code_change",
    "metric_value":    0.9985,
    "baseline_metric": 0.9979,
    "executable":      true,
    "validated":       true,
    "simplicity_score":  0.9,
    "leverage_score":    0.5,
    "robustness_score":  0.7,
    "note": "No PE: regressed vs baseline"
  }
]
```

Ranking order: **improvement → robustness → simplicity → leverage**. The winner is written to `lineage/gen_000/epic/winner.json`. If no candidate strictly beats the baseline, ratification raises an error — produce a failure EPIC via `record` instead.

| Flag | Default | Description |
|---|---|---|
| `--candidates PATH` | required | JSON array of evaluated candidates |
| `--registry-path PATH` | `lineage/registry.json` | Lineage registry location |

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
  --claim         "RoPE replaces learned absolute PE: −0.0058 val_bpb, −200 params, cleaner code" \
  --artifact      train.py \
  --do-more       "positional encoding ablations" \
  --do-more       "RoPE hyperparameter sweep (base frequency)" \
  --avoid         "learned absolute positional embeddings" \
  --open-question "Does RoPE frequency scaling help beyond 2048 context?"
```

| Flag | Default | Description |
|---|---|---|
| `--claim TEXT` | required | One-sentence description of what changed |
| `--artifact PATH` | `train.py` | Adopted artifact |
| `--winner PATH` | auto-detected | Path to `winner.json` (defaults to current generation's epic dir) |
| `--do-more TEXT` | — | Guidance for future generations (repeat for multiple) |
| `--avoid TEXT` | — | Anti-patterns to carry forward (repeat for multiple) |
| `--open-question TEXT` | — | Open research question |
| `--registry-path PATH` | `lineage/registry.json` | Lineage registry location |

```
generation=0
epic_type=code_change
artifact=train.py
```

---

## Full generation walkthrough

```bash
# ── 1. Bootstrap ───────────────────────────────────────────────────────────
python generation.py start \
  --objective "Explore positional encoding alternatives on top of baseline" \
  --hypothesis "Baseline: train.py unmodified" \
  --hypothesis "RoPE in place of learned absolute PE" \
  --hypothesis "Muon optimizer in place of AdamW"

# ── 2. Run candidates on HF Jobs ───────────────────────────────────────────
# Repeat for each hypothesis; save each log as run_000.log, run_001.log, …
hf jobs uv run \
    --flavor a100-large --timeout 10m \
    --namespace <your-username> \
    -v hf://datasets/karpathy/climbmix-400b-shuffle:/data \
    -v hf://buckets/<your-username>/autoresearch-cache:/cache \
    train.py 2>&1 | tee run_001.log

# ── 3. Append to results.tsv ───────────────────────────────────────────────
# commit   val_bpb    memory_gb  status  paper       description
# a1b2c3d  0.997900   44.0       keep    -           baseline
# b2c3d4e  0.992100   44.1       keep    2503.08234  RoPE positional encoding
# c3d4e5f  0.998800   44.3       discard -           Muon: no improvement

# ── 4. Ratify ──────────────────────────────────────────────────────────────
# Write lineage/gen_000/candidates/evaluated.json first, then:
python generation.py ratify \
  --candidates lineage/gen_000/candidates/evaluated.json

# ── 5. Commit + save to bucket ─────────────────────────────────────────────
git add train.py && git commit -m "gen_000: RoPE positional encoding"

hf buckets cp train.py    hf://buckets/<your-username>/autoresearch-results/best_train.py
hf buckets cp results.tsv hf://buckets/<your-username>/autoresearch-results/results.tsv

# ── 6. Record EPIC ─────────────────────────────────────────────────────────
python generation.py record \
  --claim    "RoPE replaces learned PE: −0.0058 val_bpb with simpler code" \
  --artifact train.py \
  --do-more  "RoPE scaling experiments" \
  --avoid    "learned absolute positional embeddings"

# ── 7. Advance ─────────────────────────────────────────────────────────────
python generation.py start \
  --objective "Build on RoPE — explore attention and optimizer changes" \
  --hypothesis "..."
```

---

## Logging results

`results.tsv` is **tab-separated** (commas break descriptions). Do not commit it.

```
commit   val_bpb   memory_gb   status   paper        description
a1b2c3d  0.997900  44.0        keep     -            baseline
b2c3d4e  0.992100  44.1        keep     2503.08234   RoPE positional encoding
c3d4e5f  0.998800  44.3        discard  -            Muon: no improvement
d4e5f6g  0.000000  0.0         crash    -            doubled width, OOM
```

| Column | Description |
|---|---|
| `commit` | 7-character git hash |
| `val_bpb` | Validation bits-per-byte (0.000000 for crashes) |
| `memory_gb` | `peak_vram_mb ÷ 1024`, one decimal (0.0 for crashes) |
| `status` | `keep` · `discard` · `crash` |
| `paper` | arXiv paper ID or `-` |
| `description` | Short description |

---

## Research with `hf papers`

Search for techniques before each experiment. Skim — you need one concrete implementable idea, not a full read.

```bash
# Keyword search
hf papers search "efficient transformer training"
hf papers search "rotary positional encoding"
hf papers search "optimizer small language model"

# Read a promising paper
hf papers read 2104.09864
```

Log the paper ID in `results.tsv` whenever a paper directly inspires an experiment.

---

## Rules

<table>
<tr>
<td valign="top" width="50%">

**Can change**
- Model architecture (depth, width, heads, attention variants)
- Optimizer and learning rate schedule
- Batch size and gradient accumulation
- Any part of the training loop

</td>
<td valign="top" width="50%">

**Cannot change**
- `evaluate_bpb` — ground truth metric
- Dataloader, tokenizer, or constants (`MAX_SEQ_LEN`, `TIME_BUDGET`, `EVAL_TOKENS`)
- Dependencies beyond the inline UV metadata

</td>
</tr>
</table>

**Simplicity criterion** — a marginal gain that adds complex code is not worth it. Equal results with less code is a win. Deleting code while keeping quality is the best outcome.

**VRAM** — soft constraint. Meaningful gains justify modest increases; blowups do not.

---

## Failure semantics

A generation that cannot improve still produces a **failure EPIC** — first-class lineage assets:

- Negative-result codex (what definitely does not work)
- Pruning rule to avoid the same waste in future generations
- Bug or failure taxonomy
- Evaluator improvement that prevents a repeated crash

Record it the same way: `python generation.py record --claim "..."`.

---

## Resources

| | Resource | Purpose |
|:---:|---|---|
| ![HF](https://img.shields.io/badge/-Dataset-FFD21E?logo=huggingface&logoColor=black) | [`karpathy/climbmix-400b-shuffle`](https://huggingface.co/datasets/karpathy/climbmix-400b-shuffle) | Training data, mounted read-only at `/data` |
| ![HF](https://img.shields.io/badge/-Buckets-FFD21E?logo=huggingface&logoColor=black) | [HF Storage Buckets](https://huggingface.co/docs/hub/storage-buckets) | Mutable artifact storage, mounted at `/cache` |
| ![HF](https://img.shields.io/badge/-Jobs-FFD21E?logo=huggingface&logoColor=black) | [HF Jobs](https://huggingface.co/docs/hub/jobs) | Remote GPU compute (A100, H200, …) |
| ![HF](https://img.shields.io/badge/-Papers-FFD21E?logo=huggingface&logoColor=black) | [`hf papers`](https://huggingface.co/docs/huggingface_hub/main/en/guides/cli#search-papers) | Research paper search and reading |

---

## Experiment results

| Generation | Commit | `val_bpb` | Description |
|:---:|:---:|:---:|---|
| — | — | — | No runs yet — be the first |
