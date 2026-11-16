#!/usr/bin/env bash
# Source inside nix develop. Functions remain local to this shell session.
if [[ ${CBMP_NIX_SHELL:-} != 1 ]]; then
  printf '%s\n' 'Enter nix develop, then source scripts/nix_env.sh.' >&2
  return 1 2>/dev/null || exit 1
fi
CBMP_NIX_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
export CBMP_NIX_ROOT
export CBMP_FEATURE_DIR="${CBMP_FEATURE_DIR:-$CBMP_NIX_ROOT/artifacts/features/full-reproduction}"
export CBMP_PATHOLOGY_DEVICE="${CBMP_PATHOLOGY_DEVICE:-cpu}"
_cbmp_nix_python() {
  local target=$1
  shift
  if [[ ${CBMP_NIX_SHELL:-} != 1 ]]; then
    printf '%s\n' 'These interpreter functions must run inside nix develop.' >&2
    return 1
  fi
  local executable="$CBMP_NIX_ROOT/.venv-nix-$target/bin/python"
  if [[ ! -x $executable ]]; then
    printf 'Missing environment. Run: bash scripts/nix_setup.sh %s\n' "$target" >&2
    return 1
  fi
  "$executable" "$@"
}
head_python() { _cbmp_nix_python heads "$@"; }
vision_python() { _cbmp_nix_python vision "$@"; }
pathology_python() { _cbmp_nix_python pathology "$@"; }
