# `mockturtle_mig_opt`

Local optimizer for BLIF netlists using mockturtle MIG passes:

- convert BLIF -> `klut_network`
- resynthesize to `mig_network` (`mig_npn_resynthesis`)
- run recipe-selected optimization passes (`mig_resubstitution`, `mig_resubstitution2`,
  `mig_algebraic_depth_rewriting`) 
- run `cleanup_dangling` after each round

This mirrors the pass pattern used in mockturtle experiments/docs.

## Build

From the repository root:

```bash
cmake -S tools/mockturtle_mig_opt -B tools/mockturtle_mig_opt/build \
  -DCMAKE_BUILD_TYPE=Release
cmake --build tools/mockturtle_mig_opt/build -j
```

The build fetches the pinned Mockturtle revision recorded in `CMakeLists.txt`.

## Run

```bash
tools/mockturtle_mig_opt/build/mockturtle_mig_opt \
  --input artifacts/examples/n7/baseline/maj_baseline_strict_7.blif \
  --recipe resub_depth_resub2 \
  --rounds 3 \
  --max-pis 8 \
  --max-inserts 1
```

Optional output BLIF:

```bash
tools/mockturtle_mig_opt/build/mockturtle_mig_opt \
  --input in.blif \
  --output out_opt.blif \
  --rounds 4
```

Expected stdout format:

```text
RESULT klut_gates=<...> mig_before=<...> mig_after=<...> depth_before=<...> depth_after=<...> rounds=<...> max_pis=<...> max_inserts=<...> recipe=<...>
```

## Native BLIF equivalence check

The same build also creates `mockturtle_blif_cec`. It constructs a miter and
runs Mockturtle's native equivalence checker without a conflict limit:

```bash
tools/mockturtle_mig_opt/build/mockturtle_blif_cec \
  artifacts/examples/n7/baseline/maj_baseline_strict_7.blif \
  artifacts/examples/n7/folded_bias/maj_fb_7.blif
```

Only `RESULT=EQUIVALENT` is an equivalence proof. `RESULT=UNDECIDED` must not be
reported as a pass.
