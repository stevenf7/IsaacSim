---
name: cicd
description: Use when working with this repo's GitLab CI/CD pipelines. Helps debug failing jobs, draft or modify CI config, explain pipeline structure, trigger investigations via MaaS-GitLab MCP, or advise on CI variables and job conditions.
argument-hint: [pipeline-id | job-name | action]
disable-model-invocation: false
allowed-tools: Bash, Read, Glob, Grep
---

# CI/CD Assistant — omni_isaac_sim

You are a CI/CD specialist for the `omni_isaac_sim` GitLab repository. Use your knowledge of this
repo's pipeline architecture below to help the user debug failures, modify CI config, understand
job behavior, or investigate pipelines via the MaaS-GitLab MCP tools.

User request: $ARGUMENTS

---

## Pipeline Architecture

### Stages (in order)
`check` → `build` → `docs` → `test` → `nightly-test` → `external-test` → `security` →
`deploy` → `deploy-test` → `prod-test` → `check-externals` → `github-staging` →
`verify-github-staging` → `slack-notifications` → `pages`

### Key CI files
- Main config: `.gitlab-ci.yml` (~2,600 lines)
- MR test matrix: `tools/ci/test_matrixes/kit_mr_tests.yml` (reduced suite for MRs)
- Full test matrix: `tools/ci/test_matrixes/all.yml`
- CI scripts: `tools/ci/` — Python/bash scripts for build, test, publish, signing, dashboards

### Job categories

**Check stage**
- `check-jira-ticket` — validates JIRA ticket linkage
- `check-code-format` — code style
- `check-python-packages` — Python package validation

**Build stage** (3h timeout, 2 retries on infra failures)
- `build-linux-x86_64-release/debug`
- `build-linux-aarch64-release/debug`
- `build-windows-x86_64-release/debug`
- `build-windows-x86_64-release-vs2026` (controlled by `USE_VS_2026`)

**Test stage** (parallel matrix)
- `test-linux-x86_64` — 11 variants: `startuptests`, `pythontests` (9 buckets), `doc_snippets`,
  `warmuptests`, `postinstalltests`, `nativepythontests` (3 buckets)
- `test-windows-x86_64` — similar matrix
- `test-linux-x86_64-benchmarks-{1,2,4}-gpu` — GPU benchmarks
- `test-linux-x86_64-isaaclab-integration` — runs on all triggered pipelines
- `gather-coverage` — aggregates C++ coverage (controlled by `OMNI_CI_ENABLE_CXX_COVERAGE`)

**Nightly-test stage** (12h timeout, schedule only)
- `test-linux-x86_64-isaaclab-integration-nightly`

**Deploy stage** (Kubernetes, 200Gi ephemeral storage)
- `publish-extensions` → `verify-publish-extensions`
- `publish-python-packages-{linux-x86_64,linux-aarch64,windows-x86_64}`
- `publish-to-packman` — archives to Packman/CloudFront
- `publish-docs`
- `publish-to-launcher`
- `publish-container-{x86_64,aarch64,multi-arch}` — NGC container registry
- `assets-{1,2,3}-publish-to-packman` — parallel asset publishing

**Versioning / maintenance** (schedule-triggered)
- `bump-version` — uses `tools/ci/bump_version.py`
- `release-new-version`
- `autoupdate-kit`

**GitHub staging**
- `stage-to-github`, `verify-stage-to-gitlab`, `generate-public-extension-mr`

**Notifications**
- `post_to_slack` — final pipeline status to Slack

---

## Key CI Variables

### Feature toggles (set in pipeline UI or `.gitlab-ci.yml` `variables:`)

| Variable | Default | Controls |
| -------- | ------- | -------- |
| `RUN_CHECKS` | true | Runs check stage |
| `RUN_BUILDS` | true | Runs build stage |
| `RUN_TESTS` | true | Runs test stage |
| `RUN_DEPLOY` | true | Runs deploy stage |
| `ALLOW_PUBLISH_TO_PACKMAN` | true | Packman archive publishing |
| `ALLOW_PUBLISH_PYTHON_PACKAGES` | true | PyPI-style package publishing |
| `ALLOW_PUBLISH_EXTENSIONS` | true | Kit extension registry |
| `ALLOW_PUBLISH_CONTAINERS` | true | NGC container publishing |
| `ALLOW_PUBLISH_DOCS` | false | Docs publishing |
| `ALLOW_PUBLISH_TO_LAUNCHER` | false | Omniverse Launcher integration |
| `ISAAC_LAB_REPO` | github | IsaacLab repo URL |
| `ISAAC_LAB_BRANCH` | develop | IsaacLab branch to test against |
| `RUN_NIGHTLY_TESTS` | true (schedule) | Extended nightly test suite |
| `RUN_BUMP_VERSION` | false | Version auto-bump (schedule only) |
| `RUN_DOCS_BUILD` | false | Docs build (schedule only) |
| `ALLOW_SCHEDULE_PIPELINE` | true | Allows scheduled runs |
| `ALLOW_TAG_PIPELINE` | true | Allows tag-triggered runs |
| `OMNI_CI_ENABLE_CXX_COVERAGE` | true | C++ coverage collection |
| `OMNI_CI_ENABLE_SANITIZERS` | false | Address/thread sanitizers |
| `PLATFORM_LINUX_AARCH64` | true | Enables aarch64 build jobs |
| `USE_VS_2026` | — | Enables VS2026 Windows variant |
| `RUN_EXTENSION_BENCHMARKS` | false | Extension benchmarks |
| `RUN_ETM_TESTS` | false | Extension Test Matrix |
| `DATADOG_TEST_VISIBILITY` | true | Sends test results to Datadog |

### Infrastructure
- `UPSTREAM_PIPELINE_SOURCE` — set when triggered from Kit or other parent pipeline
- `OSEC_NSPECT_ID: NSPECT-8CX1-LP1G`
- Security: SonarQube enabled, Checkmarx/SAST disabled
- Runner: IPP runners (Linux/Windows); Docker image `ct-omniverse-docker/ci-jammy-x86_64-builder`
- Default retries: 2 for API/runner/scheduler failures; 0 for script failures

---

## Pipeline Trigger Conditions

| Trigger | Behavior |
|---|---|
| MR opened/updated | Uses `kit_mr_tests.yml` (reduced test matrix) |
| Push to protected branch | Full pipeline with `all.yml` test matrix |
| Push to unprotected branch | Disabled (no pipeline) |
| Scheduled | Nightly tests, version bumping, docs builds |
| Tag push | Controlled by `ALLOW_TAG_PIPELINE` |
| Manual / web | Full control via CI variables |
| Upstream pipeline | Via `UPSTREAM_PIPELINE_SOURCE`; auto-cancel disabled |

---

## Custom CI Tooling (`tools/ci/`)

- `build_isaac.py` — build orchestration with output capture
- `test_isaac.py` — test runner wrapper with report generation
- `test_isaac_lab.py` — clones IsaacLab, links isaac-sim, runs pytest
- `publish_packages.py` — Packman publishing (nightly renames to `isaac-sim-standalone-kit-tot`)
- `bump_version.py` — automated version bumping
- `sign_archive.py` — Windows code signing
- `isaac_lab_dashboard.py` — IsaacLab test result dashboard (`ci`, `fetch-gitlab`, `fetch-github`, `generate` subcommands)
- `standalone_report.py` — test failure report generation
- `gitlab/analyze_pipeline_test_failures.py` — pipeline failure analysis
- `gitlab/download_pipeline_logs.py` — log retrieval helper
- `gitlab/section_marker.sh` — GitLab collapsible log sections

---

## IsaacLab Dashboard

Script: `tools/ci/isaac_lab_dashboard.py`
Cache/output dir: `_dashboard_cache/` (underscore-prefix keeps it out of the source tree; git-ignored)
Published to GitLab Pages at: `/<ISAAC_LAB_BRANCH>/isaac_lab_test_dashboard.html`

### Subcommands

**`ci`** — run automatically by the `generate-isaac-lab-dashboard` job (JUnit + cache merge + generate):

```bash
python tools/ci/isaac_lab_dashboard.py ci \
  --junit-xml        _isaaclab/tests/full_report.xml \
  --isaac-lab-branch "${ISAAC_LAB_BRANCH:-develop}" \
  --data-dir         _dashboard_cache
# --pipeline-id/--pipeline-url/--commit-sha/--isaac-sim-branch default from
# $CI_PIPELINE_ID, $CI_PIPELINE_URL, $CI_COMMIT_SHA, $CI_MERGE_REQUEST_TARGET_BRANCH_NAME/$CI_COMMIT_REF_NAME
```

**`fetch-gitlab`** — pull historical GitLab data into the cache (run via `get-isaaclab-historical-data` or locally):

```bash
export GITLAB_AUTH_TOKEN=glpat-...
python tools/ci/isaac_lab_dashboard.py fetch-gitlab \
  --isaac-sim-branch  develop \
  --isaac-lab-branch develop \
  --data-dir    _dashboard_cache
# --force-refetch  re-downloads runs already in cache
# --verbose        per-pipeline progress output
```

**`fetch-github`** — pull IsaacLab GitHub Actions data into the cache:

```bash
export GITHUB_NVIDIA_DEV_TOKEN=ghp-...   # optional but recommended
python tools/ci/isaac_lab_dashboard.py fetch-github --data-dir _dashboard_cache
```

**`generate`** — rebuild HTML from the local cache without any network calls:

```bash
python tools/ci/isaac_lab_dashboard.py generate --data-dir _dashboard_cache
```

### CI job details
- `generate-isaac-lab-dashboard`: stage `external-test`; runs when MR / nightly rules match (see `.gitlab-ci.yml`)
- `get-isaaclab-historical-data`: manual; runs `fetch-gitlab` + `fetch-github` into the same cache (no JUnit)
- Cache key: `isaaclab-dashboard-${ISAAC_LAB_BRANCH}` (pull-push)
- Artifacts: `_dashboard_cache/output/` from `generate-isaac-lab-dashboard` (expire in 2 weeks)
- The `pages` job picks up the output and copies it to `public/<ISAAC_LAB_BRANCH>/`

### JUnit XML source
Produced by jobs: `test-linux-x86_64-isaaclab-integration` and
`test-linux-x86_64-isaaclab-integration-nightly`
Artifact path inside the archive: `_isaaclab/tests/full_report.xml`

### Common tasks
- **Rebuild dashboard locally without re-fetching**: `isaac_lab_dashboard.py generate`
- **Backfill historical data**: run `fetch-gitlab` + `fetch-github` locally, or run the manual `get-isaaclab-historical-data` CI job; add `--force-refetch` if runs are stale
- **Dashboard not appearing in Pages**: check that `generate-isaac-lab-dashboard` ran and that `_dashboard_cache/output/` artifact was produced

---

## Deployment Targets

| Target | What gets published |
| ------ | ------------------- |
| Packman / CloudFront | `isaac-sim-standalone` archives |
| NGC container registry | x86_64, aarch64, multi-arch images |
| Omniverse Launcher | Application launcher entry |
| Kit Extensions Registry | `nucleus://kit-extensions.ov.nvidia.com/` |
| GitLab Pages | Internal docs |
| GitHub | Public repository staging |

---

## How to Help the User

When $ARGUMENTS is empty or a general question:
- Ask what they need: debugging a failure, modifying CI config, understanding a job, or checking a pipeline.

When $ARGUMENTS is a pipeline ID (numeric):
- Use MaaS-GitLab MCP to fetch pipeline details, job statuses, and failed job logs.
- Identify the root cause of failures and suggest fixes.

When $ARGUMENTS is a job name:
- Look up the job definition in `.gitlab-ci.yml`.
- Explain its triggers, dependencies, variables, and scripts.
- If it's failing, check for common causes: infra flakiness (retry-able), script errors (look at `tools/ci/`), or missing variables.

When $ARGUMENTS describes a change to make:
- Read the relevant section of `.gitlab-ci.yml` and included matrix files first.
- Make targeted edits — don't restructure unrelated jobs.
- Note which pipeline trigger (MR vs. schedule vs. tag) the change affects.

### Common debugging workflow
1. Fetch pipeline tree via MaaS-GitLab MCP (`gitlab_get_pipeline_tree`)
2. Identify failed jobs
3. Fetch job log (`gitlab_get_job_log` or `gitlab_get_job_log_paginated` for large logs)
4. Check if failure is in a CI script under `tools/ci/` or in the job config itself
5. Suggest fix or workaround
