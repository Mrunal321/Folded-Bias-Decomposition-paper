TCAD Final Paper Data (n=5..61)

Folders:
- data/   : source CSVs used to generate tables/figures
- tables/ : LaTeX tables (ready to \input{})
- figures/: PDF+PNG figures (ready to \includegraphics{})

Key LaTeX tables to include in the main paper:
- tables/table_core_metrics_consolidated.tex   (9-column consolidated core table, includes MIG b/a, runtime in ms)
- tables/table_core_metrics_summary.tex        (aggregate summary: mean/median + W/T/L)

Other paper-ready tables (from your package):
- tables/table_lut6.tex
- tables/table_stdcell_*.tex
- tables/table_cirkit_qca_stmg.tex

Key figures to include in the main paper:
- figures/fig_fa_vs_n.pdf
- figures/fig_raw_klut_vs_n.pdf
- figures/fig_mig_after_vs_n.pdf
- figures/fig_depth_after_vs_n.pdf
- figures/fig_light_runtime_ms_vs_n.pdf
- figures/fig_abc_lut6_count_vs_n.pdf
- figures/fig_cirkit_inv_vs_n.pdf
- figures/fig_qca_delay_delta_vs_n.pdf (optional)
- figures/fig_stmg_delay_delta_vs_n.pdf (optional)

Composite figures included (if you prefer compact presentation):
- figures/fig_core_light.pdf
- figures/fig_lut6_deltas.pdf
- figures/fig_cirkit_deltas.pdf
- figures/fig_win_counts.pdf
