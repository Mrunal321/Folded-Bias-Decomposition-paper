# `mockturtle_mig_opt`

Local optimizer for BLIF netlists using mockturtle MIG passes:

- convert BLIF -> `klut_network`
- resynthesize to `mig_network` (`mig_npn_resynthesis`)
- run recipe-selected optimization passes (`mig_resubstitution`, `mig_resubstitution2`,
  `mig_algebraic_depth_rewriting`) 
- run `cleanup_dangling` after each round

This mirrors the pass pattern used in mockturtle experiments/docs.

## Build

```bash
cd tools/mockturtle_mig_opt
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

## Run

```bash
./build/mockturtle_mig_opt \
  --input ../../results/baseline_threshold/maj_baseline_strict_7.blif \
  --recipe resub_depth_resub2 \
  --rounds 3 \
  --max-pis 8 \
  --max-inserts 1
```

Optional output BLIF:

```bash
./build/mockturtle_mig_opt \
  --input in.blif \
  --output out_opt.blif \
  --rounds 4
```

Expected stdout format:

```text
RESULT klut_gates=<...> mig_before=<...> mig_after=<...> depth_before=<...> depth_after=<...> rounds=<...> max_pis=<...> max_inserts=<...> recipe=<...>
```
