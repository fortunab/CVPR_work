# Data and checkpoint inputs

The tracked manifests contain the paper's selected identities, labels, recorded
centers/groups, source annotations and content hashes. They contain no image
pixels. The PolypGen manifest has 5,444 frames and 37 sequences; CAMELYON has
17,200 patches and 43 recorded patients. Paths are relative and can be relocated.
This extraction does not newly adjudicate labels or establish PolypGen patient
linkage. Altering a canonical manifest invalidates its registry hash.

## Fast route: exact paper caches

`scripts/import_local_artifacts.py --source ORIGINAL_PROJECT` copies only the five
matching NPZ feature files. A directory containing the five `TASK.npz` files is
also accepted. Their complete SHA256 values are in `configs/tasks.json`. Nothing
is fitted, no raw image is read and no old experiment directory is imported.

These large numerical files are runtime inputs, not part of Git. Supply them as
a separately authorized release artifact if distributing cached refitting inputs.
This code-only Git repository does not claim those caches are publicly hosted.

## PolypGen raw reconstruction

Acquire `PolypGen2021_MultiCenterData_v3.zip` through the dataset's permitted access
route. Reference: Ali et al., DOI **10.1038/s41597-023-01981-y**.

```bash
python scripts/stage_images.py --dataset polypgen --archive /path/to/PolypGen2021_MultiCenterData_v3.zip
```

PowerShell uses the same arguments with a quoted Windows path. Only the reviewed
frames are copied to ignored `data/raw/polypgen/`. Their original encoded-image
hashes must match. ZIP members are read by registered suffix; arbitrary archive
paths are never extracted. Multiple matches cause an error. Labels, sequence
groups and reviewed center assignments come from the audited manifest, not from
guessing center identity from directory names.

For existing extracted images:

```bash
python scripts/stage_images.py --dataset polypgen --image-root /path/to/extracted/PolypGen2021_MultiCenterData_v3
```

`src/audit_cbmp_data.py` and the unchanged manifest implementation are retained for
annotation/provenance inspection. A newly generated audit is not automatically
the reviewed paper cohort; the canonical identities must still match.

## CAMELYON patches

The paper uses a pinned redistribution of CAMELYON17-WILDS, with label-blind
patient capping. It is not the complete official WILDS protocol. Sources are
H0/H3/H4 (26 patients), primary target H2 has 9 patients and secondary H1 has 8.
Patient-macro patch metrics do not infer clinical patient/slide diagnoses.

If the exact selected images already exist:

```bash
python scripts/stage_images.py --dataset camelyon --image-root /path/to/existing/images
```

Alternatively obtain the original pinned parquet files under their dataset terms:

- Dataset repository: `wltjr1007/Camelyon17-WILDS`
- Revision: `d784d5344ba6c967f83f9f3d9b2f1e2a4d6eb78f`
- Required shard names and row-group positions: `manifests/camelyon.csv`

With a compatible Hugging Face Hub installation, download through its normal
provider API (`snapshot_download`, `repo_type='dataset'`, the revision above and
`allow_patterns=['*.parquet']`). This can be a large transfer; it is not needed
for cached head fitting. Then, in the separate vision-feature environment:

```bash
python scripts/extract_camelyon_parquet.py --shard-dir /path/to/downloaded/parquet
```

The extractor reads the manifest's exact shard rows, verifies encoded and decoded
pixel hashes, and saves only the registered patches in `data/raw/camelyon/`.
No images, paraphrased clinical labels or extra target patients are synthesized.

## Pretrained encoders

ResNet18 and DINOv2 public files are pinned in `configs/vision_assets.json`:

```bash
python scripts/fetch_vision_checkpoints.py --destination artifacts/checkpoints/vision
```

Original UNI and CONCH require provider approval and local login:

- https://huggingface.co/MahmoodLab/UNI
- https://huggingface.co/MahmoodLab/CONCH

In the separate pathology environment, log in interactively and fetch pinned bytes:

```bash
python -c "from huggingface_hub import login; login(add_to_git_credential=False)"
python scripts/fetch_pathology_checkpoints.py --registry configs/pathology_models.json --dest artifacts/checkpoints/pathology
```

Credentials stay outside the repository. No token argument is accepted by the
paper scripts. Checkpoint identifiers and SHA256 are recorded, but access rights
are not supplied by configuration files. Original UNI/CONCH are not UNI2 or later
CONCH derivatives. Pretraining overlap with the evaluation cohort remains unaudited.
