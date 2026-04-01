# generational autoresearch

An autonomous research harness where each generation produces exactly one EPIC outcome and hands it forward to the next.

## Core concept

Each generation is a bounded research cycle. It inherits state, runs experiments, and must ratify **exactly one EPIC**:

- **Executable**: runnable artifact or operationally usable process
- **Proven**: validated on the declared eval (`val_bpb` by default)
- **Irreversible**: adopted into lineage state
- **Compounding**: increases future search/build/verification capability

Generation recursion: `G_{g+1} = H(S_g, K_g)` where `S_g = adopt(EPIC_g)`, `K_g` is lineage memory, and `H` is the research harness.

## Setup

1. **Agree on a run tag**: propose a tag based on today's date (e.g. `apr01`). The branch `autoresearch/<tag>` must not exist.
2. **Create the branch**: `git checkout -b autoresearch/<tag>` from current master.
3. **Read `train.py`**: the only file you edit — full GPT model, optimizer, training loop, dataloader, and eval in one self-contained file with inline UV dependencies.
4. **Ask for a results bucket**: HF Storage Bucket for best models and results (e.g. `hf://buckets/<username>/autoresearch-results`). Create if missing:
   ```bash
   hf buckets create <username>/autoresearch-results
   ```
5. **Initialize results.tsv**: create with just the header row.
6. **Check HF CLI**: run `hf --help`. If missing:
   ```bash
   curl -LsSf https://hf.co/cli/install.sh | bash
   ```
7. **Check login**: run `hf auth whoami`. If not logged in, tell the human to run `hf auth login`.

## Running on HF Jobs

Each experiment runs on a single GPU via HF Jobs:

```bash
hf jobs uv run \
    --flavor a100-large \
    --timeout 10m \
    --namespace mishig \
    -v hf://datasets/karpathy/climbmix-400b-shuffle:/data \
    -v hf://buckets/mishig/autoresearch-cache:/cache \
    train.py 2>&1 | tee run.log
```

- Dataset mounted read-only at `/data` (parquet shards)
- Tokenizer cached at `/cache/tokenizer`
- `train.py` auto-detects these paths

## Experiment rules

**Time budget**: fixed 5-minute wall-clock training time (excluding startup/compilation).

**You CAN**: modify `train.py` — architecture, optimizer, hyperparameters, training loop, batch size, model size.

**You CANNOT**: modify `evaluate_bpb`, the dataloader, tokenizer, or constants (`MAX_SEQ_LEN`, `TIME_BUDGET`, `EVAL_TOKENS`).

**Goal**: lowest `val_bpb`. Simpler is better — equal results with less code beats marginal improvement with added complexity.

**VRAM**: soft constraint. Meaningful gains justify modest increases; blowups do not.

## Output format

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

Extract key metric: `grep "^val_bpb:" run.log`

## Logging results

Log to `results.tsv` (tab-separated). Do not commit this file.

```
commit	val_bpb	memory_gb	status	paper	description
```

- `commit`: 7-char git hash
- `val_bpb`: achieved value (0.000000 for crashes)
- `memory_gb`: peak_vram_mb / 1024, rounded to .1f (0.0 for crashes)
- `status`: `keep`, `discard`, or `crash`
- `paper`: paper ID (e.g. `2501.12345`) or `-`
- `description`: short description

## Research with `hf papers`

```bash
hf papers search "efficient transformer training"
hf papers search "learning rate schedule"
hf papers read <paper_id>
```

Use papers as one source of ideas — novel combinations and original ideas are equally encouraged.

## Generation CLI

Three commands drive one generation:

### 1. `start` — bootstrap workspace and candidate plan

```bash
python generation.py start \
  --objective "Beat baseline val_bpb with simpler architecture" \
  --hypothesis "Reduce depth, increase width" \
  --hypothesis "Replace learned PE with RoPE" \
  --budget-tokens 100
```

Creates `lineage/gen_NNN/` with `genesis.md` and `candidates/plan.json`. Prints `generation=N` and paths.

### 2. `ratify` — select exactly one EPIC winner

After running experiments and writing evaluated candidates to a JSON file:

```bash
python generation.py ratify --candidates lineage/gen_NNN/candidates/evaluated.json
```

Reads a list of evaluated `Candidate` objects, selects the winner by utility ordering, writes `lineage/gen_NNN/epic/winner.json`.

### 3. `record` — commit EPIC to lineage

```bash
python generation.py record \
  --claim "RoPE replaces learned PE with no degradation and -200 params" \
  --artifact train.py \
  --do-more "positional encoding ablations" \
  --avoid "learned absolute PE"
```

Reads `winner.json` for the current generation, appends to `lineage/registry.json`, advances the seed artifact.

## Generation topology

- **Inner ring** (high-trust): Archivist, Theorist, Builder, Judge, Compressor
- **Outer ring** (disposable explorers): paper-led, ablation, architecture, optimizer, simplification, skeptic

Outer ring proposes candidates; inner ring selects one EPIC.

## Budget split (default)

- 10% inheritance + memory load
- 20% hypothesis generation
- 50% execution / evaluation
- 10% replication on finalists
- 10% compression + ratification

## Adoption rule

A candidate is ratifiable when all hold:

1. executable or operationally usable
2. validated on declared eval
3. strict improvement on ≥1 important axis vs inherited state
4. simple enough to preserve
5. compressible into reusable lineage memory

Tie-break order: correctness → improvement magnitude → robustness → simplicity → future leverage.

## Generation loop

LOOP FOREVER:

1. **Start**: `python generation.py start --objective ... --hypothesis ...`
2. **Research**: `hf papers search` for ideas; read 1-2 with `hf papers read <id>`
3. **Implement**: modify `train.py`
4. **Commit**: `git commit` the change
5. **Run**: submit HF Job, wait for completion
6. **Evaluate**: check `run.log`, extract `val_bpb` and `peak_vram_mb`
7. **Log**: record in `results.tsv`
8. **Ratify**: write `evaluated.json`, run `python generation.py ratify --candidates ...`
9. **Record**: `python generation.py record --claim ... --artifact train.py`
10. If improved: save best files to results bucket, update `README.md`, commit. Otherwise: `git reset` to previous commit.
11. Repeat from step 2 within this generation, or advance to next generation.

**On crashes**: fix trivial bugs (typo, missing import) and re-run. If the idea is fundamentally broken, log `crash` and move on.

**NEVER STOP**: once running, do not pause to ask whether to continue. The loop runs until manually interrupted.

## Failure semantics

A generation that cannot improve must still produce a failure EPIC:

- negative-result codex
- pruning rule for future search
- bug/failure taxonomy
- evaluator improvement preventing repeated waste

Failure EPICs are first-class lineage assets.

## Files

- `train.py`: the only file you edit
- `generation.py`: CLI (`start`, `ratify`, `record`)
- `lineage.py`: registry and generation state IO
- `swarm.py`: role assignment and candidate planning
- `ratify.py`: hard gate for exactly-one-EPIC selection
- `templates/epic.md.j2`: canonical EPIC record template
- `templates/generation_report.md.j2`: generation summary template
- `lineage/registry.json`: append-only lineage index
- `results.tsv`: experiment log (untracked)
