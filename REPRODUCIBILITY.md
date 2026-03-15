# Reproducibility Guide (Paper Artifacts)

## 1. One-Command Entry Point

Use the wrapper:

```bash
chmod +x reproduce_all_artifacts.sh
./reproduce_all_artifacts.sh
```

Default behavior is conservative/reviewer-friendly:

- `RUN_CORE_PACKAGE=0`
- `RUN_VIVADO=0`
- `RUN_CROSS_TOOL_WLT=0`
- `RUN_INTRO_MOTIVATION=0`
- `RUN_LARGE_N=0`
- `RUN_PACKAGE_ZIP=0`

So by default it does not require ABC/CirKit/Vivado/mockturtle.

## 2. Full Regeneration (Author Mode)

To regenerate all major paper artifacts from tools:

```bash
RUN_CORE_PACKAGE=1 \
RUN_VIVADO=1 \
RUN_CROSS_TOOL_WLT=1 \
RUN_INTRO_MOTIVATION=1 \
RUN_LARGE_N=1 \
RUN_PACKAGE_ZIP=1 \
./reproduce_all_artifacts.sh
```

## 3. Environment Variables

Core range and tool paths:

- `N_START` (default: `5`)
- `N_END` (default: `61`)
- `ABC_BIN` (default: `/home/mrunal/abc/abc`)
- `CIRKIT_PY` (default: `/home/mrunal/Mockturtle-mMIG-main/experiments-dac19-flow/.venv/bin/python`)
- `VIVADO_BIN` (default: `/tools/Xilinx/Vivado/2024.2/bin/vivado`)
- `FPGA_PART` (default: `xc7a100tcsg324-1`)
- `ASIC_LIB` (default: `mcnc.genlib`)
- `LARGE_N_VALUES` (default: `513,1025,2049,4097,5001`)

Execution switches:

- `RUN_CORE_PACKAGE=0|1`
- `RUN_VIVADO=0|1`
- `RUN_CROSS_TOOL_WLT=0|1`
- `RUN_INTRO_MOTIVATION=0|1`
- `RUN_LARGE_N=0|1`
- `RUN_PACKAGE_ZIP=0|1`

## 4. Tool Requirements by Stage

- `RUN_CORE_PACKAGE=1` requires:
  - Python 3
  - ABC (`ABC_BIN`)
  - CirKit python env (`CIRKIT_PY`)
- `RUN_VIVADO=1` requires:
  - Vivado (`VIVADO_BIN`)
- `RUN_LARGE_N=1` requires:
  - mockturtle binary
  - ABC (`ABC_BIN`)

## 5. Expected Outputs

Main output roots:

- `results/paper_package_<N_START>_<N_END>/`
- `results/vivado_compare_<N_START>_<N_END>_synth/`
- `results/vivado_paper_package_<N_START>_<N_END>/`

Optional outputs when enabled:

- Cross-tool WLT figure/table:
  - `results/paper_package_<...>/figures/fig_cross_tool_wlt_summary.*`
  - `results/paper_package_<...>/figures/fig_cross_tool_wlt_grouped.*`
  - `results/paper_package_<...>/tables/table_cross_tool_wlt_summary.tex`
- Intro motivation artifact:
  - `results/paper_package_<...>/figures/fig_intro_motivation.*`
  - `results/paper_package_<...>/tables/fig_intro_motivation.tex`
  - `results/paper_package_<...>/tables/intro_motivation_paragraph.tex`
- Large-n scalability CSV:
  - `results/scalability_large_n_metrics.csv`

## 6. Common Failure Cases

- Missing `results/vivado_compare_<range>_synth/*.csv` with `RUN_VIVADO=0`:
  - Fix: set `RUN_VIVADO=1`, or use a range with committed Vivado CSVs.
- Missing mockturtle when enabling `RUN_K_ADVANTAGE` or `RUN_LARGE_N`:
  - Fix: build `tools/mockturtle_mig_opt` and ensure resolver can find the binary.
- Missing ABC/CirKit when `RUN_CORE_PACKAGE=1`:
  - Fix: set `ABC_BIN`/`CIRKIT_PY` correctly or disable core rebuild.

## 7. Minimal Reviewer Command (No External EDA Tools)

```bash
RUN_CORE_PACKAGE=0 \
RUN_VIVADO=0 \
RUN_CROSS_TOOL_WLT=0 \
RUN_INTRO_MOTIVATION=0 \
RUN_LARGE_N=0 \
RUN_PACKAGE_ZIP=0 \
./reproduce_all_artifacts.sh
```
