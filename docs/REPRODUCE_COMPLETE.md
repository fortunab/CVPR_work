# Complete end-to-end tutorial

This guide covers the current five-task, ten-seed study from real images through
classifier fitting, evaluation, uncertainty analysis and table exports. It
includes **Windows PowerShell and Linux Bash**, each with **venv or conda**.
No files from an old author workspace are required by the main route.


This is the **complete, explicit workflow**: four environment setup choices,
real data, all five feature sets, all registered classifier experiments,
uncertainty/stability analyses, paper exports and result comparisons.
For the three-command launcher route, use the separate [Short tutorial](REPRODUCE_ALL.md).
Choose one tutorial; the detailed route below uses its own environment/output paths.

The detailed scientific stages from the earlier guide are retained here. Its
environment instructions now use **Python 3.11 throughout** and ordinary portable
requirements, matching the short route's scientific package versions.

## How to use this guide

1. Complete step 0 for your operating system.
2. Choose exactly one setup in step 1: **1A, 1B, 1C or 1D**.
3. Follow steps 2-9 using only your shell's block at each step.
4. Stay in the same terminal so interpreter functions remain defined. After
   reopening it, restore step 0 and the functions/paths for the existing
   environments; do not repeat environment creation.

| Platform | Environment manager | Setup |
|---|---|---|
| Windows PowerShell | venv | [1A](#1a-windows-powershell-with-venv) |
| Windows PowerShell | conda | [1B](#1b-windows-powershell-with-conda) |
| Linux Bash | venv | [1C](#1c-linux-bash-with-venv) |
| Linux Bash | conda | [1D](#1d-linux-bash-with-conda) |

The paper trains linear/cosine classifier heads and fits prototype banks on
**frozen** representations. It does not pretrain or fine-tune ResNet18, DINOv2,
UNI or CONCH. Published weights are prepared as inputs; training the paper's
heads happens in step 6.

Three environments stay separate, all on **Python 3.11**: **head** for classifier
fitting/reporting, **vision** for ResNet18/DINOv2, and **pathology** for original
UNI/CONCH. Their provider packages need different dependency versions. The setup
defines forwarding functions, so later commands select the intended interpreter.

## 0. Obtain a fixed source snapshot and choose outputs

Download/extract the full code release or clone the repository. Integrate the
accompanying supplementary-export correction if it is not included. Run from the
root containing `src`, `scripts`, `configs`, `manifests` and `tests`. Record
`git rev-parse HEAD` when available, and record local updates separately.

Prerequisites: 64-bit Windows or x86_64 Linux, Git, network access, dataset/model
access and disk/RAM for images, checkpoints, features and generated runs. Full
fresh-run time and peak storage have not been measured in this audit. macOS/ARM
remains unverified; Windows x86_64 and Ubuntu 24.04 x86_64 are the tested targets.

For venv, install Python 3.11 with venv support. Any Python 3.11 patch version
uses the same package constraints; record the actual version in step 2.
The conda route creates Python 3.11 environments. No environment activation or
PowerShell execution-policy change is needed by the forwarding functions.
For conda, use a terminal where `conda --version` works. Creation uses Python/pip
from conda-forge, followed by the repository's pip requirements; do not install a
second conda NumPy/PyTorch stack afterward.

Use fresh output directories. `artifacts/` is only a name for outputs derived
from real data: features, fitted models, predictions and reports. Test fixtures
are not scientific inputs. The main route uses no old author feature caches.

**PowerShell:**

```powershell
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath 'C:\path\to\paper-code'
if (-not (Test-Path -LiteralPath 'scripts/run_experiments.py')) { throw 'Open the full repository root' }
$env:CBMP_FEATURE_DIR = Join-Path $PWD 'artifacts/features/full-reproduction'
$PathologyDevice = 'cpu'
New-Item -ItemType Directory -Force -Path artifacts/environment-records/full-reproduction | Out-Null
```

**Bash/Linux:**

```bash
set -euo pipefail
cd '/path/to/paper-code'
test -f scripts/run_experiments.py
export CBMP_FEATURE_DIR="$PWD/artifacts/features/full-reproduction"
CBMP_PATHOLOGY_DEVICE='cpu'
mkdir -p artifacts/environment-records/full-reproduction
```

Replace the example repository path above. Keep `CBMP_FEATURE_DIR` unchanged for
extraction, fitting and prototype auditing. If repeating a full reconstruction,
choose fresh feature/run/report/export directories consistently. The extractor
will not replace an existing feature cache.

Native Linux paths differ from Windows paths. In WSL, a path such as
`D:\datasets\...` is normally `/mnt/d/datasets/...`; native Linux uses its
own mounts. Do not reuse a Windows venv in Linux/WSL.

### CPU and GPU configuration

The supplied reviewer setup installs CPU PyTorch wheels. The full classifier
study runs on CPU; extraction also defaults to CPU. A smaller extraction batch
reduces memory use. `--device cuda` requires a separately validated CUDA-enabled
Python 3.11 environment and compatible existing hardware/drivers. Merely changing
the device flag does not turn a CPU wheel into a CUDA build. Historical GPU
inventories remain provenance, not a second required Python setup.

## 1. Create three environments: choose one option

Use new environment directories. If they already exist, restore their path and
function definitions without recreating them, or choose new names. No command
below clears an environment or installs into conda base.

### 1A. Windows PowerShell with venv

The `py` selectors use installed interpreters; confirm their versions.

```powershell
py -3.11 --version
if ($LASTEXITCODE -ne 0) { throw 'Python 3.11 is required' }
py -3.11 -m venv .venv-review
if ($LASTEXITCODE -ne 0) { throw 'Head venv creation failed' }
py -3.11 -m venv .venv-vision
if ($LASTEXITCODE -ne 0) { throw 'Vision venv creation failed' }
py -3.11 -m venv .venv-pathology
if ($LASTEXITCODE -ne 0) { throw 'Pathology venv creation failed' }
$HeadPython = (Resolve-Path '.venv-review/Scripts/python.exe').Path
$VisionPython = (Resolve-Path '.venv-vision/Scripts/python.exe').Path
$PathologyPython = (Resolve-Path '.venv-pathology/Scripts/python.exe').Path
function Invoke-HeadPython {
    & $HeadPython @args
    if ($LASTEXITCODE -ne 0) { throw 'Head Python command failed; see the error above' }
}
function Invoke-VisionPython {
    & $VisionPython @args
    if ($LASTEXITCODE -ne 0) { throw 'Vision Python command failed; see the error above' }
}
function Invoke-PathologyPython {
    & $PathologyPython @args
    if ($LASTEXITCODE -ne 0) { throw 'Pathology Python command failed; see the error above' }
}
```

Continue at step 2. Activation is optional because the functions use explicit
interpreter paths; no PowerShell execution-policy change is needed.

### 1B. Windows PowerShell with conda

The prefix environments live under the already-ignored `.conda/` directory.
`conda run` supplies the environment context, including Windows DLL paths. Do
not replace it with an unactivated conda-prefix `python.exe` invocation.

```powershell
conda --version
if ($LASTEXITCODE -ne 0) { throw 'Open a conda-enabled PowerShell terminal' }
$HeadPrefix = Join-Path $PWD '.conda/review'
$VisionPrefix = Join-Path $PWD '.conda/vision'
$PathologyPrefix = Join-Path $PWD '.conda/pathology'
conda create --override-channels --channel conda-forge --prefix $HeadPrefix python=3.11 pip -y
if ($LASTEXITCODE -ne 0) { throw 'Head conda environment creation failed' }
conda create --override-channels --channel conda-forge --prefix $VisionPrefix python=3.11 pip -y
if ($LASTEXITCODE -ne 0) { throw 'Vision conda environment creation failed' }
conda create --override-channels --channel conda-forge --prefix $PathologyPrefix python=3.11 pip -y
if ($LASTEXITCODE -ne 0) { throw 'Pathology conda environment creation failed' }
function Invoke-HeadPython {
    conda run --no-capture-output --prefix $HeadPrefix python @args
    if ($LASTEXITCODE -ne 0) { throw 'Head conda command failed; see the error above' }
}
function Invoke-VisionPython {
    conda run --no-capture-output --prefix $VisionPrefix python @args
    if ($LASTEXITCODE -ne 0) { throw 'Vision conda command failed; see the error above' }
}
function Invoke-PathologyPython {
    conda run --no-capture-output --prefix $PathologyPrefix python @args
    if ($LASTEXITCODE -ne 0) { throw 'Pathology conda command failed; see the error above' }
}
```

Continue at step 2. No `conda activate`/`deactivate` switching is required.

### 1C. Linux Bash with venv

Python 3.11 needs its matching venv support. If unavailable, install
it for your distribution or use 1D; do not silently substitute `python`.
Keep `set -euo pipefail` from step 0 enabled.

```bash
python3.11 --version
python3.11 -m venv .venv-review
python3.11 -m venv .venv-vision
python3.11 -m venv .venv-pathology
CBMP_HEAD_PYTHON="$PWD/.venv-review/bin/python"
CBMP_VISION_PYTHON="$PWD/.venv-vision/bin/python"
CBMP_PATHOLOGY_PYTHON="$PWD/.venv-pathology/bin/python"
head_python() { "$CBMP_HEAD_PYTHON" "$@"; }
vision_python() { "$CBMP_VISION_PYTHON" "$@"; }
pathology_python() { "$CBMP_PATHOLOGY_PYTHON" "$@"; }
```

Continue at step 2. Activation is optional; the functions use explicit paths.

### 1D. Linux Bash with conda

```bash
conda --version
CBMP_HEAD_PREFIX="$PWD/.conda/review"
CBMP_VISION_PREFIX="$PWD/.conda/vision"
CBMP_PATHOLOGY_PREFIX="$PWD/.conda/pathology"
conda create --override-channels --channel conda-forge --prefix "$CBMP_HEAD_PREFIX" python=3.11 pip -y
conda create --override-channels --channel conda-forge --prefix "$CBMP_VISION_PREFIX" python=3.11 pip -y
conda create --override-channels --channel conda-forge --prefix "$CBMP_PATHOLOGY_PREFIX" python=3.11 pip -y
head_python() { conda run --no-capture-output --prefix "$CBMP_HEAD_PREFIX" python "$@"; }
vision_python() { conda run --no-capture-output --prefix "$CBMP_VISION_PREFIX" python "$@"; }
pathology_python() { conda run --no-capture-output --prefix "$CBMP_PATHOLOGY_PREFIX" python "$@"; }
```

Continue at step 2. These environments are separate from conda base and need
no shell activation. Keep `set -euo pipefail` enabled so failures stop execution.

## 2. Install dependencies, check environments and run tests

Use your shell's block for either setup method. Pip chooses platform wheels
using version-constrained requirements. Install each stack in its own environment.

**PowerShell:**

```powershell
Invoke-HeadPython -m pip install -r requirements/reviewer-heads.txt
Invoke-HeadPython -m pip check
Invoke-VisionPython -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.13.0 torchvision==0.28.0
Invoke-VisionPython -m pip install -r requirements/reviewer-vision.txt
Invoke-VisionPython -m pip check
Invoke-PathologyPython -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.5.1 torchvision==0.20.1
Invoke-PathologyPython -m pip install -r requirements/reviewer-pathology.txt
Invoke-PathologyPython -m pip check
Invoke-HeadPython scripts/check_reviewer_environment.py --profile heads
Invoke-VisionPython scripts/check_reviewer_environment.py --profile vision
Invoke-PathologyPython scripts/check_reviewer_environment.py --profile pathology
Invoke-HeadPython -m pytest tests -q --basetemp tmp/reproduction-tests
Invoke-PathologyPython -m unittest discover -s tests -p test_pathology_checkpoint.py
Invoke-HeadPython scripts/verify_paper_results.py
Invoke-HeadPython -c "import platform,sys; print(platform.platform()); print(sys.version)" | Set-Content -Encoding utf8 artifacts/environment-records/full-reproduction/head-runtime.txt
Invoke-VisionPython -c "import platform,sys; print(platform.platform()); print(sys.version)" | Set-Content -Encoding utf8 artifacts/environment-records/full-reproduction/vision-runtime.txt
Invoke-PathologyPython -c "import platform,sys; print(platform.platform()); print(sys.version)" | Set-Content -Encoding utf8 artifacts/environment-records/full-reproduction/pathology-runtime.txt
Invoke-HeadPython -m pip freeze --all | Set-Content -Encoding utf8 artifacts/environment-records/full-reproduction/head-packages.txt
Invoke-VisionPython -m pip freeze --all | Set-Content -Encoding utf8 artifacts/environment-records/full-reproduction/vision-packages.txt
Invoke-PathologyPython -m pip freeze --all | Set-Content -Encoding utf8 artifacts/environment-records/full-reproduction/pathology-packages.txt
```

**Bash/Linux:**

```bash
head_python -m pip install -r requirements/reviewer-heads.txt
head_python -m pip check
vision_python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.13.0 torchvision==0.28.0
vision_python -m pip install -r requirements/reviewer-vision.txt
vision_python -m pip check
pathology_python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.5.1 torchvision==0.20.1
pathology_python -m pip install -r requirements/reviewer-pathology.txt
pathology_python -m pip check
head_python scripts/check_reviewer_environment.py --profile heads
vision_python scripts/check_reviewer_environment.py --profile vision
pathology_python scripts/check_reviewer_environment.py --profile pathology
head_python -m pytest tests -q --basetemp tmp/reproduction-tests
pathology_python -m unittest discover -s tests -p test_pathology_checkpoint.py
head_python scripts/verify_paper_results.py
head_python -c "import platform,sys; print(platform.platform()); print(sys.version)" > artifacts/environment-records/full-reproduction/head-runtime.txt
vision_python -c "import platform,sys; print(platform.platform()); print(sys.version)" > artifacts/environment-records/full-reproduction/vision-runtime.txt
pathology_python -c "import platform,sys; print(platform.platform()); print(sys.version)" > artifacts/environment-records/full-reproduction/pathology-runtime.txt
head_python -m pip freeze --all > artifacts/environment-records/full-reproduction/head-packages.txt
vision_python -m pip freeze --all > artifacts/environment-records/full-reproduction/vision-packages.txt
pathology_python -m pip freeze --all > artifacts/environment-records/full-reproduction/pathology-packages.txt
```

The minimal head environment does not install torch, so three checkpoint-loader
tests skip there and run separately using unittest in the pathology environment.
Those tests use explicit small test fixtures, not medical results. The summary
checker checks tracked hashes/displays reference values; it does not fit models
or validate newly generated predictions.

## 3. Obtain and stage the real-image cohorts

**Numerical scope:** the default Pillow wheels decode tested PolypGen JPEGs
differently from the original libjpeg 9 build, despite the same Pillow version.
The environment check records the decoder. Bounded real-image probes isolated
this difference; using original decoded pixels restored encoder agreement.
Fresh extraction is a new measured condition, not presumed numerical agreement
with the paper. For confirmed original-input refits, the appendix describes the
separately supplied genuine feature caches. Full image-to-paper reproduction
has not been certified. Read the generated comparison in step 9.


### 3.1 PolypGen

Obtain the permitted v3 archive from the dataset's provider:
[PolypGen2021_MultiCenterData_v3.zip on Synapse](https://www.synapse.org/Synapse:syn45200214).
The [dataset paper](https://doi.org/10.1038/s41597-023-01981-y) documents the release.
Replace the local archive path below. Matching the filename is not sufficient:
staging checks each selected image's recorded content hash.

**PowerShell:**

```powershell
$PolypGenZip = 'D:\datasets\PolypGen2021_MultiCenterData_v3.zip'
Invoke-HeadPython scripts/stage_images.py --dataset polypgen --archive $PolypGenZip
```

**Bash/Linux:**

```bash
CBMP_POLYPGEN_ZIP='/srv/datasets/PolypGen2021_MultiCenterData_v3.zip'
head_python scripts/stage_images.py --dataset polypgen --archive "$CBMP_POLYPGEN_ZIP"
```

Expected: `data/raw/polypgen/STAGED.json` records **5,444 images** from 37
sequences. Labels and group/center IDs come from the reviewed canonical manifest;
this route does not independently repeat the original annotation review.

### 3.2 Custom CAMELYON cohort

Download the pinned community redistribution with the vision environment's Hub
client. This can fetch all matching parquet shards, not just selected patches.
Dataset terms/provider access requirements still apply. The source/revision
are preserved for the custom cohort actually used in the paper.

**PowerShell:**

```powershell
Invoke-VisionPython -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='wltjr1007/Camelyon17-WILDS', repo_type='dataset', revision='d784d5344ba6c967f83f9f3d9b2f1e2a4d6eb78f', allow_patterns=['*.parquet'], local_dir='data/downloads/camelyon')"
Invoke-VisionPython scripts/extract_camelyon_parquet.py --shard-dir data/downloads/camelyon
```

**Bash/Linux:**

```bash
vision_python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='wltjr1007/Camelyon17-WILDS', repo_type='dataset', revision='d784d5344ba6c967f83f9f3d9b2f1e2a4d6eb78f', allow_patterns=['*.parquet'], local_dir='data/downloads/camelyon')"
vision_python scripts/extract_camelyon_parquet.py --shard-dir data/downloads/camelyon
```

Expected: `data/raw/camelyon/STAGED.json` records **17,200 patches** from 43
recorded patients. This is the capped custom cohort, not full official WILDS.
The extractor checks encoded-image and decoded-pixel hashes.

## 4. Fetch ResNet18/DINOv2 weights and extract three feature sets

**PowerShell:**

```powershell
Invoke-VisionPython scripts/fetch_vision_checkpoints.py --destination artifacts/checkpoints/vision
Invoke-VisionPython scripts/extract_features.py --task polypgen_resnet18 --image-root data/raw/polypgen --checkpoint-dir artifacts/checkpoints/vision --threads 4 --batch-size 64
Invoke-VisionPython scripts/extract_features.py --task polypgen_dinov2 --image-root data/raw/polypgen --checkpoint-dir artifacts/checkpoints/vision --threads 8 --batch-size 16
Invoke-VisionPython scripts/extract_features.py --task camelyon_resnet18 --image-root data/raw/camelyon --checkpoint-dir artifacts/checkpoints/vision --threads 4 --batch-size 64
```

**Bash/Linux:**

```bash
vision_python scripts/fetch_vision_checkpoints.py --destination artifacts/checkpoints/vision
vision_python scripts/extract_features.py --task polypgen_resnet18 --image-root data/raw/polypgen --checkpoint-dir artifacts/checkpoints/vision --threads 4 --batch-size 64
vision_python scripts/extract_features.py --task polypgen_dinov2 --image-root data/raw/polypgen --checkpoint-dir artifacts/checkpoints/vision --threads 8 --batch-size 16
vision_python scripts/extract_features.py --task camelyon_resnet18 --image-root data/raw/camelyon --checkpoint-dir artifacts/checkpoints/vision --threads 4 --batch-size 64
```

Expected: `polypgen_resnet18.npz`, `polypgen_dinov2.npz` and
`camelyon_resnet18.npz`, each with a `.receipt.json`, in `CBMP_FEATURE_DIR`.
Checkpoint/configuration identities are pinned in `configs/vision_assets.json`.

## 5. Fetch original UNI/CONCH weights and extract two feature sets

First obtain approval from [UNI](https://huggingface.co/MahmoodLab/UNI) and
[CONCH](https://huggingface.co/MahmoodLab/CONCH), then log in interactively on your
own machine. Approval is external to this repository. Do not put tokens in
commands, source, logs or shared archives. `conda run --no-capture-output` leaves
the login interactive.

**PowerShell:**

```powershell
Invoke-PathologyPython -c "from huggingface_hub import login; login(add_to_git_credential=False)"
Invoke-PathologyPython scripts/fetch_pathology_checkpoints.py --registry configs/pathology_models.json --dest artifacts/checkpoints/pathology
Invoke-PathologyPython scripts/extract_features.py --task camelyon_custom_uni --image-root data/raw/camelyon --checkpoint-dir artifacts/checkpoints/pathology --threads 4 --batch-size 16 --device $PathologyDevice
Invoke-PathologyPython scripts/extract_features.py --task camelyon_custom_conch --image-root data/raw/camelyon --checkpoint-dir artifacts/checkpoints/pathology --threads 4 --batch-size 16 --device $PathologyDevice
```

**Bash/Linux:**

```bash
pathology_python -c "from huggingface_hub import login; login(add_to_git_credential=False)"
pathology_python scripts/fetch_pathology_checkpoints.py --registry configs/pathology_models.json --dest artifacts/checkpoints/pathology
pathology_python scripts/extract_features.py --task camelyon_custom_uni --image-root data/raw/camelyon --checkpoint-dir artifacts/checkpoints/pathology --threads 4 --batch-size 16 --device "$CBMP_PATHOLOGY_DEVICE"
pathology_python scripts/extract_features.py --task camelyon_custom_conch --image-root data/raw/camelyon --checkpoint-dir artifacts/checkpoints/pathology --threads 4 --batch-size 16 --device "$CBMP_PATHOLOGY_DEVICE"
```

Expected: `camelyon_custom_uni.npz` and `camelyon_custom_conch.npz`, with receipts,
in the same feature directory. The three CAMELYON tasks share patient/patch IDs.
The loader checks shapes, norms, identities and provenance. Fresh extraction is
labelled `fresh_extraction`; it is not automatically claimed bitwise-identical
to historical caches. Existing features are not overwritten.

## Experiment matrix and complete candidate configurations

The following settings come from `configs/tasks.json` and the actual
`scripts/review_protocol.py::grids` implementation. The same frozen classifier
code in `src/` is used by both tutorials. No backbone is trained or fine-tuned.

| Registered task | Encoder | Feature dimension | Dataset |
|---|---|---:|---|
| `camelyon_custom_conch` | conch | 512 | camelyon |
| `camelyon_custom_uni` | uni | 1024 | camelyon |
| `camelyon_resnet18` | resnet18 | 512 | camelyon |
| `polypgen_dinov2` | dinov2 | 768 | polypgen |
| `polypgen_resnet18` | resnet18 | 512 | polypgen |

Each task uses seeds **17, 29, 43, 61, 89, 101, 131, 173, 211, 257** and all
three protocols: `historical`, `matched4`, `factorial`. This is 50 task/seed
jobs and 3,080 target/head/seed result cells. A cell holds five metrics, not
five additional independent experiments. Source-only validation selects the
candidate and temperature; target data do not select a fitted head.

| Protocol | Head / control | Candidates | Exact candidate specifications |
|---|---|---:|---|
| `historical` | `cbmp` | 12 | `beta in {0.0, 0.5, 1.0}; k in {1, 2, 4, 8}; kind="prototype"` |
| `historical` | `multi_prototype_unbalanced` | 4 | `beta=0.0; k in {1, 2, 4, 8}; kind="prototype"` |
| `historical` | `linear_logistic` | 5 | `C in {0.01, 0.1, 1.0, 10.0, 100.0}; kind="linear"` |
| `historical` | `trainable_cosine` | 3 | `kind="cosine"; learning_rate in {0.01, 0.03, 0.1}` |
| `historical` | `linear_group_center_weighted` | 15 | `C in {0.01, 0.1, 1.0, 10.0, 100.0}; beta in {0.0, 0.5, 1.0}; kind="linear"` |
| `historical` | `cosine_group_center_weighted` | 9 | `beta in {0.0, 0.5, 1.0}; kind="cosine"; learning_rate in {0.01, 0.03, 0.1}` |
| `historical` | `single_centroid_group_weighted` | 1 | `beta=0.0; k=1; kind="prototype"` |
| `historical` | `single_centroid_center_balanced` | 1 | `beta=1.0; k=1; kind="prototype"` |
| `historical` | `single_centroid_image_weighted` | 1 | `beta=0.0; image_weighted=true; k=1; kind="prototype"` |
| `matched4` | `cbmp` | 4 | `beta in {0.0, 1.0}; k in {1, 4}; kind="prototype"` |
| `matched4` | `multi_prototype_unbalanced` | 4 | `beta=0.0; k in {1, 2, 4, 8}; kind="prototype"` |
| `matched4` | `linear_logistic` | 4 | `C in {0.1, 1.0, 10.0, 100.0}; kind="linear"` |
| `matched4` | `trainable_cosine` | 4 | `kind="cosine"; learning_rate in {0.003, 0.01, 0.03, 0.1}` |
| `matched4` | `linear_group_center_weighted` | 4 | `C in {0.1, 10.0}; beta in {0.0, 1.0}; kind="linear"` |
| `matched4` | `cosine_group_center_weighted` | 4 | `beta in {0.0, 1.0}; kind="cosine"; learning_rate in {0.01, 0.1}` |
| `matched4` | `single_centroid_group_weighted` | 1 | `beta=0.0; k=1; kind="prototype"` |
| `matched4` | `single_centroid_center_balanced` | 1 | `beta=1.0; k=1; kind="prototype"` |
| `matched4` | `single_centroid_image_weighted` | 1 | `beta=0.0; image_weighted=true; k=1; kind="prototype"` |
| `factorial` | `K1_beta0` | 1 | `beta=0.0; k=1; kind="prototype"` |
| `factorial` | `K1_beta1` | 1 | `beta=1.0; k=1; kind="prototype"` |
| `factorial` | `K4_beta0` | 1 | `beta=0.0; k=4; kind="prototype"` |
| `factorial` | `K4_beta1` | 1 | `beta=1.0; k=4; kind="prototype"` |

For each row, combine the listed varying parameter values as a Cartesian product;
the candidate count confirms the complete grid. Constant values apply to every
candidate in that row. No candidate is omitted from this table.

`k` is prototypes per class; `beta` controls center influence; `C` is the
logistic regularization parameter; `learning_rate` is the trained-cosine step
size. Weighted learned heads use the recorded class/group/center weighting.
Source and target partitions are in `configs/polypgen_splits.json` and the
registered cohort loader. Individual source selections and temperatures are
saved in each job's `source_heads_frozen.json`; do not replace the grids with
the final winning settings before running validation.

Prototype fitting uses the frozen implementation's five restarts; logistic
regression uses its 3,000-iteration convergence limit; the cosine head uses
300 steps. These are implementation settings, not new tuning choices.
Keep `configs/tasks.json`, manifests and classifier-source hashes unchanged.

## 6. Plan, then actually train all heads and evaluate targets

The head environment performs source validation, candidate/temperature selection,
linear/cosine training and prototype fitting/refitting on outer sources. Source
choices are frozen before target prediction. `--prepare-only` validates inputs
and writes `run_manifest.json` without training; the second command runs fitting.
It does not load reference metric CSVs as a substitute for training.

**PowerShell:**

```powershell
$StudyArgs = @(
    '--run-dir', 'artifacts/runs/full-reproduction',
    '--tasks', 'polypgen_resnet18', 'polypgen_dinov2', 'camelyon_resnet18', 'camelyon_custom_uni', 'camelyon_custom_conch',
    '--seeds', '17', '29', '43', '61', '89', '101', '131', '173', '211', '257',
    '--protocols', 'historical', 'matched4', 'factorial',
    '--workers', '1', '--threads', '4'
)
Invoke-HeadPython scripts/run_experiments.py @StudyArgs --prepare-only
Invoke-HeadPython scripts/run_experiments.py @StudyArgs --resume
```

**Bash/Linux:**

```bash
CBMP_STUDY_ARGS=(
    --run-dir artifacts/runs/full-reproduction
    --tasks polypgen_resnet18 polypgen_dinov2 camelyon_resnet18 camelyon_custom_uni camelyon_custom_conch
    --seeds 17 29 43 61 89 101 131 173 211 257
    --protocols historical matched4 factorial
    --workers 1 --threads 4
)
head_python scripts/run_experiments.py "${CBMP_STUDY_ARGS[@]}" --prepare-only
head_python scripts/run_experiments.py "${CBMP_STUDY_ARGS[@]}" --resume
```

| Tasks | Targets per seed | Head/settings cells per target |
|---|---|---|
| PolypGen ResNet18 and DINOv2 | C2, C4, C5, C6 | 9 historical + 9 matched4 + 4 factorial |
| CAMELYON ResNet18, UNI and CONCH | H2 primary, H1 secondary | 9 historical + 9 matched4 + 4 factorial |

Expected: **50 task/seed jobs and 3,080 target/head/seed metric cells** on fixed
cohorts. Each job saves `source_heads_frozen.json`, fitted model/source caches,
`predictions.csv`, `metrics.json`, `run.log` and `COMPLETE.json`. The run root
also gets `COMPLETE.json`. These cells are not independent patient populations.

### Optional one-seed fitting check before the full study

The following uses a separate directory, all three protocols and one task/seed.
It does not replace the full run or support ten-seed aggregate/paper exports.

**PowerShell:**

```powershell
$SmokeArgs = @('--run-dir', 'artifacts/runs/full-smoke', '--tasks', 'polypgen_resnet18', '--seeds', '17', '--protocols', 'historical', 'matched4', 'factorial', '--workers', '1', '--threads', '4')
Invoke-HeadPython scripts/run_experiments.py @SmokeArgs --prepare-only
Invoke-HeadPython scripts/run_experiments.py @SmokeArgs --resume
```

**Bash/Linux:**

```bash
CBMP_SMOKE_ARGS=(--run-dir artifacts/runs/full-smoke --tasks polypgen_resnet18 --seeds 17 --protocols historical matched4 factorial --workers 1 --threads 4)
head_python scripts/run_experiments.py "${CBMP_SMOKE_ARGS[@]}" --prepare-only
head_python scripts/run_experiments.py "${CBMP_SMOKE_ARGS[@]}" --resume
```

## 7. Recompute reports, uncertainty and prototype audits

**PowerShell:**

```powershell
Invoke-HeadPython scripts/report_review_revision.py --run-dir artifacts/runs/full-reproduction --output-dir artifacts/reports/full-reproduction --attempts 2000 --seed 2027
Invoke-HeadPython scripts/audit_aggregate_uncertainty.py --report-dir artifacts/reports/full-reproduction --output-dir artifacts/reports/full-aggregate-intervals
Invoke-HeadPython scripts/audit_review_stability.py --run-dir artifacts/runs/full-reproduction --output-dir artifacts/reports/full-prototype-stability
```

**Bash/Linux:**

```bash
head_python scripts/report_review_revision.py --run-dir artifacts/runs/full-reproduction --output-dir artifacts/reports/full-reproduction --attempts 2000 --seed 2027
head_python scripts/audit_aggregate_uncertainty.py --report-dir artifacts/reports/full-reproduction --output-dir artifacts/reports/full-aggregate-intervals
head_python scripts/audit_review_stability.py --run-dir artifacts/runs/full-reproduction --output-dir artifacts/reports/full-prototype-stability
```

The report recomputes metrics from new predictions and checks worker metrics.
It saves per-seed/averaged metrics, selections, Same/Across and equal-group-pair
ranking, factorial contrasts, paired BA intervals, grid sensitivity, sequence
predictions and patient-macro patch metrics. The aggregate auditor defaults to
2,000 attempts/seed 2027. Stability auditing needs fitted models/source features;
retain those outputs.

## 8. Export main-study and supplementary tables/figures

**PowerShell:**

```powershell
Invoke-HeadPython scripts/export_paper_results.py --report-dir artifacts/reports/full-reproduction --output-dir artifacts/paper-exports-full
Invoke-HeadPython scripts/export_review_supplement.py --report-dir artifacts/reports/full-reproduction --aggregate-dir artifacts/reports/full-aggregate-intervals --stability-dir artifacts/reports/full-prototype-stability --output-dir artifacts/supplement-exports-full
```

**Bash/Linux:**

```bash
head_python scripts/export_paper_results.py --report-dir artifacts/reports/full-reproduction --output-dir artifacts/paper-exports-full
head_python scripts/export_review_supplement.py --report-dir artifacts/reports/full-reproduction --aggregate-dir artifacts/reports/full-aggregate-intervals --stability-dir artifacts/reports/full-prototype-stability --output-dir artifacts/supplement-exports-full
```

The supplement command needs the accompanying exporter correction for unified
five-task reports. Its six `review_*.tex` files retain the original three-task
scope and explicitly use ResNet18 for the original patient-macro tables.
UNI/CONCH summaries/figures are exported separately by the first command; full
foundation contrasts remain in report CSVs.

### Paper-to-output map

| Paper result | Regenerated evidence/export |
|---|---|
| Table 1: PolypGen original-grid mean/worst BA | `paper-exports-full/original/main_polypgen.tex` |
| Figure 2: center-specific PolypGen comparison | `paper-exports-full/original/figure_polypgen.tex` |
| Table 2: three-encoder H2/H1 matched4 BA | Matching cells in `paper-exports-full/patch_summary.csv`; full-head table `foundation_matched4_balanced_accuracy.tex` |
| Table 3: group-ranking diagnostics | `paper-exports-full/original/main_group_ranking.tex` |
| Table 4: fixed-K balancing ranking changes | `paper-exports-full/original/main_factorial_ranking.tex` |
| Historical/matched4/factorial foundation metrics | Six `paper-exports-full/foundation_PROTOCOL_METRIC.tex` files |
| Foundation patch/patient-macro figures | `paper-exports-full/patch_balanced_accuracy.tex`, `patient_macro_balanced_accuracy.tex` |
| Original full image-metric supplement | `paper-exports-full/original/full_ten_seed_tables.tex` |
| Original supplementary interval/endpoint/stability tables | Six `supplement-exports-full/review_*.tex` files |
| Configuration choices and source-selection reversal | Report `selected_settings.csv`, per-job `source_heads_frozen.json` and fixed-factorial metrics |
| NLL, Brier, per-seed metrics, patient/sequence results | Report CSVs; scalar claims must be checked against the matching task/protocol/endpoint |

All export paths in this table are relative to `artifacts/`. The focused Table 2
is a three-head presentation of matching CSV cells; its exact stored filename
and LaTeX layout are not generated by a single command here. Exports do not
automatically overwrite `paper/` or rewrite numbers in manuscript prose. Review
the regenerated values before updating the corresponding LaTeX sources.

## 9. Check completion and compare with recorded paper values

Check the new run's completion, then inspect the reference summaries:

**PowerShell:**

```powershell
Invoke-HeadPython -c "import csv,json,pathlib; run=pathlib.Path('artifacts/runs/full-reproduction'); report=pathlib.Path('artifacts/reports/full-reproduction'); done=json.loads((run/'COMPLETE.json').read_text()); rows=list(csv.DictReader((report/'image_metrics_by_seed.csv').open(encoding='utf-8'))); assert done['completed_jobs']==50, done; assert len(rows)==3080, len(rows); print('Complete:', done['completed_jobs'], 'jobs;', len(rows), 'metric cells')"
Invoke-HeadPython -c "from pathlib import Path; from reproduce import compare_report; compare_report(Path('artifacts/reports/full-reproduction'), True)"
Invoke-HeadPython scripts/verify_paper_results.py
```

**Bash/Linux:**

```bash
head_python -c "import csv,json,pathlib; run=pathlib.Path('artifacts/runs/full-reproduction'); report=pathlib.Path('artifacts/reports/full-reproduction'); done=json.loads((run/'COMPLETE.json').read_text()); rows=list(csv.DictReader((report/'image_metrics_by_seed.csv').open(encoding='utf-8'))); assert done['completed_jobs']==50, done; assert len(rows)==3080, len(rows); print('Complete:', done['completed_jobs'], 'jobs;', len(rows), 'metric cells')"
head_python -c "from pathlib import Path; from reproduce import compare_report; compare_report(Path('artifacts/reports/full-reproduction'), True)"
head_python scripts/verify_paper_results.py
```

`python scripts/verify_paper_results.py` checks the tracked reference summaries;
it does not compare a new run to those summaries. The separate `compare_report`
call compares all 308 newly computed means, seed standard deviations and valid
seed counts. It writes `artifacts/reports/comparison.json`, retaining every
maximum difference and an absolute 1e-6 score tolerance for numerical agreement.
Read `within_numerical_tolerance`; a complete run does not imply matching values.
Compare the new matched4 H2
rows in `patch_summary.csv` to these recorded ten-seed BA values (%):

| Encoder | CBMP | Linear logistic | Trained cosine |
|---|---:|---:|---:|
| ResNet18 | 85.54 | 88.88 | 86.73 |
| UNI | 95.80 | 97.72 | 97.96 |
| CONCH | 92.63 | 96.50 | 96.88 |

Also compare PolypGen original-grid results, selected settings and paired
contrasts with their matching reference tables/CSVs. Retain raw predictions,
model hashes, environment inventories and run/report provenance. A matching
rounded mean does not establish matching predictions or uncertainty intervals.
New hardware/runtime extraction can change features; report any differences
rather than overwriting reference summaries or weakening input checks.

## Restarting and troubleshooting

| Situation | Action |
|---|---|
| New terminal | Restore step 0 with the same paths/mode and only the chosen setup's path/function definitions. Do not recreate environments. |
| Missing Python/venv | Install the correct interpreters with venv support, or use conda. Do not substitute another major/minor version. |
| `conda` not found | Use a conda-enabled terminal. The guide uses `conda run`, not global shell-activation changes. |
| Missing wheel/package | Preserve the error; check OS, x86_64 architecture and interpreter version. Changed pins are a different software condition. |
| Provider 403/login failure | Obtain UNI/CONCH approval and log in locally before retrying. |
| Image hash mismatch | Check the exact dataset release/bytes. Do not edit canonical manifests to suppress it. |
| Feature file exists | Preserve it; select a fresh `CBMP_FEATURE_DIR`. Interrupted extraction is not batch-resumable. |
| Interrupted fitting | Repeat step 6's execution command with identical code, inputs, tasks, seeds and resource settings. |
| Stale `RUNNING` marker | Verify that no worker remains active before handling a stale marker. Never remove a live run's lock. |
| Report/export exists | Use a new destination and update all dependent commands consistently. |
| Only smoke completed | Run the separate full ten-seed plan before aggregate audits and paper exports. |

Changing tasks/seeds/resources requires a new run, not a modified resume. Use a
new report/export directory for another analysis pass without deleting old data.

For optional interactive work, venv activation is
`. ./.venv-review/Scripts/Activate.ps1` in PowerShell or
`source .venv-review/bin/activate` in Bash; `deactivate` leaves it. Conda-enabled
shells can use `conda activate ./.conda/review` and `conda deactivate`. These
activation commands are not needed by the explicit environment functions above.

## Optional appendix: separately supplied exact paper features

This is not required by raw-image reproduction. It applies only if the five
exact task NPZs have been supplied separately; they and the full prediction
archive are not currently hosted in this source release. After steps 0-2,
import them into the selected feature directory, skip 3-5 and continue with
step 6 to actually refit the classifiers.

**PowerShell:**

```powershell
Invoke-HeadPython scripts/import_local_artifacts.py --source 'D:\supplied-paper-features'
```

**Bash/Linux:**

```bash
head_python scripts/import_local_artifacts.py --source '/srv/supplied-paper-features'
```

Replace the example path with the supplied task-NPZ directory or an available
original project. Import is not a download or training command; it verifies
recorded SHA256 values. Keep the same `CBMP_FEATURE_DIR` for import/fitting/audits.

## Scope and validation status

The current measured validation is in `provenance/REVIEWER_REPRODUCTION.json`:
Python 3.11 venv/conda classifier setups passed on Windows/Linux; the separate
vision/pathology dependency checks passed; genuine classifier refits and bounded
real-image probes have separately recorded scopes and differences. The complete
50-job rerun may still be in progress; consult the record rather than inferring
completion from this guide. Installation checks are not scientific reproduction.

The detailed command sequence is explicit so reviewers can inspect or execute
each stage. The short launcher calls the same scientific scripts automatically.
The manual path does not create launcher stage receipts; preserve each scientific
stage's own provenance and use fresh output directories for repeated analyses.

The current-study route excludes historical three-seed pilots, earlier source-
composition/removal stress experiments and legacy archives. Those experiments
are not silently recreated by the 50-job current-study command. Neither tutorial
adds official full-WILDS evaluation, backbone fine-tuning or clinical validation.

Dataset/model details: [DATA.md](DATA.md). For the compact alternative, use the
separate [Short tutorial](REPRODUCE_ALL.md). Both use Python 3.11 and the same
registered scientific models, seeds, inputs and configurations.
