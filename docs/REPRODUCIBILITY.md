# Reproducibility Guide

This guide documents how to regenerate the committed paper artifacts.  The
default flow is lightweight: it uses CSV files already stored in the repository
and does not require commercial or specialized EDA tools.

## 1. Reviewer Check

From the repository root:

```bash
python3 -m pip install -r requirements.txt
chmod +x reproduce_all_artifacts.sh
./reproduce_all_artifacts.sh
```

Default switches:

- `RUN_CORE_PACKAGE=0`
- `RUN_VIVADO=0`
- `RUN_CROSS_TOOL_WLT=0`
- `RUN_INTRO_MOTIVATION=0`
- `RUN_PACKAGE_ZIP=0`

This command checks that the committed Vivado CSVs can be consumed and that the
paper-level Vivado tables/figures can be regenerated.

To also regenerate the cross-target W/T/L figure/table and the introduction
motivation figure from committed CSVs:

```bash
RUN_CROSS_TOOL_WLT=1 RUN_INTRO_MOTIVATION=1 ./reproduce_all_artifacts.sh
```

## 2. Full Regeneration

To regenerate tool-derived data, install the external tools and provide their
paths explicitly:

```bash
ABC_BIN=/path/to/abc \
CIRKIT_PY=/path/to/python-with-cirkit \
VIVADO_BIN=/path/to/vivado \
RUN_CORE_PACKAGE=1 \
RUN_VIVADO=1 \
RUN_CROSS_TOOL_WLT=1 \
RUN_INTRO_MOTIVATION=1 \
RUN_PACKAGE_ZIP=1 \
./reproduce_all_artifacts.sh
```

`RUN_CORE_PACKAGE=1` also requires the optional mockturtle helper to be built:

```bash
cmake -S tools/mockturtle_mig_opt -B tools/mockturtle_mig_opt/build
cmake --build tools/mockturtle_mig_opt/build -j
```

## 3. Environment Variables

Core range and tool paths:

- `N_START` (default: `5`)
- `N_END` (default: `61`)
- `ABC_BIN` (default: `abc`)
- `CIRKIT_PY` (default: `python3`; set to a Python executable with CirKit installed)
- `VIVADO_BIN` (default: `vivado`)
- `FPGA_PART` (default: `xc7a100tcsg324-1`)
- `ASIC_LIB` (default: `mcnc.genlib`)

Execution switches:

- `RUN_CORE_PACKAGE=0|1`
- `RUN_VIVADO=0|1`
- `RUN_CROSS_TOOL_WLT=0|1`
- `RUN_INTRO_MOTIVATION=0|1`
- `RUN_PACKAGE_ZIP=0|1`

## 4. Tool Requirements by Stage

- `RUN_CORE_PACKAGE=1` requires Python 3, ABC, CirKit, and the mockturtle helper.
- `RUN_VIVADO=1` requires Vivado.
- `RUN_CROSS_TOOL_WLT=1` and `RUN_INTRO_MOTIVATION=1` use committed CSVs and
  require only Python plus the packages in `requirements.txt`.

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

## 6. Common Failure Cases

- Missing `results/vivado_compare_<range>_synth/*.csv` with `RUN_VIVADO=0`:
  - Set `RUN_VIVADO=1`, or use a range with committed Vivado CSVs.
- Missing mockturtle helper with `RUN_CORE_PACKAGE=1`:
  - Build `tools/mockturtle_mig_opt` using the CMake commands above.
- Missing ABC/CirKit with `RUN_CORE_PACKAGE=1`:
  - Set `ABC_BIN` and `CIRKIT_PY` correctly, or leave `RUN_CORE_PACKAGE=0`.
- Missing Python plotting dependency:
  - Run `python3 -m pip install -r requirements.txt`.
