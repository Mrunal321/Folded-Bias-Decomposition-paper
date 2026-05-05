# Folded-Bias Decomposition Artifact

This repository contains the implementation, committed data, and reproduction
scripts for the TCAD manuscript on folded-bias decomposition for odd-input
majority functions.

The main entry point is intentionally kept at the repository root:

```bash
./reproduce_all_artifacts.sh
```

The default command uses committed CSV artifacts and does not require ABC,
CirKit, Vivado, or mockturtle.  It regenerates the paper-level Vivado package
from the committed Vivado CSVs.

## Quick Start

```bash
git clone https://github.com/Mrunal321/Folded-Bias-Decomposition-paper.git
cd Folded-Bias-Decomposition-paper

python3 -m pip install -r requirements.txt
chmod +x reproduce_all_artifacts.sh
./reproduce_all_artifacts.sh
```

To also regenerate the cross-target W/T/L figure/table and the introduction
motivation figure from committed CSVs:

```bash
RUN_CROSS_TOOL_WLT=1 RUN_INTRO_MOTIVATION=1 ./reproduce_all_artifacts.sh
```

## Layout

```text
reproduce_all_artifacts.sh       Main reproduction wrapper
requirements.txt                 Python plotting dependency
scripts/                         Python generators and comparison scripts
tools/mockturtle_mig_opt/        Source for the optional mockturtle helper
artifacts/netlists/              Committed generated BLIF/Verilog/testbench files
results/                         Committed CSVs, paper tables, and figures
docs/REPRODUCIBILITY.md          Detailed reproduction notes
```

## Generator

The core generator is `scripts/final_generator.py`.  It emits Verilog and BLIF
netlists for:

- `maj_fb_<n>`: folded-bias CSA construction.
- `maj_baseline_strict_<n>`: baseline CSA plus explicit threshold-comparator
  construction.

Run it directly for the configured `N` value:

```bash
python3 scripts/final_generator.py
```

The script prints FA counts, FA levels, threshold/bias parameters, and output
signal names for the constructed netlist.  The same scheduling logic is used for
Verilog and BLIF emission.

## Full Tool Regeneration

The committed results can be checked without external EDA tools.  To regenerate
the tool-derived data, install the external tools and provide their paths:

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

See `docs/REPRODUCIBILITY.md` for the full switch list and expected outputs.
