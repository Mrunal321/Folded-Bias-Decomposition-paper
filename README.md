# Folded-Bias Decomposition Artifact

This repository contains the implementation, scripts, and committed result
files used for the TCAD manuscript on folded-bias decomposition for
odd-input majority functions.

The main reproducibility entry point is:

```bash
./reproduce_all_artifacts.sh
```

The default command uses the committed CSV files and regenerates the
paper-level Vivado package without requiring ABC, CirKit, Vivado, or
mockturtle.  Tool-based regeneration can be enabled with environment
variables; see `REPRODUCIBILITY.md`.

## Quick Start

```bash
git clone https://github.com/Mrunal321/Folded-Bias-Decomposition-paper.git
cd Folded-Bias-Decomposition-paper

python3 -m pip install -r requirements.txt
chmod +x reproduce_all_artifacts.sh
./reproduce_all_artifacts.sh
```

Expected default outputs:

```text
results/vivado_paper_package_5_61/
results/paper_package_5_61/
```

To also regenerate the cross-target W/T/L figure/table and the introduction
motivation figure from committed CSVs:

```bash
RUN_CROSS_TOOL_WLT=1 RUN_INTRO_MOTIVATION=1 ./reproduce_all_artifacts.sh
```

## Repository Layout

```text
final_generator.py                  Core folded-bias and baseline generator
compare_raw_light_metrics.py        Raw structural and mockturtle-light metrics
compare_abc_mapped_metrics.py       ABC LUT6 and genlib mapping metrics
compare_cirkit_qca_stmg.py          CirKit QCA/STMG metric collection
compare_vivado_stats.py             Vivado synthesis comparison
generate_paper_package.py           Core CSV/table/figure package builder
generate_vivado_paper_package.py    Vivado table/figure package builder
generate_cross_tool_wlt.py          Cross-target W/T/L summary builder
generate_intro_motivation_artifact.py
                                    Introduction motivation figure builder
reproduce_all_artifacts.sh          Main wrapper script
results/                            Committed CSVs, tables, figures, and packages
```

## Generator

`final_generator.py` emits both Verilog and BLIF netlists for the two majority
implementations evaluated in the manuscript:

- `maj_fb_<n>`: folded-bias CSA construction.
- `maj_baseline_strict_<n>`: baseline CSA plus explicit threshold-comparator
  construction.

A direct run uses the parameters defined near the top of the file:

```bash
python3 final_generator.py
```

Important parameters:

| Name | Meaning |
|---|---|
| `N` | Odd majority input size. |
| `OUTPUT_DIR` | Directory for generated Verilog and BLIF files. |
| `INCLUDE_FOLDED_BIAS` | Emit folded-bias implementation. |
| `INCLUDE_BASELINE_STRICT` | Emit baseline strict implementation. |
| `MAJ_ONLY_FA` | Select MAJ/NOT-only full-adder expansion for BLIF output. |

The script prints FA counts, FA levels, threshold/bias parameters, and output
signal names for the constructed netlist.  The same scheduling logic is used for
Verilog and BLIF emission.

## Full Tool Regeneration

The committed results can be checked without external EDA tools.  To regenerate
the main tool-derived data, provide the tool paths and enable the corresponding
stages:

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

Large-`n` and mockturtle-based ablations are optional and require the
mockturtle helper binary under `tools/mockturtle_mig_opt/`:

```bash
RUN_LARGE_N=1 ./reproduce_all_artifacts.sh
```

See `REPRODUCIBILITY.md` for the full list of switches and output files.
