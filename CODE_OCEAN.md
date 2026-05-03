# Code Ocean Capsule Notes

This repository includes `run.sh` for a Code Ocean compute capsule.

The runner executes the reviewer-facing reproducibility path from committed CSV
artifacts and copies generated outputs to `/results`, which is the directory
Code Ocean preserves after a run.

## Capsule Setup

Use a Python 3 base environment and install the Python dependencies from:

```text
requirements.txt
```

The run command is:

```bash
bash run.sh
```

## Scope

The capsule reproduces paper-level tables and figures from committed CSV files:

```bash
./reproduce_all_artifacts.sh
RUN_CROSS_TOOL_WLT=1 RUN_INTRO_MOTIVATION=1 ./reproduce_all_artifacts.sh
```

Full regeneration of tool-derived CSVs is documented in `REPRODUCIBILITY.md`.
Those stages require external EDA tools such as ABC, CirKit, Vivado, and the
mockturtle helper binary.  They are intentionally not enabled in the default
capsule path.
