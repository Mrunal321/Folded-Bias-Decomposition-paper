# v5.61 numerical archive

This archive preserves the raw numerical inputs used by the v5.61 comparison
package without republishing figures, manuscripts, logs, build trees, local
paths, or contributor contact details.

## Contents

- `raw-data/raw_light_metrics_5_61.csv`: structural and light-mapping metrics.
- `raw-data/abc_mapped_compare_5_61.csv`: ABC LUT6 and standard-cell proxy metrics.
- `raw-data/cirkit_qca_stmg_compare_5_61.csv`: CirKit QCA/STMG proxy metrics.
- `raw-data/vivado_comparison.csv` and `vivado_detailed.csv`: Vivado metrics.
- `*.py` and `reproduce_paper.sh`: the historical v5.61 analysis workflow,
  made portable by removing local executable-path fallbacks.
- `SHA256SUMS`: integrity checks for every archived script and CSV.

The five CSVs are byte-for-byte copies of the historical result data. The three
scripts that previously searched contributor-specific executable locations now
require a supplied path or a tool on `PATH`; their analysis logic is unchanged.

## Environment record

| Component | Recorded setting |
| --- | --- |
| Input sizes | odd (n = 5\ldots61) |
| FPGA target | `xc7a100tcsg324-1` |
| Vivado | 2024.2 |
| ABC | required; version was not recorded |
| CirKit | required; version was not recorded |
| Python | required; version was not recorded |

The missing version fields are intentionally marked unknown rather than
guessed. A future rerun should record `python --version`, `abc -c version`,
the CirKit package revision, and the Vivado build string alongside its outputs.

## Verify

```bash
cd archive/paper-results-v5.61
sha256sum --check SHA256SUMS
```
