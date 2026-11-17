# Do Center-Balanced Prototypes Generalize?

A controlled study in medical imaging: frozen features, nine classifier heads,
five task/encoder settings, ten fitting seeds and three source-only protocols.

[Project website](https://anonymous.4open.science/w/CVPR_work-7DDE/) ·
[Reproduction guide](docs/REPRODUCE_ALL.md) · [Data access](docs/DATA.md)

## Reproduce with a few commands

Use **Python 3.11** for both venv and conda. Run commands from this repository
root. The small `reproduce.py` launcher creates separate package environments
and calls the existing scientific scripts; it does not change the algorithms.

Choose one setup:

```bash
python reproduce.py setup --manager venv
```

or:

```bash
python reproduce.py setup --manager conda
```

Then check the installation and refit using the five genuine feature caches:

```bash
python reproduce.py check
python reproduce.py run --features /path/to/paper-features
```

These commands work from PowerShell or Bash; quote paths containing spaces.
`check` tests the installation and saved summary checksums. **Only `run` fits
the study.** It runs all five tasks, ten seeds and three protocols by default,
then regenerates reports and paper exports and compares the means to the recorded
results. Outputs go into `artifacts/reviewer-run`; use `--resume` after an
interruption, or `--output` for a different run directory.

For venv, install Python 3.11 first and make it available as `python` or
`python3.11`. On Windows, `py -3.11` can replace `python`; `setup --python PATH`
also accepts an explicit Python 3.11 executable. Conda setup creates Python 3.11
itself. Environments need no activation, and the launcher remembers your choice.

## Start from real images instead

Add the feature dependencies to your chosen setup (venv shown; conda is also
supported), obtain the permitted datasets and provider access, then run:

```bash
python reproduce.py setup --manager venv --features
python reproduce.py login
python reproduce.py images --polypgen-root /path/to/polypgen --camelyon-root /path/to/camelyon
```

`images` verifies the canonical images/checkpoints, extracts all five feature
sets and runs the full classifier study. The pretrained encoders stay frozen.
See the [short complete guide](docs/REPRODUCE_ALL.md) for archive/parquet staging,
local checkpoints, CPU/GPU selection and a smaller first refit.

## What is portable, and what is fixed?

Pip selects the appropriate wheels using ordinary requirements files, without
machine-specific hash-file commands in the reviewer setup. Scientific package
versions, input identities, seeds, models and protocols remain controlled.
CPU execution is the default; no particular GPU is required for head fitting.

This does not imply support for every machine or bitwise equality across all
hardware. Feature extraction requires supported PyTorch wheels, sufficient
memory/storage, and access to UNI/CONCH weights. The tested platforms are
Windows x86_64 and Ubuntu 24.04 x86_64; other platforms remain unverified.
The installation checker reports incompatible runtimes. Package environments remain separate because
the two encoder-provider stacks require different dependency versions.

Real-image probes also found PolypGen feature drift between libjpeg 9 and the
libjpeg-turbo decoder in pip's Pillow wheels, despite identical Pillow versions.
The checker records the decoder. Use the genuine original caches for the
confirmed numerical refit route; full agreement after fresh image decoding
remains unverified.

## Recorded paper numbers

Primary H2 balanced accuracy, four-candidate protocol, ten-seed means (%):

| Encoder | CBMP | Linear | Cosine |
|---|---:|---:|---:|
| ResNet18 | 85.54 | 88.88 | 86.73 |
| UNI | 95.80 | 97.72 | 97.96 |
| CONCH | 92.63 | 96.50 | 96.88 |

Checking these saved values is not a refit. Validation scope and measured rerun
differences are recorded in `provenance/REVIEWER_REPRODUCTION.json`.

## Materials and scope

The source release contains scientific code, manifests, configurations, tests,
recorded summaries and anonymous manuscript sources. Raw medical images,
checkpoints, numerical feature caches and private run trees are separate inputs.
The cohort is custom; results are conditional on the recorded centers and groups,
not an official full WILDS benchmark or a hospital-population guarantee.

[Optional Nix setup](docs/NIX.md) remains an additional choice. Historical
environment records are retained for provenance; they are not required by the
normal reviewer setup. Dataset/provider terms and licenses remain separate.
