#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

N_START="${N_START:-5}"
N_END="${N_END:-61}"

RUN_CORE_PACKAGE="${RUN_CORE_PACKAGE:-0}"

ABC_BIN="${ABC_BIN:-/home/mrunal/abc/abc}"
CIRKIT_PY="${CIRKIT_PY:-/home/mrunal/Mockturtle-mMIG-main/experiments-dac19-flow/.venv/bin/python}"
VIVADO_BIN="${VIVADO_BIN:-/tools/Xilinx/Vivado/2024.2/bin/vivado}"
FPGA_PART="${FPGA_PART:-xc7a100tcsg324-1}"
RUN_VIVADO="${RUN_VIVADO:-0}"

ASIC_LIB="${ASIC_LIB:-mcnc.genlib}"

RUN_CROSS_TOOL_WLT="${RUN_CROSS_TOOL_WLT:-0}"
RUN_INTRO_MOTIVATION="${RUN_INTRO_MOTIVATION:-0}"
INTRO_EXAMPLE_N="${INTRO_EXAMPLE_N:-}"

RUN_K_ADVANTAGE="${RUN_K_ADVANTAGE:-0}"
RUN_LARGE_N="${RUN_LARGE_N:-0}"
LARGE_N_VALUES="${LARGE_N_VALUES:-513,1025,2049,4097,5001}"

RUN_PACKAGE_ZIP="${RUN_PACKAGE_ZIP:-0}"

PAPER_DIR="results/paper_package_${N_START}_${N_END}"
VIVADO_CMP_DIR="results/vivado_compare_${N_START}_${N_END}_synth"
VIVADO_PAPER_DIR="results/vivado_paper_package_${N_START}_${N_END}"

log() {
  echo "[artifact] $*"
}

die() {
  echo "[error] $*" >&2
  exit 1
}

is_true() {
  case "${1,,}" in
    1|true|yes|y|on) return 0 ;;
    *) return 1 ;;
  esac
}

require_exec_file() {
  local path="$1"
  local label="$2"
  [[ -x "${path}" ]] || die "${label} is not executable: ${path}"
}

require_file() {
  local path="$1"
  [[ -f "${path}" ]] || die "Missing required file: ${path}"
}

choose_intro_n() {
  local start="$1"
  local end="$2"
  local requested="${3:-}"

  if [[ -n "${requested}" ]]; then
    if ! [[ "${requested}" =~ ^[0-9]+$ ]]; then
      die "INTRO_EXAMPLE_N must be an odd integer in [N_START, N_END]. Got: ${requested}"
    fi
    if (( requested < start || requested > end || requested % 2 == 0 )); then
      die "INTRO_EXAMPLE_N must be odd and within [N_START, N_END]. Got: ${requested}, range=[${start},${end}]"
    fi
    echo "${requested}"
    return
  fi

  if (( start <= 13 && 13 <= end )); then
    echo "13"
    return
  fi

  local cand="${start}"
  if (( cand % 2 == 0 )); then
    cand=$((cand + 1))
  fi
  if (( cand > end )); then
    die "Could not choose an odd INTRO_EXAMPLE_N within [${start},${end}]"
  fi
  echo "${cand}"
}

resolve_mock_bin() {
  python3 - <<'PY'
import final_generator as fg
print(fg._resolve_mockturtle_bin() or "")
PY
}

if ! [[ "${N_START}" =~ ^[0-9]+$ && "${N_END}" =~ ^[0-9]+$ ]]; then
  die "N_START and N_END must be integers. Got N_START=${N_START}, N_END=${N_END}"
fi
if (( N_START > N_END )); then
  die "N_START must be <= N_END"
fi
if (( N_START < 3 || N_END < 3 )); then
  die "N_START/N_END must be >= 3"
fi

command -v python3 >/dev/null 2>&1 || die "python3 not found in PATH"

if is_true "${RUN_CORE_PACKAGE}" || is_true "${RUN_LARGE_N}"; then
  require_exec_file "${ABC_BIN}" "ABC_BIN"
fi

if is_true "${RUN_CORE_PACKAGE}"; then
  require_exec_file "${CIRKIT_PY}" "CIRKIT_PY"
fi

if is_true "${RUN_VIVADO}"; then
  require_exec_file "${VIVADO_BIN}" "VIVADO_BIN"
fi

if is_true "${RUN_K_ADVANTAGE}" || is_true "${RUN_LARGE_N}"; then
  MOCK_BIN="$(resolve_mock_bin | tr -d '\n')"
  [[ -n "${MOCK_BIN}" ]] || die "mockturtle binary not found. Build tools/mockturtle_mig_opt first."
  require_exec_file "${MOCK_BIN}" "mockturtle binary"
fi

if is_true "${RUN_CORE_PACKAGE}"; then
  log "[1/8] Generating core paper package (raw/light + ABC + CirKit)..."
  python3 generate_paper_package.py \
    --n-start "${N_START}" \
    --n-end "${N_END}" \
    --abc-bin "${ABC_BIN}" \
    --cirkit-python "${CIRKIT_PY}"
else
  log "[1/8] Skipping core package rebuild (RUN_CORE_PACKAGE=${RUN_CORE_PACKAGE}); using existing CSV artifacts."
fi

if is_true "${RUN_VIVADO}"; then
  log "[2/8] Running Vivado synthesis comparison..."
  python3 compare_vivado_stats.py \
    --n-start "${N_START}" \
    --n-end "${N_END}" \
    --part "${FPGA_PART}" \
    --vivado-bin "${VIVADO_BIN}" \
    --synth-only \
    --output-dir "${VIVADO_CMP_DIR}"
else
  log "[2/8] Skipping Vivado rerun (RUN_VIVADO=${RUN_VIVADO}); expecting committed CSVs."
fi

if [[ ! -f "${VIVADO_CMP_DIR}/vivado_comparison.csv" ]]; then
  if is_true "${RUN_VIVADO}"; then
    die "Missing Vivado output after rerun: ${VIVADO_CMP_DIR}/vivado_comparison.csv"
  fi
  die "Missing ${VIVADO_CMP_DIR}/vivado_comparison.csv. Set RUN_VIVADO=1 to regenerate or use a range with committed Vivado CSVs."
fi

if [[ ! -f "${VIVADO_CMP_DIR}/vivado_detailed.csv" ]]; then
  if is_true "${RUN_VIVADO}"; then
    die "Missing Vivado output after rerun: ${VIVADO_CMP_DIR}/vivado_detailed.csv"
  fi
  die "Missing ${VIVADO_CMP_DIR}/vivado_detailed.csv. Set RUN_VIVADO=1 to regenerate or use a range with committed Vivado CSVs."
fi

log "[3/8] Generating Vivado paper package..."
python3 generate_vivado_paper_package.py \
  --comparison-csv "${VIVADO_CMP_DIR}/vivado_comparison.csv" \
  --detailed-csv "${VIVADO_CMP_DIR}/vivado_detailed.csv"

RAW_CSV="${PAPER_DIR}/data/raw_light_metrics_${N_START}_${N_END}.csv"
ABC_CSV="${PAPER_DIR}/data/abc_mapped_compare_${N_START}_${N_END}.csv"
CIRKIT_CSV="${PAPER_DIR}/data/cirkit_qca_stmg_compare_${N_START}_${N_END}.csv"
VIVADO_CSV="${VIVADO_PAPER_DIR}/data/vivado_comparison.csv"

if is_true "${RUN_CROSS_TOOL_WLT}" || is_true "${RUN_INTRO_MOTIVATION}"; then
  require_file "${RAW_CSV}"
fi
if is_true "${RUN_CROSS_TOOL_WLT}"; then
  require_file "${ABC_CSV}"
  require_file "${CIRKIT_CSV}"
  require_file "${VIVADO_CSV}"
  log "[4/8] Generating cross-tool WLT figures + LaTeX table..."
  python3 generate_cross_tool_wlt.py \
    --raw-csv "${RAW_CSV}" \
    --abc-csv "${ABC_CSV}" \
    --cirkit-csv "${CIRKIT_CSV}" \
    --vivado-csv "${VIVADO_CSV}" \
    --asic-lib "${ASIC_LIB}" \
    --out-fig-prefix "${PAPER_DIR}/figures/fig_cross_tool_wlt_summary" \
    --out-fig-grouped-prefix "${PAPER_DIR}/figures/fig_cross_tool_wlt_grouped" \
    --out-tex "${PAPER_DIR}/tables/table_cross_tool_wlt_summary.tex"
else
  log "[4/8] Skipping cross-tool WLT artifact generation (RUN_CROSS_TOOL_WLT=${RUN_CROSS_TOOL_WLT})."
fi

if is_true "${RUN_INTRO_MOTIVATION}"; then
  INTRO_N="$(choose_intro_n "${N_START}" "${N_END}" "${INTRO_EXAMPLE_N}")"
  log "[5/8] Generating introduction motivation artifact (n=${INTRO_N})..."
  python3 generate_intro_motivation_artifact.py \
    --raw-csv "${RAW_CSV}" \
    --example-n "${INTRO_N}" \
    --out-fig-prefix "${PAPER_DIR}/figures/fig_intro_motivation" \
    --out-tex "${PAPER_DIR}/tables/fig_intro_motivation.tex" \
    --out-intro-paragraph "${PAPER_DIR}/tables/intro_motivation_paragraph.tex" \
    --fig-rel-path-for-latex "${PAPER_DIR}/figures/fig_intro_motivation.pdf"
else
  log "[5/8] Skipping introduction motivation artifact (RUN_INTRO_MOTIVATION=${RUN_INTRO_MOTIVATION})."
fi

if is_true "${RUN_K_ADVANTAGE}"; then
  log "[6/8] Generating default-vs-k_advantage comparison CSV..."
  python3 compare_k_advantage_mode.py \
    --n-start "${N_START}" \
    --n-end "${N_END}" \
    --output "results/k_advantage_mode_compare_${N_START}_${N_END}.csv"
else
  log "[6/8] Skipping k_advantage ablation (RUN_K_ADVANTAGE=${RUN_K_ADVANTAGE})."
fi

if is_true "${RUN_LARGE_N}"; then
  log "[7/8] Generating large-n scalability CSV (${LARGE_N_VALUES})..."
  python3 compare_scalability_large_n_metrics.py \
    --n-values "${LARGE_N_VALUES}" \
    --output "results/scalability_large_n_metrics.csv" \
    --abc-bin "${ABC_BIN}"
else
  log "[7/8] Skipping large-n scalability (RUN_LARGE_N=${RUN_LARGE_N})."
fi

if is_true "${RUN_PACKAGE_ZIP}"; then
  if command -v zip >/dev/null 2>&1; then
    log "[8/8] Creating zip bundles..."
    zip -qr "results/paper_package_${N_START}_${N_END}.zip" "${PAPER_DIR}"
    zip -qr "results/vivado_paper_package_${N_START}_${N_END}.zip" "${VIVADO_PAPER_DIR}"
  else
    log "[8/8] zip not found; skipping zip bundle generation."
  fi
else
  log "[8/8] Skipping zip bundle generation (RUN_PACKAGE_ZIP=${RUN_PACKAGE_ZIP})."
fi

log "Done."
log "Core package:               ${PAPER_DIR}"
log "Vivado compare CSVs:        ${VIVADO_CMP_DIR}"
log "Vivado package:             ${VIVADO_PAPER_DIR}"
if is_true "${RUN_CROSS_TOOL_WLT}"; then
  log "Cross-tool WLT figure:      ${PAPER_DIR}/figures/fig_cross_tool_wlt_summary.pdf"
  log "Cross-tool grouped figure:  ${PAPER_DIR}/figures/fig_cross_tool_wlt_grouped.pdf"
fi
if is_true "${RUN_INTRO_MOTIVATION}"; then
  log "Intro motivation figure:    ${PAPER_DIR}/figures/fig_intro_motivation.pdf"
fi
if is_true "${RUN_K_ADVANTAGE}"; then
  log "K-advantage CSV:            results/k_advantage_mode_compare_${N_START}_${N_END}.csv"
fi
if is_true "${RUN_LARGE_N}"; then
  log "Large-n CSV:                results/scalability_large_n_metrics.csv"
fi
