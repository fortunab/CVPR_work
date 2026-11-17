#!/usr/bin/env bash
# Data-free environment validation, not a raw-image reproduction claim.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
bash -n scripts/nix_setup.sh scripts/nix_env.sh
bash scripts/nix_setup.sh heads
source scripts/nix_env.sh
head_python -c 'import sys,numpy,scipy,sklearn; print(sys.version); print(numpy.__version__,scipy.__version__,sklearn.__version__)'
head_python scripts/check_reviewer_environment.py --profile heads
head_python -m pytest tests -q --basetemp tmp/nix-tests
head_python scripts/verify_paper_results.py
head_python scripts/run_experiments.py --help >/dev/null
python3.11 -c 'import ssl,venv; print("Single Python 3.11 runtime available")'
mkdir -p tmp/nix-validation
head_python -m pip freeze --all > tmp/nix-validation/head-packages.txt
head_python -c 'import json,sys,numpy,scipy,sklearn; print(json.dumps({"scope":"data-free Nix head environment check", "python":sys.version.split()[0],"numpy":numpy.__version__,"scipy":scipy.__version__,"scikit_learn":sklearn.__version__,"raw_data_reproduction":False,"pathology_dependencies_tested":False,"vision_dependencies_tested":False},indent=2))' > tmp/nix-validation/environment.json
