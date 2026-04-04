# generational-autoresearch

autonomous llm pretraining research. one metric. one artifact. one compounding improvement per generation — or a documented failure. nothing in between.

runs entirely on [Hugging Face Jobs](https://huggingface.co/docs/hub/jobs). the only file you edit is `train.py`. the only number that matters is `val_bpb` — lower is better.

&nbsp;

```
  ┌──────────────────────────────────────────────────────────┐
  │                                                          │
  │   inherit ──▶ explore ──▶ ratify ──▶ advance             │
  │      ↑                                   │              │
  │      └──────────────── g+1 ──────────────┘              │
  │                                                          │
  └──────────────────────────────────────────────────────────┘
```

&nbsp;

## what is an EPIC

a candidate is only ratifiable if it is all four:

```
  E  executable    runnable artifact or operational process
  P  proven        validated on val_bpb
  I  irreversible  adopted into lineage, not tentative
  C  compounding   improves future search or build capability
```

if no candidate clears the bar, the generation still ends — with a documented failure EPIC that prunes future search space.

&nbsp;

## files

```
train.py                      ← edit this. nothing else.
generation.py                 ← cli: start · ratify · record
lineage.py                    ← registry + state helpers
swarm.py                      ← candidate planning
ratify.py                     ← exactly-one-EPIC gate
program.md                    ← agent operating constitution
lineage/registry.json         ← append-only lineage index
results.tsv                   ← experiment log  (do not commit)
```

&nbsp;

## setup

```bash
# install hf cli
curl -LsSf https://hf.co/cli/install.sh | bash
hf auth login

# clone + branch  (tag = today's date)
git clone https://github.com/jesusvilela/generational-autoresearch
cd generational-autoresearch
git checkout -b autoresearch/apr01

# one-time: create results bucket
hf buckets create <username>/autoresearch-results

# init experiment log
printf 'commit\tval_bpb\tmemory_gb\tstatus\tpaper\tdescription\n' > results.tsv
```

&nbsp;

## run a candidate

every experiment is the same command:

```bash
hf jobs uv run \
  --flavor    a100-large \
  --timeout   10m \
  --namespace <username> \
  -v hf://datasets/karpathy/climbmix-400b-shuffle:/data \
  -v hf://buckets/<username>/autoresearch-cache:/cache \
  train.py 2>&1 | tee run.log
```

extract the metric:

```bash
grep "^val_bpb:" run.log
```

<details>
<summary>full output format</summary>

```
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

&nbsp;

## cli — three verbs, one generation

&nbsp;

### start

bootstrap the generation workspace. creates `lineage/gen_NNN/` with `genesis.md` and `candidates/plan.json`.

```bash
python generation.py start \
  --objective  "rethink positional encoding" \
  --hypothesis "replace learned absolute PE with RoPE" \
  --hypothesis "remove PE entirely, rely on causal mask" \
  --hypothesis "sinusoidal PE at half embedding dimension" \
  --budget-tokens 100
```

| flag | default | |
|---|---|---|
| `--objective TEXT` | required | generation objective |
| `--hypothesis TEXT` | required, repeatable | one candidate per flag |
| `--budget-tokens N` | `100` | planning budget |
| `--max-candidates N` | — | hard cap on candidates |
| `--registry-path PATH` | `lineage/registry.json` | |

```
generation=0
root=lineage/gen_000
plan=lineage/gen_000/candidates/plan.json
candidates=3
```

&nbsp;

### ratify

score your candidates, write `evaluated.json`, then select exactly one winner:

```bash
python generation.py ratify \
  --candidates lineage/gen_000/candidates/evaluated.json
```

**`evaluated.json`** — one object per candidate:

```json
[
  {
    "candidate_id":     "cand_000",
    "epic_type":        "code_change",
    "metric_value":     0.9921,
    "baseline_metric":  0.9979,
    "executable":       true,
    "validated":        true,
    "simplicity_score": 0.8,
    "leverage_score":   0.7,
    "robustness_score": 0.9,
    "note":             "RoPE: clean swap, stable across two reruns"
  },
  {
    "candidate_id":     "cand_001",
    "epic_type":        "code_change",
    "metric_value":     0.9985,
    "baseline_metric":  0.9979,
    "executable":       true,
    "validated":        true,
    "simplicity_score": 0.9,
    "leverage_score":   0.5,
    "robustness_score": 0.7,
    "note":             "no PE: regressed vs baseline"
  }
]
```

ranking: **improvement → robustness → simplicity → leverage**

writes winner to `lineage/gen_000/epic/winner.json`. if nothing beats the baseline, emit a failure EPIC via `record`.

| flag | default | |
|---|---|---|
| `--candidates PATH` | required | evaluated candidates JSON |
| `--registry-path PATH` | `lineage/registry.json` | |

```
winner=cand_000
epic_type=code_change
metric=0.9921
written=lineage/gen_000/epic/winner.json
```

&nbsp;

### record

commit the ratified EPIC to `lineage/registry.json`. advances seed artifact to the next generation.

```bash
python generation.py record \
  --claim         "RoPE replaces learned absolute PE: -0.0058 val_bpb, -200 params" \
  --artifact      train.py \
  --do-more       "RoPE hyperparameter sweep" \
  --avoid         "learned absolute positional embeddings" \
  --open-question "does RoPE frequency scaling help beyond 2048 context?"
```

| flag | default | |
|---|---|---|
| `--claim TEXT` | required | one-sentence description |
| `--artifact PATH` | `train.py` | adopted artifact |
| `--winner PATH` | auto-detected | path to `winner.json` |
| `--do-more TEXT` | — | carry-forward guidance, repeatable |
| `--avoid TEXT` | — | anti-patterns, repeatable |
| `--open-question TEXT` | — | open question for next generation |
| `--registry-path PATH` | `lineage/registry.json` | |

```
generation=0
epic_type=code_change
artifact=train.py
```

&nbsp;

## full generation walkthrough

```bash
# 1 · bootstrap
python generation.py start \
  --objective  "positional encoding ablation" \
  --hypothesis "baseline: unmodified train.py" \
  --hypothesis "RoPE in place of learned absolute PE" \
  --hypothesis "Muon optimizer in place of AdamW"

# 2 · run each hypothesis on HF Jobs
#     save logs as run_000.log, run_001.log, run_002.log
hf jobs uv run \
  --flavor a100-large --timeout 10m \
  --namespace <username> \
  -v hf://datasets/karpathy/climbmix-400b-shuffle:/data \
  -v hf://buckets/<username>/autoresearch-cache:/cache \
  train.py 2>&1 | tee run_001.log

# 3 · log to results.tsv  (tab-separated, do not commit)
# a1b2c3d  0.9979  44.0  keep     -           baseline
# b2c3d4e  0.9921  44.1  keep     2503.08234  RoPE
# c3d4e5f  0.9988  44.3  discard  -           Muon: no improvement

# 4 · ratify
python generation.py ratify \
  --candidates lineage/gen_000/candidates/evaluated.json

# 5 · commit + save best to bucket
git add train.py
git commit -m "gen_000: RoPE positional encoding"

hf buckets cp train.py    hf://buckets/<username>/autoresearch-results/best_train.py
hf buckets cp results.tsv hf://buckets/<username>/autoresearch-results/results.tsv

# 6 · record EPIC
python generation.py record \
  --claim    "RoPE replaces learned PE: -0.0058 val_bpb with simpler code" \
  --artifact train.py \
  --do-more  "RoPE scaling" \
  --avoid    "learned absolute positional embeddings"

# 7 · next generation
python generation.py start \
  --objective "build on RoPE — explore attention and optimizer changes" \
  --hypothesis "..."
```

&nbsp;

## logging

`results.tsv` — tab-separated. **do not commit.**

```
commit   val_bpb   memory_gb   status    paper        description
a1b2c3d  0.9979    44.0        keep      -            baseline
b2c3d4e  0.9921    44.1        keep      2503.08234   RoPE
c3d4e5f  0.9988    44.3        discard   -            Muon: no gain
d4e5f6g  0.0000    0.0         crash     -            doubled width, OOM
```

| column | notes |
|---|---|
| `val_bpb` | 0.000000 for crashes |
| `memory_gb` | `peak_vram_mb ÷ 1024`, one decimal · 0.0 for crashes |
| `status` | `keep` · `discard` · `crash` |
| `paper` | arXiv ID or `-` |

&nbsp;

## research

search before each experiment. skim — you need one concrete idea, not a full read.

```bash
hf papers search "rotary positional encoding"
hf papers search "optimizer small language model"
hf papers search "efficient transformer pretraining"

hf papers read 2104.09864
```

&nbsp;

## rules

**you can change** — architecture, optimizer, learning rate schedule, batch size, anything in the training loop.

**you cannot change** — `evaluate_bpb`, the dataloader, tokenizer, or constants (`MAX_SEQ_LEN`, `TIME_BUDGET`, `EVAL_TOKENS`).

**simplicity wins** — equal results with less code beats a marginal gain with added complexity. deleting code and keeping quality is the best possible outcome.

**VRAM** — soft constraint. meaningful gains justify modest increases.

&nbsp;

## failure semantics

a generation that cannot improve still produces a failure EPIC:

- what definitely doesn't work (negative-result codex)
- a pruning rule so future generations don't repeat the waste
- a bug or failure taxonomy
- an evaluator fix that prevents the same crash

`python generation.py record --claim "..."` — same command, same weight.

&nbsp;

## links

[HF Jobs](https://huggingface.co/docs/hub/jobs) · [HF Storage Buckets](https://huggingface.co/docs/hub/storage-buckets) · [karpathy/climbmix-400b-shuffle](https://huggingface.co/datasets/karpathy/climbmix-400b-shuffle) · [hf papers cli](https://huggingface.co/docs/huggingface_hub/main/en/guides/cli#search-papers)

&nbsp;

## results

| gen | commit | val_bpb | description |
|:---:|:---:|:---:|---|
| — | — | — | first run pending |
