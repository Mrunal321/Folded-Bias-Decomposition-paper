# Folded-Bias Decomposition

This repository is the source-focused reproduction artifact for folded-bias
decomposition of odd-input majority and threshold functions. It generates two
technology-independent implementations:

- **FB:** the folded-bias carry-save-adder (CSA) construction; and
- **B:** the strict scaffolded HW-plus-threshold baseline used for the majority
  comparison. It embeds the odd-input function in the next `2^p-1` scaffold.

Generated measurements are written under an ignored build directory. The
current release tree intentionally contains code and a few inspectable netlist
examples, not manuscripts, figures, CSV dumps, or tool-generated result
packages.

## Quick start

Python 3.10 or newer is sufficient for the default run:

```bash
chmod +x reproduce_all_artifacts.sh
./reproduce_all_artifacts.sh
```

This generates B and FB Verilog/BLIF netlists for
`n = 5, 7, 9, 11, 13`, exhaustively checks both BLIFs against the majority
specification, and audits the public tree. External tools are disabled unless
requested. Outputs are placed under `build/reproduction/` and are not tracked.

Run the paper-size open profile with:

```bash
REPRO_PROFILE=paper ./reproduce_all_artifacts.sh
```

The profile covers all 29 odd sizes from 5 through 61 and the complete 218-case
general-threshold sweep over `n = 31, 63, 127`. The threshold protocol uses the
fixed seed `20260710`, 2,048 vectors per `n=31/63` case, and 4,096 per `n=127`
case. External mapped/formal threshold checks remain opt-in so this command
finishes predictably.

## Reproduce the portable experiment layers

ABC, Mockturtle, Fiction, and the scoped EPFL experiment are optional. Build the
pinned Mockturtle helpers once:

```bash
cmake -S tools/mockturtle_mig_opt -B tools/mockturtle_mig_opt/build \
  -DCMAKE_BUILD_TYPE=Release
cmake --build tools/mockturtle_mig_opt/build -j
```

With ABC, CMake, a C++ compiler, and Docker available, one wrapper invocation
runs the principal portable B/FB layers packaged here without committing their
outputs:

```bash
REPRO_PROFILE=paper \
RUN_ABC=1 \
RUN_MOCKTURTLE=1 \
RUN_EPFL_VOTER=1 \
RUN_EPFL_ABC=metrics \
RUN_FICTION=1 \
./reproduce_all_artifacts.sh
```

This includes fixed-recipe ABC/Mockturtle optimization, equivalence checking,
the pinned EPFL `voter` deterministic experiment and ABC metrics, and the
pinned Fiction v0.6.5 QCA-ONE/2DDWave flow. The EPFL source and Fiction image
are identified by immutable revisions and verified before use.

Enabling Mockturtle also lets the generator rank deterministic structural
variants across its four documented scoring recipes before the separate fixed
strong-flow recipe is applied.

### General-threshold mapped/formal extension

The paper profile performs all 218 deterministic checks without ABC by default.
Enable AIG/LUT6 metrics and unbounded pairwise CEC explicitly:

```bash
REPRO_PROFILE=paper \
RUN_ABC=1 \
RUN_THRESHOLD_ABC=1 \
ABC_BIN=/path/to/abc \
./reproduce_all_artifacts.sh
```

Some `n=127` CEC instances can take a long time. This opt-in command disables
ABC's internal CEC time limit; it is an extended formal run, not a reproduction
of the manuscript's bounded 169-pass/49-inconclusive ledger.

### Scoped EPFL `voter` experiment

Run the quantitative experiment without ABC:

```bash
RUN_EPFL_VOTER=1 ./reproduce_all_artifacts.sh
```

The runner downloads only the pinned 1001-input `voter.blif`, checks its
SHA-256, regenerates B and FB, and tests all three designs on exactly 1,144
vectors: 120 boundary-focused permutations and 1,024 seeded random vectors.
It also reports all 3,432 pairwise miter evaluations. This is deliberately a
single-benchmark integration experiment, not an evaluation of the complete
EPFL suite.

Optional modes are:

```bash
RUN_EPFL_VOTER=1 RUN_EPFL_ABC=metrics ABC_BIN=/path/to/abc \
  ./reproduce_all_artifacts.sh

RUN_EPFL_VOTER=1 RUN_EPFL_ABC=formal ABC_BIN=/path/to/abc \
  ./reproduce_all_artifacts.sh
```

`formal` uses `cec -n -T 0`; it may run for a long time. An undecided result is
recorded as undecided and is never presented as a pass. A hash-matching local
benchmark can be supplied through `EPFL_VOTER_SOURCE`.

### Fiction QCA-ONE flow

```bash
REPRO_PROFILE=paper RUN_ABC=1 RUN_FICTION=1 \
  ./reproduce_all_artifacts.sh
```

The runner uses an immutable Fiction container digest, the QCA-ONE cell
library, and 2DDWave clocking. It performs source-to-normalized ABC CEC,
mapping, orthogonal placement, design-rule checks, layout equivalence, cell
mapping, and area extraction. Logs, JSON, normalized BLIFs, and representative
QCADesigner layouts remain under ignored `build/`. Physical-layout work has a
per-design watchdog of 900 seconds by default (`FICTION_TIMEOUT`); the preceding
source-normalization CEC is intentionally unbounded.

## Repository layout

```text
reproduce_all_artifacts.sh       Main reproduction entry point
scripts/final_generator.py       Canonical B/FB Verilog and BLIF generator
scripts/generate_suite.py        Multi-size generation driver
scripts/verify_blif.py           Independent specification checker
scripts/run_threshold_sweep.py   General-threshold deterministic/ABC sweep
scripts/run_epfl_voter.py        Pinned, scoped EPFL voter experiment
scripts/run_fiction_qca.py       Pinned Fiction QCA-ONE flow
scripts/run_strong_flow.py       ABC/Mockturtle metrics and CEC driver
scripts/release_audit.py         Privacy and repository-content gate
rtl/fa.v                         Technology-independent full-adder primitive
artifacts/examples/              Representative n=7,31,61 Verilog/BLIF
tools/mockturtle_mig_opt/        Pinned Mockturtle helper source
docs/REPRODUCIBILITY.md          Detailed protocols and interpretation
```

## Generate another size

The majority input count must be odd and at least three:

```bash
python3 scripts/final_generator.py \
  --n 31 \
  --output-dir build/netlists/n31
```

Or run a custom suite:

```bash
N_VALUES=7,31,61 ./reproduce_all_artifacts.sh
```

The generated Verilog instantiates the portable `fa` module in `rtl/fa.v`.

## Experiment presets

The generator provides two deterministic structural-search presets:

```bash
EXPERIMENT_MODE=default ./reproduce_all_artifacts.sh
EXPERIMENT_MODE=k_advantage ./reproduce_all_artifacts.sh
```

`default` reproduces the structural-search configuration. `k_advantage`
disables the scaffold/folded-embedding sweeps and exposes the direct HW+K
architectural comparison.

## Interpretation and exclusions

The majority sweep's B circuit is the strict scaffolded baseline. The separate
general-threshold experiment compares FB with a direct CSA-plus-threshold
baseline; these are intentionally different experimental baselines.

Finite-vector testing is exact only when all input patterns are enumerated.
Formal CEC is counted as a pass only when the checker explicitly reports
equivalence. A timeout or undecided result is not a functional failure, but it
is also not a proof.

The current release tree does not redistribute manuscripts, rebuttals,
supplementary files, author biography/photo/contact material, local machine
paths, CSV result dumps, plots, synthesis logs, QCA layouts, Vivado projects,
compiled binaries, or tool build directories. Proprietary Vivado runs and
larger system-level/BNN experiments require their separate licensed
environments and are not silently claimed by the open profile. Historical
APC/sorting-network/prefix-baseline comparisons, standard-cell-library sweeps,
and benchmark timing tables are likewise not presented as outputs of this
compact B/FB workflow. The release audit covers the current tree or source
archive; it does not inspect or rewrite earlier Git commits.
