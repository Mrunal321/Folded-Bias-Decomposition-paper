# Vivado Paper Package Summary

Interpretation:
- Every delta column is `baseline - folded`.
- For min-cost metrics (LUT/delay/levels/power/runtime), positive delta means folded is better.
- For WNS (max-better), negative delta means folded is better.

## Win/Tie/Loss

| Metric | Better | Folded wins | Ties | Baseline wins | Mean delta (B-F) |
|---|---:|---:|---:|---:|---:|
| CLB LUTs | min | 14 | 9 | 6 | 1.482759 |
| Datapath delay (ns) | min | 12 | 4 | 13 | 0.029483 |
| Logic levels | min | 5 | 23 | 1 | 0.137931 |
| WNS (ns) | max | 12 | 4 | 13 | -0.029483 |
| Total power (W) | min | 3 | 26 | 0 | 0.000103 |
| Runtime (s) | min | 9 | 0 | 20 | -0.070768 |

## Composite (ADP)

- Folded wins: 18
- Ties: 4
- Baseline wins: 7
- Mean ADP improvement: 4.8324%
- Median ADP improvement: 4.1207%

## Pareto (LUT, Delay)

- Folded dominates: 9
- Baseline dominates: 5
- Exact ties: 4
- Tradeoff points: 11
