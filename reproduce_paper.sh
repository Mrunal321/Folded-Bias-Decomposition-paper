#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

N_START="${N_START:-5}"
N_END="${N_END:-61}"

ABC_BIN="${ABC_BIN:-/home/mrunal/abc/abc}"
CIRKIT_PY="${CIRKIT_PY:-/home/mrunal/Mockturtle-mMIG-main/experiments-dac19-flow/.venv/bin/python}"
VIVADO_BIN="${VIVADO_BIN:-/tools/Xilinx/Vivado/2024.2/bin/vivado}"
FPGA_PART="${FPGA_PART:-xc7a100tcsg324-1}"
RUN_VIVADO="${RUN_VIVADO:-1}"
ASIC_LIB="${ASIC_LIB:-mcnc.genlib}"

PAPER_DIR="results/paper_package_${N_START}_${N_END}"
VIVADO_CMP_DIR="results/vivado_compare_${N_START}_${N_END}_synth"
VIVADO_PAPER_DIR="results/vivado_paper_package_${N_START}_${N_END}"

echo "[1/4] Generating core paper package (raw/light + ABC + CirKit)..."
python3 generate_paper_package.py \
  --n-start "${N_START}" \
  --n-end "${N_END}" \
  --abc-bin "${ABC_BIN}" \
  --cirkit-python "${CIRKIT_PY}"

if [[ "${RUN_VIVADO}" == "1" ]]; then
  echo "[2/4] Running Vivado synthesis comparison..."
  python3 compare_vivado_stats.py \
    --n-start "${N_START}" \
    --n-end "${N_END}" \
    --part "${FPGA_PART}" \
    --vivado-bin "${VIVADO_BIN}" \
    --synth-only \
    --output-dir "${VIVADO_CMP_DIR}"
else
  echo "[2/4] Skipping Vivado rerun (RUN_VIVADO=${RUN_VIVADO})."
fi

echo "[3/4] Generating Vivado paper package from CSV..."
python3 generate_vivado_paper_package.py \
  --comparison-csv "${VIVADO_CMP_DIR}/vivado_comparison.csv" \
  --detailed-csv "${VIVADO_CMP_DIR}/vivado_detailed.csv"

echo "[4/4] Generating cross-tool WLT summary..."
python3 generate_cross_tool_wlt.py \
  --raw-csv "${PAPER_DIR}/data/raw_light_metrics_${N_START}_${N_END}.csv" \
  --abc-csv "${PAPER_DIR}/data/abc_mapped_compare_${N_START}_${N_END}.csv" \
  --cirkit-csv "${PAPER_DIR}/data/cirkit_qca_stmg_compare_${N_START}_${N_END}.csv" \
  --vivado-csv "${VIVADO_PAPER_DIR}/data/vivado_comparison.csv" \
  --asic-lib "${ASIC_LIB}" \
  --out-fig-prefix "${PAPER_DIR}/figures/fig_cross_tool_wlt_summary" \
  --out-tex "${PAPER_DIR}/tables/table_cross_tool_wlt_summary.tex"

echo "Done."
echo "Core package:   ${PAPER_DIR}"
echo "Vivado package: ${VIVADO_PAPER_DIR}"
