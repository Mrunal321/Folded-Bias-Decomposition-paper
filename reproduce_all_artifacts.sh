#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${REPO_ROOT}"

REPRO_PROFILE="${REPRO_PROFILE:-quick}"       # quick | paper
case "${REPRO_PROFILE}" in
  quick)
    N_VALUES="${N_VALUES:-5,7,9,11,13}"
    RUN_THRESHOLDS="${RUN_THRESHOLDS:-0}"
    ;;
  paper)
    N_VALUES="${N_VALUES:-5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35,37,39,41,43,45,47,49,51,53,55,57,59,61}"
    RUN_THRESHOLDS="${RUN_THRESHOLDS:-1}"
    ;;
  *) echo "REPRO_PROFILE must be quick or paper" >&2; exit 2 ;;
esac

OUTPUT_ROOT="${OUTPUT_ROOT:-build/reproduction/netlists}"
SCHEDULE="${SCHEDULE:-dadda}"
EXPERIMENT_MODE="${EXPERIMENT_MODE:-default}"
FA_ENCODING="${FA_ENCODING:-majority}"
SELF_CHECK_MAX_N="${SELF_CHECK_MAX_N:-13}"

RUN_ABC="${RUN_ABC:-0}"                    # auto | 0 | 1
RUN_THRESHOLD_ABC="${RUN_THRESHOLD_ABC:-0}" # 0 | 1 (218-case mapped/formal extension)
RUN_MOCKTURTLE="${RUN_MOCKTURTLE:-0}"     # 0 | 1
RUN_EPFL_VOTER="${RUN_EPFL_VOTER:-0}"      # 0 | 1
RUN_EPFL_ABC="${RUN_EPFL_ABC:-0}"          # 0 | metrics | formal
RUN_FICTION="${RUN_FICTION:-0}"            # 0 | 1
THRESHOLD_N_VALUES="${THRESHOLD_N_VALUES:-31,63,127}"
THRESHOLD_VECTORS="${THRESHOLD_VECTORS:-paper}"
ABC_BIN="${ABC_BIN:-abc}"
DOCKER_BIN="${DOCKER_BIN:-docker}"
FICTION_IMAGE="${FICTION_IMAGE:-mawalter/fiction@sha256:c93abd35f49078d637414ce58bc03834298911ed704ec8edd960f1f76214c396}"
FICTION_EXPORT_LAYOUT_N="${FICTION_EXPORT_LAYOUT_N:-5,31,61}"
FICTION_TIMEOUT="${FICTION_TIMEOUT:-900}"
EPFL_VOTER_SOURCE="${EPFL_VOTER_SOURCE:-}"
MOCKTURTLE_BIN="${MOCKTURTLE_BIN:-tools/mockturtle_mig_opt/build/mockturtle_mig_opt}"
MOCKTURTLE_CEC_BIN="${MOCKTURTLE_CEC_BIN:-tools/mockturtle_mig_opt/build/mockturtle_blif_cec}"

case "${RUN_ABC}" in
  auto|0|1) ;;
  *) echo "RUN_ABC must be auto, 0, or 1" >&2; exit 2 ;;
esac
case "${RUN_MOCKTURTLE}" in
  0|1) ;;
  *) echo "RUN_MOCKTURTLE must be 0 or 1" >&2; exit 2 ;;
esac
case "${RUN_THRESHOLD_ABC}" in
  0|1) ;;
  *) echo "RUN_THRESHOLD_ABC must be 0 or 1" >&2; exit 2 ;;
esac
case "${RUN_THRESHOLDS}" in
  0|1) ;;
  *) echo "RUN_THRESHOLDS must be 0 or 1" >&2; exit 2 ;;
esac
case "${RUN_FICTION}" in
  0|1) ;;
  *) echo "RUN_FICTION must be 0 or 1" >&2; exit 2 ;;
esac
case "${RUN_EPFL_VOTER}" in
  0|1) ;;
  *) echo "RUN_EPFL_VOTER must be 0 or 1" >&2; exit 2 ;;
esac
case "${RUN_EPFL_ABC}" in
  0|metrics|formal) ;;
  *) echo "RUN_EPFL_ABC must be 0, metrics, or formal" >&2; exit 2 ;;
esac

echo "[1/7] Generating baseline and folded-bias netlists"
generate_args=(
  --n-values "${N_VALUES}"
  --output-root "${OUTPUT_ROOT}"
  --schedule "${SCHEDULE}"
  --experiment-mode "${EXPERIMENT_MODE}"
  --fa-encoding "${FA_ENCODING}"
  --self-check-max-n "${SELF_CHECK_MAX_N}"
)
if [[ "${RUN_MOCKTURTLE}" == "1" ]]; then
  generate_args+=(--mockturtle-scoring --mockturtle-bin "${MOCKTURTLE_BIN}")
fi
python3 scripts/generate_suite.py "${generate_args[@]}"

echo "[2/7] Independently checking generated BLIF behavior"
python3 scripts/verify_blif.py \
  --n-values "${N_VALUES}" \
  --input-root "${OUTPUT_ROOT}" \
  --exhaustive-max-n "${SELF_CHECK_MAX_N}"

echo "[3/7] General-threshold sweep"
if [[ "${RUN_THRESHOLDS}" == "1" ]]; then
  threshold_args=(
    --n-values "${THRESHOLD_N_VALUES}"
    --vectors "${THRESHOLD_VECTORS}"
  )
  if [[ "${RUN_THRESHOLD_ABC}" == "1" ]]; then
    threshold_args+=(--abc-bin "${ABC_BIN}" --require-abc)
  else
    threshold_args+=(--abc-bin "")
  fi
  python3 scripts/run_threshold_sweep.py "${threshold_args[@]}"
else
  echo "[threshold] skipped (set RUN_THRESHOLDS=1 to enable)"
fi

echo "[4/7] Optional scoped EPFL voter experiment"
if [[ "${RUN_EPFL_VOTER}" == "1" ]]; then
  epfl_args=()
  if [[ -n "${EPFL_VOTER_SOURCE}" ]]; then
    epfl_args+=(--epfl-source "${EPFL_VOTER_SOURCE}")
  fi
  case "${RUN_EPFL_ABC}" in
    0)
      epfl_args+=(--abc-bin "")
      ;;
    metrics)
      epfl_args+=(--abc-bin "${ABC_BIN}" --skip-formal)
      ;;
    formal)
      epfl_args+=(--abc-bin "${ABC_BIN}")
      ;;
  esac
  python3 scripts/run_epfl_voter.py "${epfl_args[@]}"
else
  echo "[epfl-voter] skipped (set RUN_EPFL_VOTER=1 to enable)"
fi

echo "[5/7] Optional pinned Fiction QCA flow"
if [[ "${RUN_FICTION}" == "1" ]]; then
  python3 scripts/run_fiction_qca.py \
    --n-values "${N_VALUES}" \
    --input-root "${OUTPUT_ROOT}" \
    --abc-bin "${ABC_BIN}" \
    --docker-bin "${DOCKER_BIN}" \
    --image "${FICTION_IMAGE}" \
    --export-layout-n "${FICTION_EXPORT_LAYOUT_N}" \
    --timeout "${FICTION_TIMEOUT}"
else
  echo "[fiction] skipped (set RUN_FICTION=1 with the paper profile to enable)"
fi

echo "[6/7] Running available strong-flow checks"
strong_args=(
  --n-values "${N_VALUES}"
  --input-root "${OUTPUT_ROOT}"
)
if [[ "${RUN_ABC}" == "0" ]]; then
  strong_args+=(--abc-bin "")
else
  strong_args+=(--abc-bin "${ABC_BIN}")
fi
if [[ "${RUN_ABC}" == "1" ]]; then
  strong_args+=(--require-abc)
fi
if [[ "${RUN_MOCKTURTLE}" == "1" ]]; then
  strong_args+=(
    --mockturtle-bin "${MOCKTURTLE_BIN}"
    --mockturtle-cec-bin "${MOCKTURTLE_CEC_BIN}"
    --require-mockturtle
    --require-mockturtle-cec
  )
else
  strong_args+=(--mockturtle-bin "" --mockturtle-cec-bin "")
fi
python3 scripts/run_strong_flow.py "${strong_args[@]}"

echo "[7/7] Auditing the public release tree"
python3 scripts/release_audit.py

echo "Reproduction completed successfully."
echo "Generated files are under build/reproduction/ and are intentionally untracked."
