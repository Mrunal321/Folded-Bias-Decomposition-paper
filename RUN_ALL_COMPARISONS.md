Folded-Bias vs Baseline STRICT: Full Repro Guide
=================================================

Project root used below:
/home/mrunal/Folded_Bias-Decomposition

What this guide covers
----------------------
1) Raw + light metrics (FA counts/levels + mockturtle light pass)
2) ABC mapped metrics (LUT6 + std-cell proxy genlib mapping)
3) CirKit device metrics (QCA + STMG)
4) Exact meaning of delta columns


------------------------------------------------------------
0. Prerequisites (full checks)
------------------------------------------------------------

Run from terminal:

cd /home/mrunal/Folded_Bias-Decomposition

python3 --version
/home/mrunal/abc/abc -h

If mockturtle scorer is needed:
test -x /home/mrunal/Folded_Bias-Decomposition/tools/mockturtle_mig_opt/build/mockturtle_mig_opt && echo "mockturtle binary OK"

If CirKit QCA/STMG is needed:
/home/mrunal/Mockturtle-mMIG-main/experiments-dac19-flow/.venv/bin/python -c "import cirkit; print('cirkit OK')"


------------------------------------------------------------
1. Raw + Light Optimization Metrics (n=5..51)
------------------------------------------------------------

Command:

cd /home/mrunal/Folded_Bias-Decomposition
/usr/bin/python3 /home/mrunal/Folded_Bias-Decomposition/compare_raw_light_metrics.py \
  --n-start 5 \
  --n-end 51 \
  --output /home/mrunal/Folded_Bias-Decomposition/results/raw_light_metrics_5_51.csv

Output file:
/home/mrunal/Folded_Bias-Decomposition/results/raw_light_metrics_5_51.csv

What it contains:
- folded_fa_count, folded_fa_levels
- baseline_fa_count, baseline_fa_levels
- folded_raw_klut_gates, baseline_raw_klut_gates
- folded_raw_runtime_s, baseline_raw_runtime_s
- folded_light_mig_after, folded_light_depth_after
- folded_light_runtime_s, baseline_light_runtime_s
- baseline_light_mig_after, baseline_light_depth_after
- deltas (baseline - folded)
  - delta_raw_runtime_s_baseline_minus_folded
  - delta_light_runtime_s_baseline_minus_folded


------------------------------------------------------------
2. ABC Mapping Metrics (LUT6 + Std-Cell Proxy)
------------------------------------------------------------

Command:

cd /home/mrunal/Folded_Bias-Decomposition
/usr/bin/python3 /home/mrunal/Folded_Bias-Decomposition/compare_abc_mapped_metrics.py \
  --n-start 5 \
  --n-end 51 \
  --abc-bin /home/mrunal/abc/abc \
  --output /home/mrunal/Folded_Bias-Decomposition/results/abc_mapped_compare_5_51.csv

Output file:
/home/mrunal/Folded_Bias-Decomposition/results/abc_mapped_compare_5_51.csv

Compact reshaped summary (already generated once):
/home/mrunal/Folded_Bias-Decomposition/results/abc_mapped_summary_5_51.csv

Important note:
- This script auto-prefers std-cell libs containing: stmg/qca/bioth.
- If none are found, it falls back to available proxies (sky130/asap7/mcnc).

Force specific genlib files manually (full command example):

cd /home/mrunal/Folded_Bias-Decomposition
/usr/bin/python3 /home/mrunal/Folded_Bias-Decomposition/compare_abc_mapped_metrics.py \
  --n-start 5 \
  --n-end 51 \
  --abc-bin /home/mrunal/abc/abc \
  --std-lib /home/mrunal/mockturtle/experiments/cell_libraries/sky130.genlib \
  --std-lib /home/mrunal/mockturtle/experiments/cell_libraries/asap7.genlib \
  --std-lib /home/mrunal/mockturtle/experiments/cell_libraries/mcnc.genlib \
  --output /home/mrunal/Folded_Bias-Decomposition/results/abc_mapped_compare_5_51.csv


------------------------------------------------------------
3. CirKit Device Metrics (QCA + STMG)
------------------------------------------------------------

Use the CirKit environment that supports migcost QCA/STMG:
/home/mrunal/Mockturtle-mMIG-main/experiments-dac19-flow/.venv/bin/python

Command:

cd /home/mrunal/Folded_Bias-Decomposition
/home/mrunal/Mockturtle-mMIG-main/experiments-dac19-flow/.venv/bin/python \
  /home/mrunal/Folded_Bias-Decomposition/compare_cirkit_qca_stmg.py \
  --n-start 5 \
  --n-end 51 \
  --abc-bin /home/mrunal/abc/abc \
  --output /home/mrunal/Folded_Bias-Decomposition/results/cirkit_qca_stmg_compare_5_51.csv

Output file:
/home/mrunal/Folded_Bias-Decomposition/results/cirkit_qca_stmg_compare_5_51.csv

What it does internally:
- Build folded and baseline netlists from final_generator
- Emit BLIF
- Convert BLIF to AIGER using ABC
- Read AIGER into CirKit MIG store
- Collect:
  qca_area, qca_delay, qca_energy
  stmg_area, stmg_delay, stmg_energy
  gates, depth


------------------------------------------------------------
4. Delta Interpretation (VERY IMPORTANT)
------------------------------------------------------------

In all comparison CSVs here:

delta_* = baseline - folded

Interpretation:
- delta > 0  => folded is better (lower value)
- delta < 0  => baseline is better
- delta = 0  => tie

Examples:
- delta_area_baseline_minus_folded = +12
  means baseline area is 12 units larger -> folded wins by 12.
- delta_delay_baseline_minus_folded = -0.03
  means baseline delay is 0.03 lower -> baseline wins on delay.


------------------------------------------------------------
5. Quick sanity print commands
------------------------------------------------------------

Show first rows of each CSV:

cd /home/mrunal/Folded_Bias-Decomposition
sed -n '1,20p' /home/mrunal/Folded_Bias-Decomposition/results/raw_light_metrics_5_51.csv
sed -n '1,20p' /home/mrunal/Folded_Bias-Decomposition/results/abc_mapped_compare_5_51.csv
sed -n '1,20p' /home/mrunal/Folded_Bias-Decomposition/results/cirkit_qca_stmg_compare_5_51.csv

Count rows:

cd /home/mrunal/Folded_Bias-Decomposition
python3 - <<'PY'
import csv
for p in [
    '/home/mrunal/Folded_Bias-Decomposition/results/raw_light_metrics_5_51.csv',
    '/home/mrunal/Folded_Bias-Decomposition/results/abc_mapped_compare_5_51.csv',
    '/home/mrunal/Folded_Bias-Decomposition/results/cirkit_qca_stmg_compare_5_51.csv',
]:
    with open(p) as f:
        n=sum(1 for _ in csv.reader(f))-1
    print(p, 'rows=', n)
PY


------------------------------------------------------------
6. One-command re-run block (copy-paste all)
------------------------------------------------------------

cd /home/mrunal/Folded_Bias-Decomposition && \
/usr/bin/python3 /home/mrunal/Folded_Bias-Decomposition/compare_raw_light_metrics.py \
  --n-start 5 --n-end 51 \
  --output /home/mrunal/Folded_Bias-Decomposition/results/raw_light_metrics_5_51.csv && \
/usr/bin/python3 /home/mrunal/Folded_Bias-Decomposition/compare_abc_mapped_metrics.py \
  --n-start 5 --n-end 51 \
  --abc-bin /home/mrunal/abc/abc \
  --output /home/mrunal/Folded_Bias-Decomposition/results/abc_mapped_compare_5_51.csv && \
/home/mrunal/Mockturtle-mMIG-main/experiments-dac19-flow/.venv/bin/python \
  /home/mrunal/Folded_Bias-Decomposition/compare_cirkit_qca_stmg.py \
  --n-start 5 --n-end 51 \
  --abc-bin /home/mrunal/abc/abc \
  --output /home/mrunal/Folded_Bias-Decomposition/results/cirkit_qca_stmg_compare_5_51.csv


------------------------------------------------------------
7. Full Paper Package (tables + figures + all CSVs)
------------------------------------------------------------

This single script runs all three pipelines and generates:
- data CSVs
- IEEE-ready figures (PNG + PDF)
- LaTeX tables for Overleaf
- summary markdown

Example for n=5..61:

cd /home/mrunal/Folded_Bias-Decomposition
/usr/bin/python3 /home/mrunal/Folded_Bias-Decomposition/generate_paper_package.py \
  --n-start 5 \
  --n-end 61 \
  --abc-bin /home/mrunal/abc/abc \
  --cirkit-python /home/mrunal/Mockturtle-mMIG-main/experiments-dac19-flow/.venv/bin/python

Default output folder for this run:
/home/mrunal/Folded_Bias-Decomposition/results/paper_package_5_61

Expected contents:
- results/paper_package_5_61/data/*.csv
- results/paper_package_5_61/tables/*.tex
- results/paper_package_5_61/figures/*.png + *.pdf
- results/paper_package_5_61/SUMMARY.md


------------------------------------------------------------
8. Vivado FPGA Metrics (latest run flow)
------------------------------------------------------------

Purpose:
- Collect synthesis-based FPGA metrics for folded vs baseline:
  runtime, LUT/FF/CARRY, timing (WNS/datapath delay/logic levels), power.

Validated Vivado binary on this machine:
/tools/Xilinx/Vivado/2024.2/bin/vivado

Command (n=5..51, synth-only):

cd /home/mrunal/Folded_Bias-Decomposition
/usr/bin/python3 /home/mrunal/Folded_Bias-Decomposition/compare_vivado_stats.py \
  --n-start 5 \
  --n-end 51 \
  --part xc7a100tcsg324-1 \
  --vivado-bin /tools/Xilinx/Vivado/2024.2/bin/vivado \
  --synth-only \
  --output-dir /home/mrunal/Folded_Bias-Decomposition/results/vivado_compare_5_51_synth

Output files:
- /home/mrunal/Folded_Bias-Decomposition/results/vivado_compare_5_51_synth/vivado_detailed.csv
- /home/mrunal/Folded_Bias-Decomposition/results/vivado_compare_5_51_synth/vivado_comparison.csv
- per-design reports/logs under:
  /home/mrunal/Folded_Bias-Decomposition/results/vivado_compare_5_51_synth/runs

Delta convention in vivado_comparison.csv:
- delta_* = baseline - folded
- positive => folded better for "smaller-is-better" metrics (LUTs, delay, power, runtime)

Quick check:

cd /home/mrunal/Folded_Bias-Decomposition
sed -n '1,20p' /home/mrunal/Folded_Bias-Decomposition/results/vivado_compare_5_51_synth/vivado_comparison.csv


------------------------------------------------------------
9. Vivado Paper-Ready Tables + Figures (from existing CSVs)
------------------------------------------------------------

This does NOT rerun Vivado. It uses existing:
- vivado_comparison.csv
- vivado_detailed.csv

Command example (n=5..61 already available):

cd /home/mrunal/Folded_Bias-Decomposition
/usr/bin/python3 /home/mrunal/Folded_Bias-Decomposition/generate_vivado_paper_package.py \
  --comparison-csv /home/mrunal/Folded_Bias-Decomposition/results/vivado_compare_5_61_synth/vivado_comparison.csv \
  --detailed-csv /home/mrunal/Folded_Bias-Decomposition/results/vivado_compare_5_61_synth/vivado_detailed.csv

Default output:
- /home/mrunal/Folded_Bias-Decomposition/results/vivado_paper_package_5_61

Generated contents:
- data/vivado_comparison.csv
- data/vivado_detailed.csv
- tables/table_vivado_area_delay.tex
- tables/table_vivado_timing_runtime.tex
- tables/table_vivado_summary.tex
- figures/fig_vivado_area_delay_curves.(png|pdf)
- figures/fig_vivado_timing_power_runtime_curves.(png|pdf)
- figures/fig_vivado_delta_trends.(png|pdf)
- figures/fig_vivado_win_tie_loss.(png|pdf)
- SUMMARY.md
