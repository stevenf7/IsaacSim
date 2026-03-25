# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Arbitration for whether to use upstream Kit and launching the prepare step.

This module decides if the current run should use Kit artifacts from an upstream
GitLab pipeline (downstream trigger or develop-kit-tot / kit-integration/* branch),
resolves the pipeline ID (or finds the latest nightly), and launches
prepare_kit_overrides to download artifacts and generate packman overrides.

It does not perform the actual artifact fetching; that lives in pull_kit and
prepare_kit_overrides.

Config for artifact selection comes from the caller (build_config). Platform is
auto-detected by prepare_kit_overrides via repo_man when we launch it.
"""

import os

from tools.ci.upstream_kit_build.pull_kit import KIT_BRANCH, find_latest_nightly_pipeline_id


def arbitrate_kit_upstream(build_config: str | None = None) -> None:
    """Detect whether this build should use upstream Kit and set up accordingly.

    Decision matrix:
      1. Downstream trigger from Kit (CI_PIPELINE_SOURCE == "pipeline") with
         UPSTREAM_PIPELINE_ID already set → honor it directly.
      2. Running on the develop-kit-tot or kit-integration/* branch (post-merge push, scheduled, or
         MR targeting it) → fall back to the latest Kit nightly on the effective branch.
      3. Otherwise → skip Kit override entirely.

    When an upstream Kit pipeline is identified (case 1 or 2), this function
    launches ``prepare_kit_overrides`` which downloads Kit artifacts and
    generates packman ``.user`` overrides so all Kit packages come from the
    same commit.

    Config for which artifacts to pull comes from the caller (build_config).
    Platform is auto-detected by prepare_kit_overrides via repo_man.
    """
    import omni.repo.ci  # deferred so module can be imported outside CI

    config = build_config if build_config is not None else "release"
    print(f"[arbitrate_kit_upstream] config={config} (caller); prepare_kit_overrides will auto-detect platform")

    ci_pipeline_source = os.getenv("CI_PIPELINE_SOURCE", "")
    ci_commit_ref = os.getenv("CI_COMMIT_REF_NAME", "")
    ci_mr_target = os.getenv("CI_MERGE_REQUEST_TARGET_BRANCH_NAME", "")
    upstream_pipeline_id = os.getenv("UPSTREAM_PIPELINE_ID", "")

    print(f"[arbitrate_kit_upstream] CI_PIPELINE_SOURCE={ci_pipeline_source}")
    print(f"[arbitrate_kit_upstream] CI_COMMIT_REF_NAME={ci_commit_ref}")
    print(f"[arbitrate_kit_upstream] CI_MERGE_REQUEST_TARGET_BRANCH_NAME={ci_mr_target}")
    print(f"[arbitrate_kit_upstream] UPSTREAM_PIPELINE_ID={upstream_pipeline_id}")

    downstream_pipeline = ci_pipeline_source == "pipeline"
    develop_kit_tot_pipeline = (
        ci_mr_target == "develop-kit-tot"
        or ci_commit_ref == "develop-kit-tot"
        or ci_commit_ref.startswith("kit-integration/")
        or ci_mr_target.startswith("kit-integration/")
    )

    # For kit-integration/* use the branch name from the ref for nightly lookup.
    kit_branch = KIT_BRANCH
    if ci_commit_ref.startswith("kit-integration/"):
        kit_branch = ci_commit_ref.removeprefix("kit-integration/")
    if ci_mr_target.startswith("kit-integration/"):
        kit_branch = ci_mr_target.removeprefix("kit-integration/")

    print(
        f"[arbitrate_kit_upstream] downstream_pipeline={downstream_pipeline}, "
        f"develop_kit_tot_pipeline={develop_kit_tot_pipeline}"
    )

    if downstream_pipeline and upstream_pipeline_id:
        # Upstream pipeline already provided the pipeline ID — honour it.
        print(f"[arbitrate_kit_upstream] Using upstream-provided UPSTREAM_PIPELINE_ID={upstream_pipeline_id}")
    elif develop_kit_tot_pipeline:
        # Fallback: find the latest Kit nightly on the effective branch.
        print(f"[arbitrate_kit_upstream] No upstream pipeline ID, falling back to latest Kit nightly on {kit_branch}")
        nightly_pipeline_id = find_latest_nightly_pipeline_id(branch=kit_branch)
        if nightly_pipeline_id is None:
            raise ValueError("Unable to find latest nightly pipeline")
        os.environ["UPSTREAM_PIPELINE_ID"] = str(nightly_pipeline_id)
        print(f"[arbitrate_kit_upstream] Set UPSTREAM_PIPELINE_ID={nightly_pipeline_id} from nightly lookup")
    else:
        print(
            "[arbitrate_kit_upstream] Not a downstream or develop-kit-tot/kit-integration pipeline, skipping Kit override"
        )
        return

    print("[arbitrate_kit_upstream] Launching prepare_kit_overrides to override Kit packages...")
    omni.repo.ci.launch(["${root}/repo${shell_ext}", "prepare_kit_overrides", "--config", config])
