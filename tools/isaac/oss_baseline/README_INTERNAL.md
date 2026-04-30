# Third-Party OSS Baseline + MR Gate (Internal)

> **NVIDIA-internal documentation.** Lives next to the script it documents and
> is intentionally named `README_INTERNAL.md` so it is recognizable as not for
> the public mirror. The whole `tools/isaac/` tree is also excluded from
> `repo_stage_for_github` (see
> [`repo_internal.toml`](../../../repo_internal.toml)).

Tracks every third-party Python package that ships in an Isaac Sim release
build and gates merge requests so a new dependency carrying a restrictive
license cannot land without an OSRB-cleared exception. Today this covers
Python (`.dist-info`) packages; packman / native packages are a follow-up.

## Files

| File | Purpose |
| --- | --- |
| [`generate_oss_baseline.py`](generate_oss_baseline.py) | Generator + checker. Two `repo` sub-commands: `generate_oss_baseline`, `check_oss_baseline`. |
| [`license_policy.toml`](license_policy.toml) | Allowed / restricted licenses + OSRB-cleared exceptions. |
| [`baseline.csv`](baseline.csv) | Committed snapshot of the current release dependencies. Diff target for the MR gate. |

## What "restrictive" means here

Anything in `restricted_licenses` of [`license_policy.toml`](license_policy.toml)
is treated as a blocker. Defaults: `GPL-*`, `LGPL-*`, `AGPL-*`, `SSPL-1.0`,
`BUSL-1.1`, `CC-BY-NC-*`. Adjust the list in code review if NVIDIA's policy
changes -- it is not auto-fetched.

For full context on what triggers OSRB review and how to file a ticket, see
the OSS + OSRB Confluence:
[OSS and OSRB](https://nvidia.atlassian.net/wiki/spaces/RP/pages/2584971471/OSS+and+OSRB).

## Scope: what we track vs. what we exclude

Isaac Sim's release tree contains Python packages from several origins; we
only want to gate on OSS that *this team* actually pulls in. The
`excluded_locations` list in [`license_policy.toml`](license_policy.toml)
drops everything under those top-level directories *before* classification,
so external-to-this-team packages cannot trigger regressions here.

Defaults:

| Excluded directory | Owned by | Why |
| --- | --- | --- |
| `kit/` | Omniverse Kit team | Python runtime + Kit-shipped wheels under `kit/python/lib/python3.12/site-packages/` and `kit/extscore/.../pip_registry/`. Tracked by Kit's own OSRB process. |
| `extscache/` | Mostly Kit / `omni.services.*` | Cached extension downloads that are not authored by Isaac Sim, e.g. `omni.services.pip_archive` and its pip_prebundle. |

Anything else (notably `exts/isaacsim.*/pip_prebundle/`, `extsDeprecated/`,
`extsInternal/`, `extsUser/`) stays in scope and is classified normally.

To add another excluded directory, append a plain top-level name to
`excluded_locations`. Match is by exact name or `"<name>/"` prefix; no
globs. Each generate / check run prints how many packages were dropped per
excluded directory, so reviewers can see the scoping at a glance.

## How the MR gate works

1. The build job produces `_build/linux-x86_64/release/`.
2. The CI job `check_oss_baseline` (in stage `check-externals`) runs:
   ```
   ./repo.sh check_oss_baseline --release-dir _build/linux-x86_64/release
   ```
3. The script walks every `*.dist-info` directory in the release tree,
   normalizes the license string, and diffs against `baseline.csv`.
4. For each `added` or `version_changed` row it asks the policy: is the
   normalized license `allowed`, an OSRB `exception`, `restricted`, or
   `unknown`?
5. **Restricted + no exception => the job exits non-zero.** Unknown licenses
   are warned about by default (configurable via `unknown_policy` in the
   policy file).
6. The job's `after_script` (template `.post_job_status_to_slack` in
   `.gitlab-ci.yml`) calls `tools/ci/dashboards/ci_dashboard.py slack
   --job-report`, which resolves the target channel via
   `--channel > $SLACK_CHANNEL > config routing > default`. The job sets
   `SLACK_CHANNEL=#isaac-sim-ci-mr` in its `rules:` for MR pipelines (both
   `merge_request_event` and downstream-of-MR `pipeline` source) so the post
   lands in [`#isaac-sim-ci-mr`](https://app.slack.com/client). On a protected
   push (e.g. `develop`), `SLACK_CHANNEL` is not set and the dashboard falls
   through to its default channel per
   [`tools/ci/dashboards/config_isaac_sim.yml`](../../ci/dashboards/config_isaac_sim.yml).
7. Artifacts uploaded for triage:
   - `oss_baseline_current.csv` -- this run's full snapshot.
   - `oss_baseline_diff.json` -- machine-readable summary (added / removed /
     version_changed / regressions / policy stats).

## Common workflows

### Regenerate the baseline locally (after a fresh release build)

```bash
# Build a release first (any of the standard repo build flows).
./repo.sh build -r linux-x86_64

# Refresh the snapshot AND overwrite the committed baseline.csv.
./repo.sh generate_oss_baseline --update-baseline

# Sanity check.
./repo.sh check_oss_baseline
# -> should exit 0 with "Regressions: 0".
```

The first commit of `baseline.csv` is empty (header only). Bootstrap it once
on `develop` after the rest of this MR lands and a clean release build is
available.

### Add an OSRB-cleared exception

1. File an OSRB nvbug using the template at
   <https://nvbugspro.nvidia.com/bug/2885977> (clone it, fill out the package
   name / version / license / justification). See the
   [OSS and OSRB Confluence](https://nvidia.atlassian.net/wiki/spaces/RP/pages/2584971471/OSS+and+OSRB)
   for what reviewers expect.
2. Once approved, add an entry to the `[[exceptions]]` array in
   [`license_policy.toml`](license_policy.toml):
   ```toml
   [[exceptions]]
   package = "your-package"                                       # REQUIRED
   license = "LGPL-3.0"                                            # the normalized identifier
   osrb_ticket = "https://nvbugspro.nvidia.com/bug/<your-bug-id>"  # REQUIRED for restricted-license entries
   version_pattern = "*"           # optional; or "1.2.*" to pin a major.minor
   comment = "Approved via OSRB on YYYY-MM-DD; <one-line context>."
   ```
3. Re-run `./repo.sh check_oss_baseline` locally to confirm the regression
   clears.

When is `osrb_ticket` required? The validator enforces it at policy-load time
based on what the entry could *shield*:

| Entry shape | `osrb_ticket` |
| --- | --- |
| `license` set to a `restricted_licenses` identifier (e.g. `LGPL-3.0`) | **Required** -- a missing or non-nvbug URL fails the MR gate immediately. |
| `license` unset (entry would match any license, including restricted) | **Required** -- conservative default; pin `license` to remove this requirement. |
| `license` set to an allowed identifier (e.g. `MIT`) | Optional. If set, format is still validated. Useful for documenting a tracked-but-cleared package. |

`package` is always required; format errors on `version_pattern`, `license`,
`comment`, or a malformed `osrb_ticket` are reported regardless. Errors
aggregate so a single load-time failure surfaces every offending
`[[exceptions]][N]` index in one shot.

### Investigate a CI failure

1. Open the failed `check_oss_baseline` job and download the artifacts.
2. Inspect `oss_baseline_diff.json`:
   - `summary.regressions` is the count.
   - The `regressions` array names each offending package, its normalized
     license, and the `reason` (`restricted_no_exception` or
     `unknown_license_blocked_by_policy`).
3. Resolve by either:
   - removing or replacing the dependency, or
   - filing an OSRB nvbug and adding an exception (see above), or
   - if the regression is due to an upstream version bump that's still
     allowed-licensed: regenerate the baseline (`--update-baseline`) and
     commit the new `baseline.csv`.

## CSV / policy schema

`baseline.csv` and `oss_baseline_current.csv` share one schema:

| Column | Notes |
| --- | --- |
| `name` | Package name as parsed from the `.dist-info` directory. |
| `version` | Version as parsed from the `.dist-info` directory. |
| `license` | Raw license string from the wheel METADATA (classifier or License field, with fallbacks). |
| `license_normalized` | SPDX-ish identifier produced by `normalize_license()` (`MIT`, `Apache-2.0`, `LGPL-3.0`, `UNKNOWN`, ...). |
| `location` | Relative path inside the release tree, with extension version suffixes stripped. |
| `classification` | `allowed` / `restricted` / `exception` / `unknown` per [`license_policy.toml`](license_policy.toml). |
| `osrb_ticket` | OSRB nvbug URL from the matching `[[exceptions]]` entry on `classification=exception` rows; empty everywhere else. A row with `classification=restricted` and an empty `osrb_ticket` is the one-glance "OSRB filing still needed" signal. |

## Follow-up work (out of scope for this MR)

- Add packman package coverage by extending
  [`tools/check_externals/new_check_externals.py`](../../check_externals/new_check_externals.py)
  to emit the same schema and feed the same diff machinery.
- Decide whether to flip `licensing.enabled = true` in
  [`repo.toml`](../../../repo.toml), which engages the closed-source
  `repo_licensing` packman package (currently v2.0.1 in
  [`deps/repo-deps-nv.packman.xml`](../../../deps/repo-deps-nv.packman.xml)).
