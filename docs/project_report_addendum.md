# Project Report Addendum

## Solver Portability Update

The implementation now supports configurable solver backends through `SOLVER_BACKEND` in `src/config.py`. The default setting, `auto`, uses Gurobi when it is installed and licensed, while preserving a no-Gurobi path through SciPy's open-source MILP solver. This change makes the project easier to run on machines that do not have access to a Gurobi academic license and improves reproducibility for graders or teammates using a different Python environment.

The optimization formulation remains the same: binary arc variables determine whether a crew member moves from one flight-slot node to another, and continuous shift-start variables enforce the maximum shift duration. The fallback solver receives the same objective and constraints as the Gurobi model, translated into SciPy's sparse matrix MILP interface.

## Output and Visualization Update

The command-line output now includes the solver backend used for a run. A new `--viz` flag adds lightweight terminal charts after the normal route listing. These charts summarize crew counts by group, average flights per route, and the busiest origin-destination legs by crew coverage. The visuals are intentionally text-only so they can be used in terminal demos, saved output files, and report notes without requiring a plotting library.

Example command:

```bash
cd src
python main.py ../data/flight-schedules/F01-simple.csv --viz
```

## Suggested Report Language

To improve portability, we added a solver-selection layer around the core model. Gurobi remains the preferred backend when available, but the model can also be solved with SciPy's MILP implementation. This supports the same route-covering formulation while avoiding a hard dependency on a commercial solver license.

We also added a small command-line visualization mode. In addition to the detailed crew route output, the model can now print compact ASCII summaries of crew distribution, route utilization, and major airport flows. These summaries help interpret the raw assignment output and make it easier to compare schedules or parameter settings during experimentation.
