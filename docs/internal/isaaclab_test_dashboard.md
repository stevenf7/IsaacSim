# IsaacLab Integration Test Dashboard

**Internal only — not part of the Isaac Sim public documentation.**

The IsaacLab test dashboard is a self-contained HTML page that shows the historical
results of the `test-linux-x86_64-isaaclab-integration` CI job across Isaac Sim
branches, alongside data pulled from the IsaacLab GitHub Actions workflows.  It is
generated automatically by the CI pipeline and published to GitLab Pages.

---

## How it works

### Data sources

| Tab | Source |
|-----|--------|
| **Isaac Sim CI** (one per branch) | `test-linux-x86_64-isaaclab-integration` job artifacts (`_isaaclab/tests/full_report.xml`) fetched from GitLab pipelines on the configured Isaac Sim branches |
| **GitHub → Pull Requests** | IsaacLab GitHub Actions `build.yml` workflow — runs on every PR to the IsaacLab repo |
| **GitHub → Nightly Runs** | IsaacLab GitHub Actions `daily-compatibility.yml` — nightly backwards-compatibility runs against multiple Isaac Sim versions |

### Pipeline flow

```text
test-linux-x86_64-isaaclab-integration
  └─ produces _isaaclab/tests/full_report.xml (JUnit XML)

get-isaaclab-historical-data  (manual / on_success in triggered pipelines)
  ├─ fetches GitLab historical data for each branch in ISAAC_LAB_CI_REPORT_BRANCHES
  ├─ fetches GitHub build + compat workflow data
  └─ writes everything to _dashboard_cache/  (GitLab cache)

generate-isaac-lab-dashboard  (runs after the isaaclab test job)
  ├─ reads historical data from _dashboard_cache/ (artifact from above job, or cache)
  ├─ merges the current pipeline's JUnit XML into the cache
  └─ writes _dashboard_cache/output/
       ├─ isaac_lab_test_dashboard.html
       └─ data/data.js

pages
  └─ copies _dashboard_cache/output/ → public/<ISAAC_LAB_BRANCH>/
```

### Cache and storage

- **GitLab cache key**: `isaaclab-dashboard-${ISAAC_LAB_BRANCH}` (pull-push).
  Persists the `_dashboard_cache/` directory between pipeline runs so historical
  data accumulates without re-fetching every time.
- **Per-run test data**: stored as individual JSON files under
  `_dashboard_cache/<isaac-sim-branch>/tests/<pipeline-id>.json`.
- **GitHub data**: stored under `_dashboard_cache/github/`.
- **Dashboard output**: `_dashboard_cache/output/` (artifact from
  `generate-isaac-lab-dashboard`, expires in 2 weeks).

---

## Where the dashboard is published

The `pages` job copies the generated output to GitLab Pages:

```
https://omniverse.gitlab-master-pages.nvidia.com/-/isaac/omni_isaac_sim/-/jobs/<job-id>/artifacts/public/<ISAAC_LAB_BRANCH>/isaac_lab_test_dashboard.html
```

`ISAAC_LAB_BRANCH` defaults to `develop`.  When the nightly schedule runs with a
different `ISAAC_LAB_BRANCH`, a separate page is published under that branch's path.

---

## CI jobs

### `test-linux-x86_64-isaaclab-integration`

Runs on all triggered pipelines, MR pipelines, and nightly schedules.
Clones the IsaacLab repo, links the Isaac Sim build, installs dependencies, and runs
`pytest tools -m isaacsim_ci`.  Produces `_isaaclab/tests/full_report.xml`.

### `generate-isaac-lab-dashboard`

Runs on:
- Any MR pipeline
- All triggered pipelines
- Nightly schedules

Reads the JUnit XML from the current pipeline (if the isaaclab test job ran) and
merges it into the accumulated cache from `get-isaaclab-historical-data`.  The current
pipeline's run is flagged as `is_ci_run` and rendered as the first (highlighted) column
in the heatmap.

The `--isaac-sim-branch` argument is set to `$CI_MERGE_REQUEST_TARGET_BRANCH_NAME` for
MR pipelines (so MR results appear alongside the target branch's historical data) and
to `$CI_COMMIT_REF_NAME` for all other pipeline types.

### `get-isaaclab-historical-data`  _(manual, or on_success in triggered pipelines)_

Fetches historical test data from GitLab and GitHub APIs and writes it into
`_dashboard_cache/`.  Requires the following CI variables to be set as masked/protected
secrets:

| Variable | Description |
|----------|-------------|
| `GITLAB_AUTH_TOKEN` | GitLab PAT with `read_api` scope |
| `GITHUB_NVIDIA_DEV_TOKEN` | GitHub PAT with `repo` scope (optional but recommended) |

Iterates over each branch listed in `ISAAC_LAB_CI_REPORT_BRANCHES` for the GitLab
fetch.  A failed fetch for one branch increments `ERR_COUNT` but does not abort the
remaining branches.

---

## Configuration

### `ISAAC_LAB_CI_REPORT_BRANCHES`

Defined in the `.isaaclab-dashboard-cache` template in `.gitlab-ci.yml`.  Newline-
separated list of Isaac Sim branches whose historical GitLab pipelines are fetched
and shown in the **Isaac Sim** dropdown:

```yaml
ISAAC_LAB_CI_REPORT_BRANCHES: |
    develop
    develop-kit-tot
    kit-integration/master
    kit-integration/feature/110.0
    kit-integration/feature/110.1
    kit-integration/production/110.0
```

Override at runtime by setting `ISAAC_LAB_CI_REPORT_BRANCHES` in the GitLab pipeline
variables UI (Run pipeline → Variables) with a newline-separated list.

### `ISAAC_LAB_BRANCH`

Controls which IsaacLab branch is checked out for testing and which cache key and
Pages subdirectory are used.  Defaults to `develop`.

---

## Running locally

Use `tools/ci/dashboard_fetch_local.sh` to replicate what `get-isaaclab-historical-data`
does without waiting for a pipeline:

```bash
export GITLAB_AUTH_TOKEN="glpat-..."          # required (or GITLAB_TOKEN / GITLAB_API_TOKEN)
export GITHUB_NVIDIA_DEV_TOKEN="ghp_..."      # optional (or GITHUB_TOKEN / GITHUB_API_TOKEN)
export ISAAC_SIM_BRANCH="develop"             # default: develop
export ISAAC_LAB_BRANCH="develop"             # default: develop
export DASHBOARD_MAX_RUNS=5                   # default: 5 (keep low for quick runs)
./tools/ci/dashboard_fetch_local.sh
```

The script:
1. Creates (or reuses) a `.ci-dashboard-venv/` virtualenv with `requests` installed.
2. Runs `isaac_lab_dashboard.py fetch-gitlab` then `fetch-github` with the configured
   tokens and branches.
3. Runs `isaac_lab_dashboard.py generate` to write
   `_dashboard_cache/output/isaac_lab_test_dashboard.html`.

Open the generated HTML file directly in a browser — it is fully self-contained
(data is embedded as a `data/data.js` script loaded from the same directory).

To regenerate the HTML from an existing cache without any network calls:

```bash
python tools/ci/isaac_lab_dashboard.py generate --data-dir _dashboard_cache
```

---

## Source files

| Path | Purpose |
|------|---------|
| `tools/ci/isaac_lab_dashboard.py` | Main script: `ci`, `fetch-gitlab`, `fetch-github`, `generate` subcommands |
| `tools/ci/test_isaac_lab.py` | CI test runner: clones IsaacLab, runs pytest, produces JUnit XML |
| `tools/ci/dashboard_fetch_local.sh` | Convenience wrapper for local historical fetching |
| `tools/ci/verify_dashboard_api_tokens.py` | Token connectivity check used by CI |
| `tools/dashboard/isaac_lab/index.html` | Dashboard HTML template (static; data loaded from `data/data.js`) |
| `tools/ci/tests/test_isaac_lab_dashboard.py` | Unit tests for pure-logic parsing functions |
