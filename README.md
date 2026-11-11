# Do Center-Balanced Prototypes Generalize?

Code for **A Controlled Study in Medical Imaging**. This repository keeps
the implemented paper methods, audited cohort manifests, five task/encoder
configurations, tests, numerical summaries and LaTeX sources. Historical working
folders, pilots, virtual environments, datasets, checkpoint binaries and full run
outputs are not part of the source release.

The study compares center-balanced multi-prototype classification (CBMP) with
eight linear/cosine/prototype controls. Encoders are frozen; tuning uses source
centers only.

## Reproduce the complete study, including classifier fitting

Follow [the ordered end-to-end guide](docs/REPRODUCE_ALL.md) to start from
images and pretrained checkpoints, extract all five feature sets, fit/select
all heads over ten seeds and three protocols, and regenerate reports and table
exports. It includes complete PowerShell and Bash/Linux commands, venv and conda
setup, expected outputs, and a paper-to-output map. Apply the accompanying supplementary-export fix if using an older release.

The fitting command actually trains the linear/cosine heads and fits the
prototype banks. The paper does not train or fine-tune the pretrained encoders.
Downloading weights or checking saved summaries does not reproduce that fitting.

| Starting point | Route | External inputs |
|---|---|---|
| Raw images | [Complete reproduction](docs/REPRODUCE_ALL.md) | Exact dataset images and provider checkpoints; UNI/CONCH access approval |
| Small saved summaries | Quick check below | None; this only checks hashes and displays recorded values |

The main reproduction route needs no files from the authors' old project.
`artifacts/` is only the output directory for features extracted from real images,
fitted models, predictions and reports. Optional reuse of exact paper features
is documented in the guide's appendix, separately from raw-data reproduction.

## Optional quick check: recorded paper numbers

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

## Choose your platform and environment manager

| Platform | venv | conda |
|---|---|---|
| Windows PowerShell | [Setup 1A](docs/REPRODUCE_ALL.md#1a-windows-powershell-with-venv) | [Setup 1B](docs/REPRODUCE_ALL.md#1b-windows-powershell-with-conda) |
| Linux Bash | [Setup 1C](docs/REPRODUCE_ALL.md#1c-linux-bash-with-venv) | [Setup 1D](docs/REPRODUCE_ALL.md#1d-linux-bash-with-conda) |

Start with step 0 of the guide, choose one setup, then follow your shell's block
in steps 2-9. Each setup creates separate head, vision and pathology environments.
The guide uses explicit interpreter functions; conda uses `conda run` so Windows
DLL paths and the chosen environment are set without activation switching.

Head-fitting dependencies use OS-specific hash-locked wheels. Vision/provider
requirements stay separate. Actual Linux provisioning and full raw reconstruction
have not been independently executed in this audit; documentation and shell
syntax checks do not establish a full reproduction.

## Run the experiments

The registered task names are:

- `polypgen_resnet18`, `polypgen_dinov2`
- `camelyon_resnet18`, `camelyon_custom_uni`, `camelyon_custom_conch`

They use two canonical manifests, not five different cohorts. Ten fixed seeds are
17, 29, 43, 61, 89, 101, 131, 173, 211 and 257. `historical`, `matched4` and
`factorial` remain distinct protocols. `matched4` uses four candidates per tunable
family; centroid controls have one fixed configuration.

### Prepare real-data features

Complete steps 3-5 of [the end-to-end guide](docs/REPRODUCE_ALL.md): obtain and
stage the exact real-image cohorts, fetch the pretrained checkpoints, and extract
all five feature sets. The commands below then train/select the heads and
regenerate predictions and analyses. No precomputed author run is required.

### Plan, fit, report

After steps 0-5 of the guide have prepared the selected environment functions
and all five real-data feature sets, run your shell's block below. Defaults are
all five tasks, all ten seeds, all three protocols, one worker and four numerical
threads. The guide gives the explicit study arguments and a separate smoke run.

**PowerShell:**

```powershell
Invoke-HeadPython scripts/run_experiments.py --run-dir artifacts/runs/paper --prepare-only
Invoke-HeadPython scripts/run_experiments.py --run-dir artifacts/runs/paper --resume
Invoke-HeadPython scripts/report_review_revision.py --run-dir artifacts/runs/paper --output-dir artifacts/reports/paper --attempts 2000 --seed 2027
Invoke-HeadPython scripts/audit_aggregate_uncertainty.py --report-dir artifacts/reports/paper --output-dir artifacts/reports/patient_sequence_intervals
Invoke-HeadPython scripts/audit_review_stability.py --run-dir artifacts/runs/paper --output-dir artifacts/reports/prototype_stability
Invoke-HeadPython scripts/export_paper_results.py --report-dir artifacts/reports/paper --output-dir artifacts/paper_exports
Invoke-HeadPython scripts/export_review_supplement.py --report-dir artifacts/reports/paper --aggregate-dir artifacts/reports/patient_sequence_intervals --stability-dir artifacts/reports/prototype_stability --output-dir artifacts/supplement_exports
```

**Bash/Linux:**

```bash
head_python scripts/run_experiments.py --run-dir artifacts/runs/paper --prepare-only
head_python scripts/run_experiments.py --run-dir artifacts/runs/paper --resume
head_python scripts/report_review_revision.py --run-dir artifacts/runs/paper --output-dir artifacts/reports/paper --attempts 2000 --seed 2027
head_python scripts/audit_aggregate_uncertainty.py --report-dir artifacts/reports/paper --output-dir artifacts/reports/patient_sequence_intervals
head_python scripts/audit_review_stability.py --run-dir artifacts/runs/paper --output-dir artifacts/reports/prototype_stability
head_python scripts/export_paper_results.py --report-dir artifacts/reports/paper --output-dir artifacts/paper_exports
head_python scripts/export_review_supplement.py --report-dir artifacts/reports/paper --aggregate-dir artifacts/reports/patient_sequence_intervals --stability-dir artifacts/reports/prototype_stability --output-dir artifacts/supplement_exports
```

Use new output names for independent runs. `--resume` requires identical code,
inputs and settings. A one-seed run cannot support ten-seed aggregate/paper exports.

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

