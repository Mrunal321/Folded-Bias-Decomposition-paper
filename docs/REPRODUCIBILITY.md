# Reproducibility guide

## Root workflow

Run from the repository root:

```bash
./reproduce_all_artifacts.sh
```

The wrapper has seven ordered stages:

1. Generate canonical B and FB Verilog/BLIF netlists.
2. Independently evaluate the generated BLIFs against the majority specification.
3. Optionally run the general-threshold sweep.
4. Optionally run the scoped EPFL `voter` experiment.
5. Optionally run the pinned Fiction QCA-ONE physical-design flow.
6. Run the available ABC/Mockturtle optimization and CEC checks.
7. Audit the public source tree for private paths and generated bulk data.

The default `quick` profile uses `n = 5,7,9,11,13`. Every input pattern is
enumerated at these sizes. For larger majority designs, the independent checker
uses 12 shuffled vectors at each of seven boundary-relevant Hamming weights plus
1,024 pseudorandom vectors from seed `0x7CAD+n` (1,108 vectors total).

The `paper` profile expands the majority sweep to every odd `n` from 5 through
61 and enables all 218 finite general-threshold cases:

```bash
REPRO_PROFILE=paper ./reproduce_all_artifacts.sh
```

## Configuration

The wrapper accepts the following environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `REPRO_PROFILE` | `quick` | `quick` or paper-size `paper` profile |
| `N_VALUES` | profile-dependent | Odd majority sizes to generate |
| `OUTPUT_ROOT` | `build/reproduction/netlists` | Generated majority-netlist root |
| `SCHEDULE` | `dadda` | `serial`, `wallace`, or `dadda` CSA scheduling |
| `EXPERIMENT_MODE` | `default` | `default` or `k_advantage` structural-search preset |
| `FA_ENCODING` | `majority` | `majority` or `xor` BLIF full-adder encoding |
| `SELF_CHECK_MAX_N` | `13` | Largest exhaustively checked majority size |
| `RUN_ABC` | `0` | Strong-flow ABC mode: `0`, auto-detected `auto`, or required `1` |
| `ABC_BIN` | `abc` | ABC executable name or path |
| `RUN_MOCKTURTLE` | `0` | Enable the pinned optimizer and native CEC helper |
| `MOCKTURTLE_BIN` | local build path | Mockturtle optimizer helper |
| `MOCKTURTLE_CEC_BIN` | local build path | Native Mockturtle BLIF CEC helper |
| `RUN_THRESHOLDS` | profile-dependent | Enable the general-threshold sweep |
| `THRESHOLD_N_VALUES` | `31,63,127` | General-threshold input sizes |
| `THRESHOLD_VECTORS` | `paper` | Paper vector policy or a fixed positive count |
| `RUN_THRESHOLD_ABC` | `0` | Enable mapped metrics and unbounded CEC for all threshold cases |
| `RUN_EPFL_VOTER` | `0` | Enable the pinned EPFL `voter` experiment |
| `RUN_EPFL_ABC` | `0` | EPFL ABC mode: `0`, `metrics`, or `formal` |
| `EPFL_VOTER_SOURCE` | empty | Optional local source that must match the pinned hash |
| `RUN_FICTION` | `0` | Enable the pinned Fiction/QCA-ONE Docker stage |
| `DOCKER_BIN` | `docker` | Docker-compatible executable for Fiction |
| `FICTION_IMAGE` | pinned digest | Immutable Fiction v0.6.5 image |
| `FICTION_EXPORT_LAYOUT_N` | `5,31,61` | Sizes for ignored QCADesigner layout exports |
| `FICTION_TIMEOUT` | `900` | Physical-layout watchdog in seconds per design |

Executable paths are supplied by the user or resolved from `PATH`. They are not
written into tracked sources or JSON reports.

## Output contract

A run creates only ignored outputs:

```text
build/reproduction/
  generation_manifest.json
  verification.json
  strong_flow.json
  threshold_sweep.json                 (when enabled)
  netlists/
    n<N>/
      maj<N>_generated_canon.v
      baseline/maj_baseline_strict_<N>.blif
      folded_bias/maj_fb_<N>.blif
  strong_flow/optimized/               (when an optimizer is available)
  epfl_voter/voter.json                (when enabled)
  fiction_qca/fiction_qca.json         (when enabled)
```

Reports contain parameters, relative artifact paths, hashes, vector counts,
metrics, and checker results. They do not contain host names, user names, or
absolute machine paths. The final audit also works in a GitHub source archive,
where no `.git` directory is present. It examines the current release tree or
source archive, not prior Git commits.

## Majority specification checking

For `n <= SELF_CHECK_MAX_N`, the independent Python BLIF evaluator enumerates
all `2^n` vectors. That is an exact functional check. For larger `n`, it applies
the documented boundary-heavy and seeded vector set. A vector passes only when
both B and FB equal

```text
sum(x[0:n]) >= ceil(n/2).
```

The evaluator is independent of the generator and evaluates `.names` cubes in
topological order. Its bit-parallel implementation changes performance, not the
Boolean semantics.

## General-threshold protocol

This experiment covers every `2 <= T <= n` for `n = 31,63,127`, giving
30 + 62 + 126 = 218 cases. It compares folded bias with a direct
CSA-plus-threshold implementation. This direct threshold baseline is distinct
from the scaffolded B architecture used in the majority-size sweep.

The default `paper` vector policy uses seed `20260710` and exactly:

- 2,048 vectors for each `n=31` and `n=63` case; and
- 4,096 vectors for each `n=127` case.

Each report contains per-case `w`, `K`, popcount of `K`, carry-only validity,
near-power-of-two classification, FA count, structural depth, and regional
aggregate deltas. A threshold is in the near-power category when it lies within
one of either adjacent power of two. Enable AIG/LUT6
metrics and pairwise ABC CEC with:

```bash
REPRO_PROFILE=paper RUN_ABC=1 RUN_THRESHOLD_ABC=1 \
  ABC_BIN=/path/to/abc ./reproduce_all_artifacts.sh
```

This uses `cec -n -T 0`, so ABC has no internal runtime limit and matches I/O by
order. It can take a long
time on some 127-input cases. The command is intentionally described as an
extended unbounded run; it does not recreate the manuscript's bounded
169-pass/49-inconclusive accounting.

## ABC and Mockturtle strong flows

ABC applies `strash`, three fixed resyn2-style command rounds, and `if -K 6`.
The exact expanded recipe and canonical ABC version line are written to the
JSON report. CEC uses `-T 0`, disabling ABC's default internal limit.

The Mockturtle helper is fetched at the exact commit recorded in
`tools/mockturtle_mig_opt/CMakeLists.txt`. Build both helper executables with:

```bash
cmake -S tools/mockturtle_mig_opt -B tools/mockturtle_mig_opt/build \
  -DCMAKE_BUILD_TYPE=Release
cmake --build tools/mockturtle_mig_opt/build -j
```

Then run:

```bash
REPRO_PROFILE=paper RUN_ABC=1 RUN_MOCKTURTLE=1 \
  ./reproduce_all_artifacts.sh
```

`RUN_MOCKTURTLE=1` has two distinct roles. During generation it ranks
deterministic candidate structures across `resub`, `resub2`, `depth_resub2`,
and `resub_depth_resub2`. In the later strong-flow stage it applies only the
fixed recipe below to the selected B/FB inputs.

The optimizer recipe is `resub_depth_resub2`, with six rounds, `max_pis=8`,
and `max_inserts=1`. The native checker constructs a BLIF miter and uses
`conflict_limit=0`. When the corresponding optimizer/checker is enabled, each
optimized BLIF is regenerated beneath `build/` and checked against its source.
With both tool flows over all 29 sizes, the post-optimization scope is
29 sizes x 2 methods x 3 outputs = 174 CEC checks.

The same run also performs 29 ABC and 29 native Mockturtle B-versus-FB checks.
Those 58 pairwise checks are reported separately and are not part of the
historical 261-check ledger.

The compact public flow does not label those 174 checks as the entire historical
261-check ledger. That ledger also counted 29 behavioral-specification versus
direct-reference and 58 behavioral-specification versus method-input checks.
Here, input behavior is instead covered by the independent specification tests
described above; these are exhaustive through `n=13` and finite beyond it.

## Scoped EPFL `voter`

The runner downloads `random_control/voter.blif` from an immutable EPFL
benchmark commit and rejects any source whose SHA-256 differs. A local
hash-matching copy can be supplied with `EPFL_VOTER_SOURCE`.

It regenerates the 1001-input B and FB implementations and evaluates the EPFL,
B, and FB designs on exactly 1,144 vectors:

- 12 permutations at each weight in
  `{0,1,2,499,500,501,502,999,1000,1001}` (120 vectors); and
- 1,024 pseudorandom vectors from seed `0x7CAD`.

A specification-test pass means 1,144/1,144 matches for each design and zero
mismatches in 3,432 pairwise miter evaluations. It is quantitative regression
evidence, not exhaustive or formal proof.

```bash
RUN_EPFL_VOTER=1 ./reproduce_all_artifacts.sh
RUN_EPFL_VOTER=1 RUN_EPFL_ABC=metrics ABC_BIN=/path/to/abc \
  ./reproduce_all_artifacts.sh
```

`RUN_EPFL_ABC=formal` adds `cec -n -T 0` for all three pairs. Because the
networks are structurally dissimilar and have 1,001 inputs, the checker may run
for a long time or remain undecided. Only explicit equivalence is a formal pass.
The scope is this threshold benchmark alone, not unrelated EPFL circuits.

## Fiction QCA-ONE

The Fiction stage is opt-in because it requires Docker. It validates that the
pinned image reports Fiction v0.6.5, then applies the same three-round ABC
normalization to each B/FB source. Source-to-normalized CEC uses `-T 0` with no
outer process watchdog. Physical-layout commands retain a configurable
wall-clock timeout. The default is 900 seconds for each of 58 paper-profile
designs, so the complete physical sweep can be lengthy even though typical
small cases finish much sooner.

For each design, the runner performs AND/OR/INV mapping, orthogonal placement,
design-rule checking, layout equivalence, QCA-ONE cell mapping, and area
extraction under 2DDWave clocking:

```bash
REPRO_PROFILE=paper RUN_ABC=1 RUN_FICTION=1 \
  ./reproduce_all_artifacts.sh
```

A case passes only when required metrics are present, the design-rule checker
reports zero violations and zero warnings, layout equivalence is weak or
strong, and every requested layout file is actually exported. The reported
critical path is in clock zones; the flow does not claim calibrated device
delay or power.

## Equivalence terminology

For a pairwise checker, both circuits receive corresponding primary inputs and
their outputs feed an XOR miter. If any input can make that XOR equal one, the
circuits differ. An explicit `equivalent`/UNSAT result proves that no such input
exists. `not_equivalent` is a disproof. `undecided` means no conclusion and is
never counted as a pass. `tool_error` means the checker itself failed and makes
a requested formal run fail.

Seeded deterministic specification testing is different: “pass” means zero
observed mismatches over the stated number of vectors. It becomes an exact
proof only when the input space is exhaustively enumerated.

## Continuous integration and scope boundary

CI runs both the `quick` and `paper` Python profiles with external tools
disabled. It therefore checks generation, exhaustive/seeded specification
testing, all 218 deterministic threshold cases, checksums, and the release
audit. CI green does not by itself certify ABC, Mockturtle, Fiction, EPFL
network download, Vivado, or other external environments.

The current release tree deliberately excludes manuscripts, supplementary and
rebuttal files, figures, CSV/result dumps, logs, QCA layouts, Vivado projects,
compiled binaries, author biography/photo/contact material, and local machine
paths. Vivado and larger system-level/BNN experiments require separate licensed
or experiment-specific environments and are not claimed by the default open
profile. The compact workflow also does not claim to regenerate the historical
APC, sorting-network, CSA-prefix, standard-cell-library, or timing-table
campaigns. Its covered layers are the B/FB generator, majority specification
tests, 218-case threshold protocol, strong ABC/Mockturtle paths, scoped EPFL
voter, and modern Fiction/QCA flow.
