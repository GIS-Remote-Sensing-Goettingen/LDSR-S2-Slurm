#!/usr/bin/env bash

set -euo pipefail

MANIFEST_PATH="${1:?manifest path required}"
PYTHON_BIN="${LDSRS2_PYTHON:-python}"

if [[ -n "${LDSRS2_MODULES:-}" ]] && command -v module >/dev/null 2>&1; then
  IFS=',' read -r -a MODULE_LIST <<< "${LDSRS2_MODULES}"
  for module_name in "${MODULE_LIST[@]}"; do
    module load "${module_name}"
  done
fi

if [[ -n "${LDSRS2_CONDA_ENV:-}" ]]; then
  source activate "${LDSRS2_CONDA_ENV}"
fi

exec "${PYTHON_BIN}" -m ldsrs2_launcher.cli run task --manifest "${MANIFEST_PATH}"
