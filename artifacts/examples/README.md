# Representative generated netlists

These compact examples show the exact output format of the public generator at
three sizes. Each directory contains one Verilog bundle and separate canonical
BLIF files for the baseline and folded-bias constructions.

They were generated with the deterministic defaults:

```bash
python3 scripts/final_generator.py --n <N> \
  --output-dir artifacts/examples/n<N>
```

The Verilog bundles require the technology-independent `rtl/fa.v` primitive.
The examples are illustrative inputs for downstream tools; complete sweeps are
regenerated under the ignored `build/` directory.
