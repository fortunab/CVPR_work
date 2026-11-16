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
case "$selection" in
  heads|vision|pathology) targets=("$selection") ;;
  all) targets=(heads vision pathology) ;;
  *) printf '%s\n' 'Usage: bash scripts/nix_setup.sh [heads|vision|pathology|all]' >&2; exit 2 ;;
esac
for target in "${targets[@]}"; do
  interpreter=python3.12
  [[ $target != pathology ]] || interpreter=python3.10
  environment=".venv-nix-$target"
  if [[ ! -e $environment ]]; then
    "$interpreter" -m venv "$environment"
  fi
  python="$PWD/$environment/bin/python"
  "$python" -c 'import sys; expected=tuple(map(int,sys.argv[1].split("."))); assert sys.version_info[:2]==expected, (sys.version,expected)' "$([[ $target == pathology ]] && printf 3.10 || printf 3.12)"
  case "$target" in
    heads)
      "$python" -m pip install --require-hashes -r requirements/review-linux.lock
      ;;
    vision)
      "$python" -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.13.0 torchvision==0.28.0
      "$python" -m pip install -r requirements/vision-features.txt
      ;;
    pathology)
      "$python" -m pip install -r requirements/pathology-cpu.txt
      ;;
  esac
  "$python" -m pip check
  printf 'Ready: %s\n' "$environment"
done
