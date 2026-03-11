# Repository Guide (Structure & File Map)

This README is for navigating the repository (what each folder/file does).  
Project motivation, methodology, and results are documented in the paper in the repo root.

---

## Top-level

- **Evaluating Leakage–Performance Tradeoffs in Encrypted Databases_ An Experimental Study of Path ORAM and SEAL.pdf**  
  Draft research paper (methods, experiments, results, discussion).

- **figures/**  
  Final plots that were actually used in the paper (selected from experiment outputs).

- **configs/**  
  JSON experiment configurations used by the master runner (includes lighter/dev variants).

- **src/**  
  All implementation code: Path ORAM, SEAL, attacks, experiment framework, plotting.

- **tests/**  
  Correctness tests (Path ORAM/SEAL) + experiment-layer smoke tests.

- **out/** *(generated output; usually not committed)*  
  Experiment outputs produced by runners (results + plots + config snapshots).

- **requirements.txt**  
  Python dependencies for the project (e.g., numpy, matplotlib).

> Note: run logs like `dev_run.log` / `full_seed*.log` are local artifacts and are not part of the repository.

---

## src/ (main code)

### src/path_oram/ — Path ORAM core implementation
- **types.py**  
  Core datatypes: Block, Bucket, dummy block helpers.
- **utils.py**  
  Tree/path utilities (leaf labels, path nodes, power-of-two helpers).
- **server.py**  
  “Dumb server” bucket tree storage with `read_path()` / `write_path()` and counters.
- **client.py**  
  Path ORAM client logic: position map, stash, `access()` (read/write), eviction/write-back.
- **metrics.py**  
  Helper functions for performance accounting (e.g., bandwidth estimate).

### src/seal/ — SEAL wrapper (controlled leakage via α)
- **partitioning.py**  
  Computes SEAL parameters (`2^α` partitions, local ORAM size, bit widths).
- **prp.py**  
  Conceptual PRP used for deterministic routing (global ID → permuted ID).
- **seal_client.py**  
  SEAL wrapper: creates sub-ORAMs, maps global IDs → `(oram_index, local_id)`, routes accesses, logs per-access stats.

### src/attacks/ — Leakage-abuse attacks + padding utility
- **types.py**  
  Data containers for leakage observations and attack outputs.
- **query_recovery.py**  
  Query recovery attack (QRSR) using response volume.
- **database_recovery.py**  
  Database recovery attack (DRSR) using volume + leaked α-bit identifiers.
- **padding.py**  
  Power-of-x padding function (used by oracle/experiments).

### src/workload/ — Synthetic dataset + leakage oracles
- **synthetic.py**  
  Synthetic dataset generator (Zipf-like) + inverted index construction.
- **leakage_oracle.py**  
  SEAL leakage oracle for query-based experiments (volume + α-prefix list per query).
- **path_oram_oracle.py**  
  Baseline “no useful leakage” oracle used for Path ORAM comparisons in query-style attack experiments.

### src/eval/ — Experiment runners + plotting
- **master_runner.py**  
  Main entry point: runs experiment groups from a config file and writes outputs to `out/<run_name>/`.
- **perf_runner.py**  
  Performance experiments: Path ORAM vs SEAL runtime/bandwidth proxy under block-ID access patterns.
- **workloads.py**  
  Query workload generators (uniform / zipf-like / hot-set).
- **phase3_runner.py**  
  Attack evaluation over time using checkpoints (QRSR/DRSR vs observations).
- **padding_eval.py**  
  Padding sweep evaluation (security impact + padding overhead).
- **sessions.py**  
  Session sampler for session-reset experiments (many short sessions).
- **session_eval.py**  
  Runs attacks per session, resets attacker state between sessions, aggregates mean/std.
- **plotting.py**  
  Shared plotting utilities.
- **io_utils.py**  
  Output helpers (write CSV/JSON, create directories).
- **replot_*.py** *(optional utilities)*  
  Scripts that regenerate plots from saved `out/<run>/results/*` without rerunning experiments.

---

## tests/ (correctness + smoke tests)

Typical tests include:
- Path ORAM correctness + invariants (small n)
- SEAL correctness across α values
- Attack sanity tests (QRSR/DRSR in valid range)
- Workload/oracle/over-time/session pipeline smoke tests

Run tests as modules from repo root, e.g.:
- `python -m tests.test_invariants`
- `python -m tests.test_seal_multi_alpha`

---

## configs/ (experiment configurations)

Config JSON files define:
- dataset parameters (n, distribution settings)
- α sweep values
- padding x sweep values
- workload pattern selection
- checkpoint lists
- session lengths + session counts
- toggles to enable/disable experiment groups

---

## out/ (generated experiment outputs)

Each run directory typically contains:
- **config_snapshot.json** — exact config used for the run
- **results/** — CSV/JSON result files
- **plots/** — generated PNG plots

These outputs are used to populate `figures/` and support the paper’s results.

---

## figures/ (paper-ready figures)

Curated set of plots included in the paper (copied/renamed from `out/.../plots/`).

---

## Quick usage notes

- Install deps (recommended via venv), then run experiments through the master runner:
  - `python -m src.eval.master_runner`
- Plot regeneration utilities (`replot_*.py`) can recreate plots from saved results without rerunning experiments.
