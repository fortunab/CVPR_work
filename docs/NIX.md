# Optional Nix route: Linux and WSL2

This is an additional setup route for **x86_64 Linux**, including a Linux distribution in **Windows WSL2**. The existing PowerShell/Bash, venv and conda routes remain available as documented in [the complete reproduction guide](REPRODUCE_ALL.md).

Nix supplies Python 3.12, Python 3.10, Git and shared libraries from a pinned Nixpkgs revision. The Python packages still use the existing requirements and hash-locked classifier environment. They are installed into separate `.venv-nix-heads`, `.venv-nix-vision` and `.venv-nix-pathology` directories. No existing venv or conda environment is reused or modified.

This is a Nix development shell plus Python virtual environments, not a fully offline Nix derivation of the entire study. Dataset access, provider approval and model checkpoints are still required for image-to-result reproduction.

## 1. Install Nix and obtain the full source

Install Nix using the [official Linux/WSL2 instructions](https://nixos.org/download/). On Windows, run this route in your Linux terminal under WSL2; the existing native PowerShell route remains a separate choice. This route currently targets x86_64 Linux, not native Windows, macOS or ARM.

Download the complete source release from the [anonymous repository](https://anonymous.4open.science/r/CVPR_work-7DDE/) or the [project website](https://anonymous.4open.science/w/CVPR_work-7DDE/). Extract it, then open the root containing `flake.nix`, `scripts/` and `requirements/`.

```bash
cd /path/to/paper-code
test -f flake.nix && test -f scripts/run_experiments.py
nix --version
nix --extra-experimental-features 'nix-command flakes' develop
```

The final command opens the development shell. If flakes are already enabled, `nix develop` is sufficient. Keep the committed `flake.lock`; do not update the Nix inputs when checking this release. The pinned legacy-runtime package set deliberately retains Python 3.10 for the original UNI/CONCH provider stack.

## 2. Quick check of the classifier environment

Inside the Nix shell:

```bash
bash scripts/nix_setup.sh heads
source scripts/nix_env.sh
head_python -m pip check
head_python -m pytest tests -q --basetemp tmp/nix-tests
head_python scripts/verify_paper_results.py
```

Or run the same data-free check in one command from the source root:

```bash
nix --extra-experimental-features 'nix-command flakes' develop --command bash scripts/nix_check.sh
```

This installs the hash-locked Linux classifier packages, runs the tests and checks the recorded summary hashes. It does not train the complete study or recreate the original predictions. CPU/GPU/provider integration is a separate check.

## 3. Add the image-feature environments

For full raw-image reproduction, also create the two separate CPU feature environments:

```bash
bash scripts/nix_setup.sh vision
bash scripts/nix_setup.sh pathology
source scripts/nix_env.sh
head_python --version
vision_python --version
pathology_python --version
vision_python -m pip check
pathology_python -m pip check
mkdir -p artifacts/environment-records/nix
for runtime in head vision pathology; do
  "${runtime}_python" -c 'import platform,sys; print(platform.platform()); print(sys.version)' > "artifacts/environment-records/nix/${runtime}-runtime.txt"
  "${runtime}_python" -m pip freeze --all > "artifacts/environment-records/nix/${runtime}-packages.txt"
done
```

`bash scripts/nix_setup.sh all` creates all three environments. The feature installations download large PyTorch packages; UNI and CONCH weights require separate provider access. This route uses the existing CPU requirements. CUDA setup is not included in this optional Nix shell.

The script only installs an environment when requested. It exits on installation errors; do not continue to extraction if an installation or `pip check` fails. If you move the source directory or change the pinned Nix input, use new environment directories instead of reusing virtual environments tied to the old interpreter paths.

## 4. Continue the existing Bash reproduction steps

Stay in `nix develop` and source the interpreter functions whenever you enter a new shell:

```bash
source scripts/nix_env.sh
printf 'Feature output directory: %s\n' "$CBMP_FEATURE_DIR"
printf 'Pathology device: %s\n' "$CBMP_PATHOLOGY_DEVICE"
```

Then follow **steps 3-9 of the complete guide**, choosing its Bash blocks: stage the real datasets, fetch the provider checkpoints, extract all five feature sets, fit the heads, and export the reports. Skip that guide's venv/conda setup steps because the Nix route has already created separate environments and defined `head_python`, `vision_python` and `pathology_python`. `CBMP_FEATURE_DIR` defaults to `artifacts/features/full-reproduction` and the pathology device defaults to `cpu`.

Once all five feature caches exist, the fitting sequence is unchanged:

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

Planning only validates the inputs; the second command fits/selects the heads and evaluates them. The full run comprises 50 task/seed jobs and 3,080 target/head/seed metric cells. It keeps the pretrained encoders frozen.

Continue with the complete guide's Bash reporting and export commands. Record the runtime and package versions for this Nix run as well; provisioned Python patch versions can differ from the historical manuscript runtime even though the scientific package versions and requirements remain fixed.

## Validation scope

On 16 November 2026, the optional Nix shell passed its Linux classifier-environment check: **62 tests passed and 3 provider-runtime tests were skipped**, using Python 3.12.8, NumPy 1.26.4, SciPy 1.13.1 and scikit-learn 1.5.1. The recorded-summary hash check and CLI help check also passed, and the Python 3.10 runtime was available. The committed lock was reproduced without changes.

The optional CI workflow `.github/workflows/nix.yml` repeats these checks. The two feature-environment installation paths and a complete raw-image study have not been executed in this Nix validation. The three skipped tests require the separate provider dependencies. These checks do not certify a provider/GPU route. See `provenance/NIX_VALIDATION.json` for the recorded validation scope of this release.

## Troubleshooting

- **`nix: command not found`:** finish the official installation and reopen the Linux terminal.
- **Flakes disabled:** use the explicit `--extra-experimental-features 'nix-command flakes'` form above.
- **Untracked flake files in a Git checkout:** Nix only includes tracked files from a Git source. Use the committed release, or stage your local Nix files before testing your own changes.
- **Missing `.so` libraries:** run Python through this Nix shell; its library paths are part of the environment. The shell intentionally does not rely on a system Python or an activated conda environment.
- **Missing interpreter environment:** run `bash scripts/nix_setup.sh heads`, `vision`, or `pathology` as indicated by the message, then source `scripts/nix_env.sh` again.
- **Checkpoint access denied:** obtain the required provider approval and log in locally using the complete guide. Nix does not grant dataset or checkpoint access.
