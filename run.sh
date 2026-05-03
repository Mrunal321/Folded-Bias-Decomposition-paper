#!/usr/bin/env bash
set -euo pipefail

# Code Ocean starts runs from /code and preserves only files written to
# /results.  This runner executes the reviewer-facing artifact checks from
# committed CSV data and copies the relevant generated outputs to /results.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

RESULTS_DIR="${CODEOCEAN_RESULTS_DIR:-/results}"
if [[ ! -d "${RESULTS_DIR}" ]]; then
  RESULTS_DIR="${ROOT_DIR}/code_ocean_results"
fi
mkdir -p "${RESULTS_DIR}"

if [[ ! -d .venv-codeocean ]]; then
  python3 -m venv .venv-codeocean
fi
# shellcheck disable=SC1091
source .venv-codeocean/bin/activate
python3 -m pip install -r requirements.txt

./reproduce_all_artifacts.sh
RUN_CROSS_TOOL_WLT=1 RUN_INTRO_MOTIVATION=1 ./reproduce_all_artifacts.sh

mkdir -p "${RESULTS_DIR}/paper_package_5_61/figures"
mkdir -p "${RESULTS_DIR}/paper_package_5_61/tables"
mkdir -p "${RESULTS_DIR}/vivado_paper_package_5_61"

cp -a results/paper_package_5_61/data "${RESULTS_DIR}/paper_package_5_61/"
cp -a results/paper_package_5_61/tables "${RESULTS_DIR}/paper_package_5_61/"
cp -a results/paper_package_5_61/figures/fig_cross_tool_wlt_summary.* "${RESULTS_DIR}/paper_package_5_61/figures/"
cp -a results/paper_package_5_61/figures/fig_cross_tool_wlt_grouped.* "${RESULTS_DIR}/paper_package_5_61/figures/"
cp -a results/paper_package_5_61/figures/fig_intro_motivation.* "${RESULTS_DIR}/paper_package_5_61/figures/"
cp -a results/vivado_paper_package_5_61/data "${RESULTS_DIR}/vivado_paper_package_5_61/"
cp -a results/vivado_paper_package_5_61/tables "${RESULTS_DIR}/vivado_paper_package_5_61/"
cp -a results/vivado_paper_package_5_61/figures "${RESULTS_DIR}/vivado_paper_package_5_61/"

cat > "${RESULTS_DIR}/README.txt" <<'EOF'
Folded-Bias Decomposition artifact results

This Code Ocean run executes the reviewer-facing reproducibility path from
committed CSV artifacts:

  ./reproduce_all_artifacts.sh
  RUN_CROSS_TOOL_WLT=1 RUN_INTRO_MOTIVATION=1 ./reproduce_all_artifacts.sh

Full regeneration from ABC, CirKit, Vivado, and mockturtle is documented in
REPRODUCIBILITY.md and requires those external EDA tools to be installed and
licensed outside the lightweight capsule path.
EOF

echo "Code Ocean artifact results written to ${RESULTS_DIR}"
