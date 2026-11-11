# Upload the extracted project to GitHub

Use this **clean repository folder**, not the original large research workspace.
The extraction has no copied `.git` history, credentials, images, feature binaries,
checkpoints or full run folders. Runtime artifacts are ignored by `.gitignore`.

## 1. Create an empty repository

On GitHub choose **New repository**, name it for example `cbmp-cvpr-paper`, and
choose its visibility. Leave initialization with README, .gitignore and license
unchecked because this local project already has its tracked files. Select the
intended code license separately; this extraction has not assigned one. Preserve
review anonymity when deciding whether and where to publish identifying details.

GitHub's official guide:
https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github

## 2. Initialize and upload: PowerShell

Open PowerShell in the clean folder. Replace the path and both URL placeholders:

```powershell
Set-Location -LiteralPath 'C:\path\to\CBMP_CVPR2027'
git init -b main
git add .
git status --short
git commit -m "Add reproducible CVPR paper implementation"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

Review `git status --short` before committing. It should list source code,
manifests, configs, tests, small reference summaries and paper files, not virtual
environments, artifacts or images. The source hashes depend on `.gitattributes`;
keep it in the first commit.

If Git requests an author identity, set it for this local repository:

```powershell
git config user.name "Your Name"
git config user.email "YOUR_GITHUB_NOREPLY_EMAIL"
```

Then repeat the commit/push commands. Use the normal browser/Git Credential
Manager authentication prompt. GitHub account passwords are not HTTPS Git
credentials; use its supported authentication flow. Do not put a token in the
remote URL, code or README. No remote repository is created or pushed by extracting
this package; the commands above are for the owner to execute.

## 3. Linux / Bash

```bash
cd /path/to/CBMP_CVPR2027
git init -b main
git add .
git status --short
git commit -m "Add reproducible CVPR paper implementation"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

Use a new empty GitHub repository for these steps. If the destination already
contains commits, clone it separately and copy this clean project's files into
that checkout, then review and commit normally. Do not force-push over an existing
project to work around a history conflict.

## 4. After upload

Check that README renders, the source files are present, and the **Actions** tab
shows the Windows/Linux test results. The optional model-loader tests skip in CI
without the separate torch/provider environment. Large caches/results belong in
an appropriately authorized release artifact or dataset service, not Git history.
The small `results/paper/` summaries intentionally remain tracked.

For subsequent edits:

```bash
git add .
git diff --cached --stat
git commit -m "Describe the change"
git push
```
