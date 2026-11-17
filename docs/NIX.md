# Optional Nix setup

Use the same Python 3.11 reviewer commands inside the pinned Nix development shell. This remains optional; [venv and conda instructions](REPRODUCE_ALL.md) are independent choices.

```bash
nix develop --command python reproduce.py setup --manager venv
nix develop --command python reproduce.py check
nix develop --command python reproduce.py run --features /path/to/paper-features
```

If flakes are disabled, add `--extra-experimental-features 'nix-command flakes'` after `nix`. Install Nix following the [official Linux/WSL2 instructions](https://nixos.org/download/). This shell targets x86_64 Linux/WSL2; it does not add native Windows or macOS support.

For image reconstruction use `setup --manager venv --features` inside the same shell, then follow the complete guide. CPU is the default. Nix does not grant provider access or guarantee bitwise agreement across hardware.

Scientific packages use the same portable reviewer requirements as the other routes. The Nix input remains pinned for provenance. The measured validation scope is in `provenance/REVIEWER_REPRODUCTION.json`; historical records describe earlier releases.
