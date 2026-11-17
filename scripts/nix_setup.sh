#!/usr/bin/env bash
# Optional, separate environments; no existing venv/conda paths are reused.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
if [[ ${CBMP_NIX_SHELL:-} != 1 ]]; then
  printf '%s\n' 'Enter nix develop before running this script.' >&2
  exit 1
fi
if [[ $(uname -s) != Linux || $(uname -m) != x86_64 ]]; then
  printf '%s\n' 'This optional route supports x86_64 Linux, including WSL2.' >&2
  exit 1
fi
selection=${1:-heads}
mkdir -p tmp
case "$selection" in
  heads|vision|pathology) targets=("$selection") ;;
  all) targets=(heads vision pathology) ;;
  *) printf '%s\n' 'Usage: bash scripts/nix_setup.sh [heads|vision|pathology|all]' >&2; exit 2 ;;
esac
for target in "${targets[@]}"; do
  interpreter=python3.11
  environment=".venv-nix-$target"
  if [[ ! -e $environment ]]; then
    "$interpreter" -m venv "$environment"
  fi
  python="$PWD/$environment/bin/python"
  "$python" -c 'import sys; assert sys.version_info[:2]==(3,11), "Use a new Python 3.11 environment directory"'
  case "$target" in
    heads)
      "$python" -m pip install -r requirements/reviewer-heads.txt
      ;;
    vision)
      "$python" -m pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements/reviewer-vision.txt
      ;;
    pathology)
      "$python" -m pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements/reviewer-pathology.txt
      ;;
  esac
  "$python" -m pip check
  printf 'Ready: %s\n' "$environment"
done
