# pipx Release + Clean Install Runbook

## Goal
Install PyTestFlow with one command:

```powershell
pipx install "git+https://github.com/Alberto-Manzoni/PyTestFlow.git"
```

Source repositories:
- Engine: https://github.com/Alberto-Manzoni/PyTestFlow
- Frontend: https://github.com/Alberto-Manzoni/PyTestFlow-FrontEnd

This package includes both backend code and frontend static assets (`pytestflow/backend/frontend`).

## 1) Sync frontend build into this repo

From this repo root:

```powershell
# If your frontend dist is in the sibling repo default location:
.\scripts\sync_frontend_dist.ps1

# Or with explicit path:
.\scripts\sync_frontend_dist.ps1 -FrontendDist "C:\path\to\PyTestFlow-FrontEnd\dist"
```

## 2) Commit and push

```powershell
git add setup.py MANIFEST.in pytestflow\backend\frontend scripts docs
git commit -m "Bundle frontend assets for pipx install"
git push
```

## 3) User install command

```powershell
pipx install "git+https://github.com/Alberto-Manzoni/PyTestFlow.git"
pytestflow-am start
```

## 4) Clean-environment smoke test

Run this from repo root to simulate a fresh install in an isolated pipx venv:

```powershell
.\scripts\test_clean_install.ps1 -PackageSpec "git+https://github.com/Alberto-Manzoni/PyTestFlow.git"
```

For local/offline smoke test from current checkout:

```powershell
.\scripts\test_clean_install.ps1
```

What this test verifies:
- installs package with `pipx` into a dedicated environment
- CLI command exists (`pytestflow-am-<suffix>`)
- `quickstart` command works and copies `starter_here.md`
- backend starts and prints startup banner
- test environment is removed at the end
