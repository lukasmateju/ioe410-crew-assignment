# Forensic Rebuild Plan

## Goal
Bring the project to a final state that:
1. Supports visualization outputs for schedules/routes.
2. Runs without Gurobi (with a fallback solver path).
3. Reintroduces higher-complexity modeling features that were reduced late in the project.

## Commit-History Forensics (Key Findings)

### 1) Most recent commits mostly changed README formatting
Recent commits at the tip (`91290ac`, `b9a129c`, `aee2bef`) are README-focused and do not reintroduce implementation features.

### 2) Full-model structure existed and is still mostly present in `sc_model.py`
Core features currently in the codebase include:
- Flight-slot expansion for multiple crew per flight.
- Separate pilot solves by aircraft type.
- Configurable same-start/end enforcement by crew type.
- Delay buffer and callout-rate preprocessing.

### 3) Utility/output complexity was reduced after `f41392f`
Compared with `f41392f`, current `src/utils.py` has a simpler output path:
- Earlier code had richer formatting helpers and archived run outputs (`tar.gz` with `results.txt`, `config.txt`).
- Current code writes plain text output only.

### 4) Hard dependency on Gurobi remains
`src/sc_model.py` directly imports and uses `gurobipy`, so execution fails in environments without Gurobi installed/licensed.

## Gap Analysis vs. Target End State

### A. Visualization readiness gap
- No actual charting/graph visualization module is implemented today.
- Existing output is textual route summaries only.

### B. No-Gurobi compatibility gap
- Solver calls and variable APIs are tightly coupled to Gurobi objects.
- No backend abstraction layer exists.

### C. Complexity restoration gap
- Some complexity is modeled but lacks robust packaging and toggles:
  - Optional deadhead policy integration is not controlled by `ALLOW_DEADHEADS`.
  - No optional advanced constraints module (breaks, min-hours balancing, fairness, etc.).
  - No experiment harness to compare baseline vs. advanced constraints.

## Proposed Implementation Sequence

## Phase 1 — Stabilize and decouple solver backend
1. Add a backend abstraction (`solver_backend.py`) with a common interface.
2. Keep Gurobi backend as primary when available.
3. Add open-source fallback backend:
   - Preferred: OR-Tools CP-SAT for binary-heavy model.
   - Alternate: PuLP/CBC if CP-SAT integration overhead is too high.
4. Add runtime selection logic:
   - `SOLVER_BACKEND = auto|gurobi|ortools|pulp` in config.
   - `auto` chooses Gurobi if import/license succeeds; otherwise fallback.

Deliverable: project runs end-to-end without Gurobi.

## Phase 2 — Rebuild visualization layer
1. Add `src/visualization.py`:
   - Route timeline (Gantt-like) by crew member.
   - Airport flow/leg counts (origin-destination aggregation).
2. Add save options in `main.py`:
   - `--save` for text output.
   - `--viz` to emit plots into `output/<run>/`.
3. Support static PNG + optional HTML interactive output.

Deliverable: reproducible visual artifacts suitable for reports.

## Phase 3 — Reintroduce advanced complexity (feature flags)
1. Add feature flags in `config.py`:
   - `ENABLE_BREAK_CONSTRAINTS`
   - `ENABLE_MIN_UTILIZATION`
   - `ENABLE_FAIRNESS_OBJECTIVE`
   - `ENABLE_DEADHEAD_ASSIGNMENT`
2. Implement each in modular functions in `sc_model.py` (or split into `constraints_*.py`).
3. Add scenario runner to compare crew count/runtime across datasets and flags.

Deliverable: complexity can be toggled on/off for demonstration and grading.

## Phase 4 — Documentation and README synchronization
1. Update README math notation to exactly match implementation variable names.
2. Add a “Solver Compatibility” section documenting no-Gurobi path.
3. Add a “Visualization” section with command examples and output samples.

Deliverable: README is mathematically clear and implementation-accurate.

## Resources Needed From Project Owner
1. Which fallback solver is preferred if performance differs (OR-Tools vs PuLP/CBC).
2. Required visualization format (static report figures, interactive dashboard, or both).
3. Top 2–3 “complexity” features to prioritize first.
4. Acceptance thresholds (runtime, optimality gap, required datasets).

## Immediate Next Build Step
Start Phase 1 by introducing solver backend selection and a non-Gurobi fallback while preserving current route/shift outputs.
