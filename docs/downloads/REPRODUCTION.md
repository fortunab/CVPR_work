# Reproduction from the clean repository

For the ordered PowerShell and Bash/Linux walkthrough, with both venv and conda,
start with [REPRODUCE_ALL.md](REPRODUCE_ALL.md). It covers real images, classifier
training, all five tasks and the main/supplementary exports. This page retains
additional runtime background; use the ordered guide for the complete sequence.

Run commands from this repository root. There is no dependency on the original
dated working folders after the registered inputs are supplied. The small tracked
summaries check point estimates; refitting needs numerical caches, and raw-image
reconstruction additionally needs images and provider checkpoints.

## 1. Head-fitting environment

Use CPython 3.12.3, with platform wheel hashes in `requirements/review-*.lock`.
Windows commands and activation are in the README. Bash/WSL needs its own venv;
a Windows venv cannot be reused. A separate conda route is:

```bash
conda create -n cbmp-paper python=3.12.3 pip=24.0 -y
conda activate cbmp-paper
python -m pip install --require-hashes -r requirements/review-linux.lock
python -m pip check
```

In Windows conda, install `requirements/review-windows.lock` instead. Conda and
full Linux execution are documented routes, not locally executed validations.
The requirements freeze does not imply cross-platform bitwise equivalence.

## 2. Supply exact numerical inputs or reconstruct features

For an existing local project, activate the head environment and run:

```powershell
python scripts/import_local_artifacts.py --source 'C:\path\to\original-project'
```

Only the five whitelisted feature files are copied. The public release contains
no model weights, images, raw predictions, binary fit caches or old output trees.
Set `$env:CBMP_FEATURE_DIR='D:\paper-features'` in PowerShell or
`export CBMP_FEATURE_DIR=/path/to/paper-features` in Bash to store features outside
the clean checkout. Use the same variable for importing, planning and fitting.

For raw reconstruction, stage images and fetch checkpoints as described in DATA.md.
Create a separate Python 3.12 vision environment for ResNet18/DINOv2:

```bash
python3.12 -m venv .venv-vision
.venv-vision/bin/python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.13.0 torchvision==0.28.0
.venv-vision/bin/python -m pip install -r requirements/vision-features.txt
.venv-vision/bin/python -m pip check
.venv-vision/bin/python scripts/fetch_vision_checkpoints.py
.venv-vision/bin/python scripts/extract_features.py --task polypgen_resnet18 --image-root data/raw/polypgen --checkpoint-dir artifacts/checkpoints/vision --threads 4 --batch-size 64
.venv-vision/bin/python scripts/extract_features.py --task polypgen_dinov2 --image-root data/raw/polypgen --checkpoint-dir artifacts/checkpoints/vision --threads 8 --batch-size 16
.venv-vision/bin/python scripts/extract_features.py --task camelyon_resnet18 --image-root data/raw/camelyon --checkpoint-dir artifacts/checkpoints/vision --threads 4 --batch-size 64
```

On Windows, use `py -3.12 -m venv .venv-vision` and the interpreter
`.venv-vision/Scripts/python.exe` for the same commands. Keep the vision packages
separate from the locked head-fitting environment. The recorded encoder versions
are retained; a dependency or hardware change requires its own numerical checks.

For original UNI/CONCH, create a separate Python 3.10 environment:

```bash
python3.10 -m venv .venv-pathology
.venv-pathology/bin/python -m pip install -r requirements/pathology-cpu.txt
.venv-pathology/bin/python -m pip check
.venv-pathology/bin/python -c 'from huggingface_hub import login; login(add_to_git_credential=False)'
.venv-pathology/bin/python scripts/fetch_pathology_checkpoints.py --registry configs/pathology_models.json --dest artifacts/checkpoints/pathology
.venv-pathology/bin/python scripts/extract_features.py --task camelyon_custom_uni --image-root data/raw/camelyon --checkpoint-dir artifacts/checkpoints/pathology --threads 4 --batch-size 16
.venv-pathology/bin/python scripts/extract_features.py --task camelyon_custom_conch --image-root data/raw/camelyon --checkpoint-dir artifacts/checkpoints/pathology --threads 4 --batch-size 16
```

PowerShell setup is equivalent:

```powershell
py -3.10 -m venv .venv-pathology
$ProviderPython = (Resolve-Path '.venv-pathology/Scripts/python.exe').Path
& $ProviderPython -m pip install -r requirements/pathology-cpu.txt
if ($LASTEXITCODE -ne 0) { throw 'Provider installation failed' }
& $ProviderPython -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Provider dependency check failed' }
& $ProviderPython -c 'from huggingface_hub import login; login(add_to_git_credential=False)'
& $ProviderPython scripts/fetch_pathology_checkpoints.py --registry configs/pathology_models.json --dest artifacts/checkpoints/pathology
if ($LASTEXITCODE -ne 0) { throw 'Checkpoint fetch failed' }
& $ProviderPython scripts/extract_features.py --task camelyon_custom_uni --image-root data/raw/camelyon --checkpoint-dir artifacts/checkpoints/pathology --threads 4 --batch-size 16
if ($LASTEXITCODE -ne 0) { throw 'UNI extraction failed' }
& $ProviderPython scripts/extract_features.py --task camelyon_custom_conch --image-root data/raw/camelyon --checkpoint-dir artifacts/checkpoints/pathology --threads 4 --batch-size 16
if ($LASTEXITCODE -ne 0) { throw 'CONCH extraction failed' }
```

The executed original foundation run used Python 3.10.22, torch 2.0.1+cu117,
torchvision 0.15.2+cu117 on GTX 1660 Ti 6GB, not this CPU alternative. To repeat
that configuration, install `requirements/pathology-gpu.txt` in a distinct
environment and add `--device cuda`. Package freezes for the actual CPU/GPU
environments are included. Batch 16/four host threads were originally selected
using 32 source patches, with deterministic CPU/GPU agreement within 2e-5.
No driver modification is part of this release.

The new portable extraction helper uses the prescribed frozen representation and
records every image hash, checkpoint hash, model/runtime setting and initial-batch
repeat check. A fresh cache is labelled `fresh_extraction`, not asserted equal to
the old paper cache. Identical imported cache bytes are labelled `exact_paper_cache`.
ResNet18 and DINOv2 preserve their original feature definitions; CONCH uses its
unprojected visual embedding and permits only the checkpoint's unused decoder
branch to be absent. Source-selection and classifier math remain unchanged.

## 3. Plan and run the registered study

Activate the head-fitting environment again. Planning validates cohort hashes,
row order, class coverage, group/content boundaries, feature norms, cache identity
and frozen core source hashes before fitting.

```bash
python scripts/run_experiments.py --run-dir artifacts/runs/paper --prepare-only
python scripts/run_experiments.py --run-dir artifacts/runs/paper --resume
```

These commands default to all five tasks, all ten seeds, and all three protocols.
That is 3,080 target/head/seed metric cells, not 3,080 independent samples. Feature
extraction is separate; the experiment trains heads only. Source-only choices are
frozen before target scoring. One worker and four threads are the conservative
default. Keep these resource settings identical between plan and execution.

For a deliberately smaller implementation check:

```bash
python scripts/run_experiments.py --run-dir artifacts/runs/smoke --tasks polypgen_resnet18 --seeds 17 --prepare-only
python scripts/run_experiments.py --run-dir artifacts/runs/smoke --tasks polypgen_resnet18 --seeds 17 --resume
```

Such a check does not replace the ten-seed study or support ten-seed paper exports.
Do not edit fitting sources or inputs during execution. Resume accepts only an
identical plan and verifies completed prediction/source-choice hashes. New
configurations require a new run directory. Interrupted feature extraction is not
batch-resumable; use a new feature directory for a new extraction attempt.

## 4. Regenerate analyses and native paper figures

For the complete ten-seed run:

```bash
python scripts/report_review_revision.py --run-dir artifacts/runs/paper --output-dir artifacts/reports/paper --attempts 2000 --seed 2027
python scripts/audit_aggregate_uncertainty.py --report-dir artifacts/reports/paper --output-dir artifacts/reports/group_intervals
python scripts/audit_review_stability.py --run-dir artifacts/runs/paper --output-dir artifacts/reports/stability
python scripts/export_paper_results.py --report-dir artifacts/reports/paper --output-dir artifacts/paper_exports
```

PowerShell with checked exit codes:

```powershell
$Python = (Resolve-Path '.venv-review/Scripts/python.exe').Path
& $Python scripts/run_experiments.py --run-dir artifacts/runs/paper --prepare-only
if ($LASTEXITCODE -ne 0) { throw 'Planning failed' }
& $Python scripts/run_experiments.py --run-dir artifacts/runs/paper --resume
if ($LASTEXITCODE -ne 0) { throw 'Fitting failed' }
& $Python scripts/report_review_revision.py --run-dir artifacts/runs/paper --output-dir artifacts/reports/paper --attempts 2000 --seed 2027
if ($LASTEXITCODE -ne 0) { throw 'Reporting failed' }
& $Python scripts/audit_aggregate_uncertainty.py --report-dir artifacts/reports/paper --output-dir artifacts/reports/group_intervals
if ($LASTEXITCODE -ne 0) { throw 'Group intervals failed' }
& $Python scripts/audit_review_stability.py --run-dir artifacts/runs/paper --output-dir artifacts/reports/stability
if ($LASTEXITCODE -ne 0) { throw 'Prototype audit failed' }
& $Python scripts/export_paper_results.py --report-dir artifacts/reports/paper --output-dir artifacts/paper_exports
if ($LASTEXITCODE -ne 0) { throw 'Paper export failed' }
```

Run directories contain metrics.json, predictions.csv, source_heads_frozen.json,
run.log and COMPLETE.json per task/seed. Reports distinguish frame/patch metrics,
sequence presence, patient-macro patch metrics, group-pair ranking, calibration,
candidate budgets and fixed K/beta interactions. Undefined aggregate endpoints
remain undefined. Bootstrap resamples recorded groups with fixed fitted heads;
intervals do not infer a population of hospitals. Seed SD is separate.

## 5. Validation and limits

`provenance/RELEASE_VALIDATION.json` records actual local checks, not a proposed
protocol. The scientific core sources are byte-identical to those used originally.
The portable source files and configuration hashes differ intentionally because
dated filesystem dependencies were removed. A new run records those new hashes;
historical manifests are not edited to pretend the code revision is unchanged.

The supplied CI checks both Windows/Linux fixtures once pushed. No CI run has
occurred merely by writing the workflow. Full official WILDS, modern DG training,
new patient-linked data, resolved PolypGen linkage, and clinical cluster review
remain outside the completed experimental evidence. Earlier exploratory
three-seed pilot/removal runs are not copied into this minimal current-study
repository; their separate archival records remain in the original workspace.

