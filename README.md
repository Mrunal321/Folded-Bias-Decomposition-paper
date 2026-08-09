# Folded-Bias Decomposition

Reproducibility artifact for folded-bias (FB) and strict scaffolded
HW-plus-threshold baseline (B) implementations of odd-input majority and
threshold functions.

The active workflow generates technology-independent Verilog and BLIF
netlists, checks their behavior, and leaves all generated outputs in ignored
`build/` directories. It does not redistribute manuscripts, personal
material, proprietary tool projects, or tool-generated bulk outputs.

## Run the core checks

Python 3.10+ is sufficient:

```bash
./reproduce_all_artifacts.sh
```

This quick profile generates (n = 5, 7, 9, 11, 13) and exhaustively verifies
each generated B and FB BLIF against majority.

For the full open profile:

```bash
REPRO_PROFILE=paper ./reproduce_all_artifacts.sh
```

It covers all odd (n) from 5 through 61 plus 218 deterministic
general-threshold cases at (n = 31, 63, 127). Majority checks are exhaustive
through (n=13); larger sizes use the documented boundary-weight and seeded
vector tests.

## Optional tool flows

Build the pinned Mockturtle helpers:

```bash
cmake -S tools/mockturtle_mig_opt -B tools/mockturtle_mig_opt/build -DCMAKE_BUILD_TYPE=Release
cmake --build tools/mockturtle_mig_opt/build -j
```

Then enable the portable external flows explicitly:

```bash
REPRO_PROFILE=paper RUN_ABC=1 RUN_MOCKTURTLE=1 RUN_EPFL_VOTER=1 \
RUN_EPFL_ABC=metrics RUN_FICTION=1 ./reproduce_all_artifacts.sh
```

ABC, Mockturtle, the scoped EPFL `voter` experiment, and Fiction are separate
opt-in layers. Vivado and broader system-level experiments require their own
licensed environments and are not reproduced by this command.

## What is checked

| Layer | Default result |
| --- | --- |
| B/FB netlist generation | Deterministic |
| Majority behavior, (n \le 13) | Exhaustive |
| Majority behavior, (n > 13) | Deterministic finite vectors |
| General thresholds, paper profile | 218 deterministic cases |
| ABC, Mockturtle, EPFL, Fiction | Opt-in |

A functional proof requires exhaustive enumeration or an explicit formal CEC
equivalence result. A finite-vector pass is regression evidence, not a proof.

## Archived numerical results

[`archive/paper-results-v5.61/`](archive/paper-results-v5.61/) contains the
sanitized v5.61 numerical-result archive: five raw CSVs, portable historical
analysis scripts, known tool/environment details, and SHA-256 checksums. It is
the reference bundle for matching the archived tables; it is separate from the
current compact workflow.

## Layout

```text
reproduce_all_artifacts.sh  main entry point
scripts/                    generator, verifier, and optional-flow runners
rtl/fa.v                    full-adder primitive
artifacts/examples/         checked representative netlists
docs/REPRODUCIBILITY.md     protocol and configuration details
archive/paper-results-v5.61 sanitized historical numerical archive
```

For exact options, output schemas, and limitations, see
[`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md).
