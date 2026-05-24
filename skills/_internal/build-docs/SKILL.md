---
name: build-docs
description: Build Isaac Sim documentation (user guide, API docs, or both), serve locally for preview, and run pre-commit formatting. Use when the user asks to build docs, preview docs, serve docs, view documentation changes, or prepare docs for commit.
---

# Build Isaac Sim Documentation

## Prerequisites

A successful `./build.sh` (Linux) or `build.bat` (Windows) is required before building docs. Verify by checking that these exist:

- **Linux**: `_repo/python/python3` and `_build/linux-x86_64/release/kit/python/python3`
- **Windows**: `_repo\python\python.exe` and `_build\windows-x86_64\release\kit\python\python.exe`

If missing, tell the developer to run the main build first.

## Full Docs Build

Builds everything: doxygen input, extension docs, extension TOC, user guide, API docs, and examples list.

```bash
# Linux
./tools/build_docs.sh

# Windows
.\tools\build_docs.bat
```

The full build takes significant time. Prefer partial builds below when iterating on specific content.

## Partial Builds

Use these when only part of the docs changed. All commands run from the repo root.

### User Guide Only

For changes to RST/MD files under `docs/`:

```bash
# Linux — capture full log to a file, then pull warnings/errors from it (single build)
./repo.sh docs --project isaac-sim -c release --warn-as-error=0 2>&1 | tee /tmp/docs_build.log | tail -5
grep -nE "WARNING|ERROR" /tmp/docs_build.log || true

# Windows
repo.bat docs --project isaac-sim -c release --warn-as-error=0
```

DO NOT run the build twice just to filter warnings — pipe to `tee` and grep the saved log. Builds take ~2-3 minutes; rerunning wastes time.

### Fast Incremental User Guide Rebuild

After one successful user-guide build, use this faster Sphinx-only loop while iterating on RST/MD page content:

```bash
# Linux — reuses installed docs deps and existing Sphinx output
./repo.sh docs --project isaac-sim -c release --stage sphinx --no-clean --no-install --warn-as-error=0 2>&1 | tee /tmp/docs_incremental.log | tail -5
grep -nE "WARNING|ERROR" /tmp/docs_incremental.log || true

# Windows
repo.bat docs --project isaac-sim -c release --stage sphinx --no-clean --no-install --warn-as-error=0
```

Use the normal user-guide command above for the first build, after changing Sphinx config/theme files, after changing generated API/extension docs inputs, or whenever the incremental build appears stale. `--stage sphinx` skips clean and Doxygen stages; `--no-clean` keeps the previous output; `--no-install` assumes docs dependencies are already installed. A warm no-op rebuild should finish quickly and may report `no targets are out of date`.

### API Docs Only

For changes to extension API docstrings or `docs/api/`:

```bash
# Linux — doxygen + extension metadata must be generated first
./repo.sh generate_doxygen_input
./repo.sh extension_docs --error-as-warn
./repo.sh extension_toc --error-as-warn
./repo.sh docs --project api -c release --warn-as-error=0 2>&1 | tee /tmp/api_docs_build.log | tail -5
grep -nE "WARNING|ERROR" /tmp/api_docs_build.log || true

# Windows
repo.bat extension_docs --error-as-warn
repo.bat extension_toc --error-as-warn
repo.bat docs --project api -c release --warn-as-error=0
```

### Extension Docs / TOC Only

For changes to extension `docs/` folders (CHANGELOG, Overview, api.rst, etc.):

```bash
# Linux
./repo.sh extension_docs --error-as-warn
./repo.sh extension_toc --error-as-warn

# Windows
repo.bat extension_docs --error-as-warn
repo.bat extension_toc --error-as-warn
```

## Preview Docs Locally

After building, serve the HTML output with the helper script:

```bash
# Linux (default port 8000)
bash skills/_internal/build-docs/scripts/serve_docs.sh

# Linux (custom port)
bash skills/_internal/build-docs/scripts/serve_docs.sh 9000

# Windows
skills\_internal\build-docs\scripts\serve_docs.bat
skills\_internal\build-docs\scripts\serve_docs.bat 9000
```

The server serves `_build/docs/isaac-sim/latest/` at `http://localhost:<port>`.
API docs are at `http://localhost:<port>/py/`.

When running from the agent, background the server process so the terminal stays usable, then tell the developer the URL.

## MR Docs Media Checks

Two lightweight MR jobs protect docs media:

- `check-docs-image-filenames` validates changed docs image/video filenames against the Isaac Sim naming convention.
- `check-docs-unused-assets` runs on every MR, but only checks added/copied/modified/renamed media under `docs/isaacsim/images`. Existing unused assets do not fail the job unless the MR touches them.

To reproduce both checks locally against the target branch:

```bash
git fetch upstream develop
git diff --name-only --diff-filter=ACMR upstream/develop...HEAD > /tmp/docs_changed_files.txt
grep '^docs/' /tmp/docs_changed_files.txt > /tmp/docs_only_changed_files.txt || true
python3 docs/tools/validate_filenames/validate_filenames.py --files-from /tmp/docs_only_changed_files.txt
python3 docs/tools/check_unused_assets/check_unused_assets.py --files-from /tmp/docs_changed_files.txt
```

If `check-docs-image-filenames` fails, rename the changed media file to the required `isim_<VERSION_NUM>_<APP_TYPE>_<DOC_TYPE>_<APP_VIEW>_<YOUR_FILE_NAME>.<ext>` pattern and update every RST reference.

If `check-docs-unused-assets` fails, either reference the changed media from an RST page, remove it from the MR, or move it outside `docs/isaacsim/images` if it is not user-guide media. The full manual scan (`./docs/check_unused_assets.sh`) may report existing backlog items; do not treat those as MR blockers unless they are changed by the MR.

## Pre-Commit: Format Code

**CRITICAL**: Always run the formatter before committing docs changes. CI will reject unformatted code.

```bash
# Linux
./format_code.sh

# Windows
.\format_code.bat
```

## Workflow Summary

When a developer asks to build or preview docs:

1. **Check prerequisites** — confirm `./build.sh` has been run
2. **Determine scope** — ask what changed to pick full vs partial build
3. **Run the build** — use the appropriate command(s) above; pipe to `tee` and grep the saved log for warnings (single build, no double-run)
4. **Read built HTML to verify edits** — the docs output dir (`_build/docs/...`) is owned by the user account and lives outside Cursor's default sandbox read scope. Reading it from the agent requires elevated permissions (`required_permissions: ["all"]`); plain `ls` / `grep` will report "No such file or directory" without those permissions. The directory exists; trust the build success message rather than re-running the build.
5. **Start the preview server** — background it and share the URL
6. **Remind about formatting** — before any commit, run the formatter
