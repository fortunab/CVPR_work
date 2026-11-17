# Reproduce the study

Use **Python 3.11** with either venv or conda. The same commands below work in
PowerShell and Bash; run them from the complete source root, not from `docs/`.
Pip chooses platform-compatible distributions using ordinary requirements.
Do not remove package version constraints to resolve an unsupported platform.

## 1. Choose a setup, then check it

Choose **one** of these commands:

```bash
python reproduce.py setup --manager venv
python reproduce.py setup --manager conda
```

The venv route needs a discoverable Python 3.11 interpreter. If necessary, use
`py -3.11` on Windows, `python3.11` on Linux, or add `--python /path/to/python3.11`
to the venv setup command. The conda route needs a working conda installation
and creates its own Python 3.11 environments. No activation is required afterward.

```bash
python reproduce.py check
```

This installs/checks the classifier dependencies and exercises the test suite.
It labels the saved-number checksum check separately from real model fitting.
It does not use synthetic data as evidence of scientific reproduction.

## 2. Refit from genuine feature caches

Supply a folder containing the five registered NPZ files; original paper caches
must match the hashes in `configs/tasks.json`. Independently extracted caches
must include their matching extraction receipts. This release does not publicly
host the medical datasets or large numerical caches.

```bash
python reproduce.py run --features /path/to/paper-features
```

The default is the full study: **50 task/seed jobs**, all three protocols and
**3,080 target/head/seed metric cells**. It fits the prototype/linear/cosine heads,
recomputes metrics from their predictions, regenerates reports and paper exports,
and saves a comparison against the recorded means. It never replaces the recorded
paper CSVs with new results.

For a smaller first refit on real data:

```bash
python reproduce.py run --features /path/to/paper-features --tasks polypgen_resnet18 --seeds 17 --output artifacts/first-refit
```

This is one real task/seed run, not the complete ten-seed study. Full-paper exports
are reserved for a complete study. Add `--resume` to the same command after an
interruption; use a new `--output` directory when changing inputs or settings.
Defaults use one worker and two numerical threads; `--workers` and `--threads`
allow the reviewer to fit the machine's memory and CPU budget.

## 3. Alternatively, reconstruct features from real images

Create the additional feature environments by adding `--features` to the setup
command you chose in step 1. All environments still use Python 3.11; they are
separate because the original UNI/CONCH and newer vision stacks conflict.
Feature installation also needs Git for the pinned original CONCH source.

```bash
python reproduce.py setup --manager venv --features
python reproduce.py check --features
```

Replace `venv` with `conda` if that is your selected manager. The feature checks
exercise dependencies and model APIs without downloading pretrained weights or
using patient images. They do not constitute feature reproduction.

Obtain PolypGen and the selected CAMELYON17 images under their access terms;
see [DATA.md](DATA.md) for the exact source versions and registered identities.
If starting from the permitted archive and pinned CAMELYON parquet shards:

```bash
python reproduce.py stage --polypgen-archive /path/to/PolypGen2021_MultiCenterData_v3.zip --camelyon-shards /path/to/parquet
```

Request UNI/CONCH provider access, then log in locally and run:

```bash
python reproduce.py login
python reproduce.py images
```

The defaults use the staged `data/raw/polypgen` and `data/raw/camelyon` folders.
For existing image folders, instead use:

```bash
python reproduce.py images --polypgen-root /path/to/polypgen --camelyon-root /path/to/camelyon
```

Images must match the canonical manifest hashes. The command fetches only pinned
checkpoint bytes, extracts frozen features and calls the same full fitting and
reporting sequence as step 2. `--checkpoints /path/to/checkpoints` reuses verified
local weights laid out under `vision/` and `pathology/`. CPU is the default;
`--device cuda` is an explicit opt-in requiring compatible hardware/drivers.
Reducing `--batch-size` can reduce extraction memory use. A CPU fallback does not
establish bitwise equality with the historical GPU extraction.

## 4. Inspect outputs

The selected run directory contains fitted heads, source selections, predictions,
the actual environment record and completion marker. Its associated reports and
exports contain newly computed results and a machine-readable comparison to the
tracked summaries. Read that comparison before claiming agreement with the paper.
Full-study means and seed standard deviations use an absolute 1e-6 score tolerance
for cross-platform numerical agreement; every measured difference is retained.
Missing data, invalid checkpoints, changed receipts and incomplete studies fail
with an actionable error rather than returning the paper's saved numbers.

## Portability and validation

No setup can truthfully guarantee every OS, CPU architecture, GPU or provider
runtime. The tested targets are Windows x86_64 and Ubuntu 24.04 x86_64 CPU
operation. Other platforms are unverified and may lack compatible PyTorch or
other package wheels. Scientific versions are fixed
while pip selects their platform builds; machine-specific wheel files are not
part of the ordinary setup instructions.

The package/version checker, test suite, real cached-feature refits and fresh
image extraction have different scopes. The current measured scope is recorded
in `provenance/REVIEWER_REPRODUCTION.json`; do not infer a full raw-data rerun
from a passing installation test. UNI/CONCH still require provider approval.

**Known image-decoding difference:** the original PolypGen pixels used libjpeg 9.
Pip's Pillow 10.4.0 wheels use libjpeg-turbo and produced different pixels and
features on the tested JPEG images. On four source images, using the original
decoded pixels in the new Python 3.11 environment restored agreement within
1.5e-8 per ResNet18 feature coordinate and 7.5e-9 for DINOv2.
The checker records the JPEG decoder and warns about this difference. A fresh
extraction is still compared to the recorded results; agreement is not assumed.
Exact-cache refits and fresh raw-image reproduction are separate validation claims.

There is also an [optional Nix route](NIX.md). Older environment records are
historical provenance, not a second setup required of reviewers.
