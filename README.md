# Do Center-Balanced Prototypes Generalize?

Minimal code for **A Controlled Study in Medical Imaging**. This repository keeps
the implemented paper methods, audited cohort manifests, five task/encoder
configurations, tests, numerical summaries and LaTeX sources. Historical working
folders, pilots, virtual environments, datasets, checkpoint binaries and full run
outputs are not part of the source release.

The study compares center-balanced multi-prototype classification (CBMP) with
eight linear/cosine/prototype controls. Encoders are frozen; tuning uses source
centers only. 

## First: check the paper numbers

This command needs only the Python standard library and the tracked small summaries:

```bash
python scripts/verify_paper_results.py
```

Primary H2 balanced accuracy, four-candidate protocol, ten-seed means (%):

| Encoder | CBMP | Linear | Cosine |
|---|---:|---:|---:|
| ResNet18 | 85.54 | 88.88 | 86.73 |
| UNI | 95.80 | 97.72 | 97.96 |
| CONCH | 92.63 | 96.50 | 96.88 |

Checking these file hashes and values does not refit a classifier or reconstruct
bootstrap intervals. The full run/reconstruction routes are documented below.

## Environment: Windows / PowerShell

Run from this clean repository root, using a new Python 3.12 environment:

```powershell
py -3.12 -m venv .venv-review
$Python = (Resolve-Path '.venv-review/Scripts/python.exe').Path
& $Python -m pip install --require-hashes -r requirements/review-windows.lock
if ($LASTEXITCODE -ne 0) { throw 'Installation failed' }
& $Python -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Dependency check failed' }
& $Python -m pytest tests -q --basetemp tmp/tests-windows
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
# Optional activation instead of using the interpreter path:
# . ./.venv-review/Scripts/Activate.ps1
```

## Environment: Linux / Bash

```bash
set -euo pipefail
python3.12 -m venv .venv-review
source .venv-review/bin/activate
python -m pip install --require-hashes -r requirements/review-linux.lock
python -m pip check
python -m pytest tests -q --basetemp tmp/tests-linux
```

Windows runtime tests and a real paper-cache replay are recorded in
`provenance/RELEASE_VALIDATION.json`. Linux commands and a GitHub Actions matrix
are supplied; a Linux execution result is not claimed before it actually runs.
Three provider-runtime checkpoint tests are skipped without torch and can be run
in the separate pathology environment. For conda, create Python 3.12.3 plus pip,
then install the same platform wheel lock; see [reproduction](docs/REPRODUCTION.md).

## Run the experiments

The registered task names are:

- `polypgen_resnet18`, `polypgen_dinov2`
- `camelyon_resnet18`, `camelyon_custom_uni`, `camelyon_custom_conch`

They use two canonical manifests, not five different cohorts. Ten fixed seeds are
17, 29, 43, 61, 89, 101, 131, 173, 211 and 257. `historical`, `matched4` and
`factorial` remain distinct protocols. `matched4` uses four candidates per tunable
family; centroid controls have one fixed configuration.

### Reuse existing feature caches on this PC

The migration command copies **only** the registered feature files after checking
their original SHA256. It does not copy logs or experiment directories.

```powershell
& $Python scripts/import_local_artifacts.py --source 'C:\path\to\the-original-project'
```

On Linux/Bash:

```bash
python scripts/import_local_artifacts.py --source /path/to/original-project-or-cache-folder
```

The alternative source format is a directory containing `TASK.npz` for each task.
Caches are stored in ignored `artifacts/features/`. Set `CBMP_FEATURE_DIR` to use
an external artifact directory. The code works without the old project once
those verified inputs are supplied. To rebuild features from images, follow
[DATA.md](docs/DATA.md) and [REPRODUCTION.md](docs/REPRODUCTION.md).

### Plan, fit, report

After activating the head-fitting environment, the following commands work in
both Bash and PowerShell. Use a new output name for each independent run:

```bash
python scripts/run_experiments.py --run-dir artifacts/runs/paper --prepare-only
python scripts/run_experiments.py --run-dir artifacts/runs/paper --resume
python scripts/report_review_revision.py --run-dir artifacts/runs/paper --output-dir artifacts/reports/paper --attempts 2000 --seed 2027
python scripts/audit_aggregate_uncertainty.py --report-dir artifacts/reports/paper --output-dir artifacts/reports/patient_sequence_intervals
python scripts/audit_review_stability.py --run-dir artifacts/runs/paper --output-dir artifacts/reports/prototype_stability
python scripts/export_paper_results.py --report-dir artifacts/reports/paper --output-dir artifacts/paper_exports
```

In PowerShell, check `$LASTEXITCODE` after each command; see the complete checked
sequence in the reproduction guide. Defaults are all five tasks, all three
protocols, ten seeds, one worker and four numerical threads. A limited smoke run
can add `--tasks polypgen_resnet18 --seeds 17`; the ten-seed aggregate/paper exports
require the full study. `--resume` requires unchanged code, inputs and settings.

Each completed job saves frozen source choices before target prediction, raw
predictions, metrics, logs and completion hashes under its new runtime folder.
The code never writes to the original research project.

## Repository layout

```text
src/             Frozen classifier, data validation and audit implementation
scripts/         Portable extraction, fitting, reporting and paper exports
configs/         Model identities, task catalog and frozen PolypGen folds
manifests/       Audited image/label/center/group identities; no images
requirements/    Platform wheel locks and separate provider environments
tests/           Core and boundary regression fixtures
results/paper/   Small immutable reference summaries, not full experiment logs
paper/           main.tex, main.bib, sections, figures and supplementary sources
docs/            Data, reproduction and GitHub upload instructions
provenance/      Scientific source hashes and release validation
```

See [GitHub upload instructions](docs/GITHUB_UPLOAD.md) and [scope/provenance](NOTICE.md).
`paper/main.tex` is the Overleaf entry point; `paper/supplementary.tex` compiles the
separate supplement. Results remain limited to the recorded sequences and sampled
patients; more seeds or encoders do not add independent hospitals.
