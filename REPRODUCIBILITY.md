# Reproducibility Guide (Paper Artifacts)

This file defines exactly what to keep in git so reviewers can reproduce the
results used in the manuscript.

## 1. What To Commit

Commit these source scripts:

- `final_generator.py`
- `compare_raw_light_metrics.py`
- `compare_abc_mapped_metrics.py`
- `compare_cirkit_qca_stmg.py`
- `compare_vivado_stats.py`
- `generate_paper_package.py`
- `generate_vivado_paper_package.py`
- `generate_cross_tool_wlt.py`
- `RUN_ALL_COMPARISONS.mf`
- `reproduce_paper.sh`
- `REPRODUCIBILITY.md`

Commit these paper-facing artifacts (for the exact manuscript version):

- `results/paper_package_5_61/data/*.csv`
- `results/paper_package_5_61/tables/*.tex`
- `results/paper_package_5_61/figures/*.pdf`
- `results/paper_package_5_61/figures/*.png`
- `results/paper_package_5_61/SUMMARY.md`

- `results/vivado_compare_5_61_synth/vivado_comparison.csv`
- `results/vivado_compare_5_61_synth/vivado_detailed.csv`

- `results/vivado_paper_package_5_61/data/*.csv`
- `results/vivado_paper_package_5_61/tables/*.tex`
- `results/vivado_paper_package_5_61/figures/*.pdf`
- `results/vivado_paper_package_5_61/figures/*.png`
- `results/vivado_paper_package_5_61/SUMMARY.md`

Do **not** commit large transient directories:

- `results/vivado_compare_5_61_synth/runs/` (per-run Vivado logs/reports; huge)
- `__pycache__/`
- `.Xil/`

## 2. Environment Required

- Python 3
- ABC binary
- CirKit Python env (for QCA/STMG script)
- Vivado (only if regenerating FPGA CSVs)

Paths can be overridden with environment variables in `reproduce_paper.sh`.

## 3. One-Command Reproduction

From repo root:

```bash
chmod +x reproduce_paper.sh
./reproduce_paper.sh
```

Defaults:

- `N_START=5`, `N_END=61`
- ASIC panel library for cross-tool plot: `mcnc.genlib`
- Runs Vivado synthesis flow (`RUN_VIVADO=1`)

Skip Vivado rerun (use existing CSVs):

```bash
RUN_VIVADO=0 ./reproduce_paper.sh
```

## 4. Reviewer-Friendly Claim Scope

When describing reproducibility in the paper:

- Core logic + mapping + cross-tool figures are fully script-reproducible.
- Vivado per-case implementation logs are optional and can be omitted from git.
- Published FPGA tables/figures are reproducible from committed Vivado CSVs.

