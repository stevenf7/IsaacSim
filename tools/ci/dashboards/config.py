# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

"""Dashboard YAML configuration loader and accessor helpers."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

try:
    import yaml  # pyyaml
except ImportError:
    yaml = None  # type: ignore[assignment]


def load_config(path: str | None) -> dict:
    """Load dashboard config from a YAML file.

    Returns an empty dict if *path* is None, the file does not exist, or
    *pyyaml* is not installed (all existing behaviour is preserved).
    """
    if not path:
        return {}
    if yaml is None:
        print(
            "Warning: pyyaml not installed; config file will be ignored. "
            "Install with: pip install pyyaml",
            file=sys.stderr,
        )
        return {}
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        print(f"Warning: config file not found: {path}", file=sys.stderr)
        return {}
    except Exception as exc:
        print(f"Warning: failed to load config {path}: {exc}", file=sys.stderr)
        return {}


def _cfg_channel_id_map(config: dict) -> dict[str, str]:
    """Return the Slack channel name->ID map from config."""
    return dict(config.get("slack", {}).get("channels", {}))


def _cfg_kit_project_id(config: dict) -> str:
    """Return the Kit upstream GitLab project ID from config."""
    return str(config.get("slack", {}).get("heatmap", {}).get("upstream_project_id", "6510"))


def _cfg_gitlab_url(config: dict) -> str:
    """Return the GitLab base URL from config, falling back to $GITLAB_URL."""
    return config.get("gitlab_url", os.getenv("GITLAB_URL", "https://gitlab-master.nvidia.com"))


def _cfg_slack_token(config: dict) -> str | None:
    """Return the Slack bot token by reading the env var named in config."""
    var = config.get("slack", {}).get("token_env_var", "DS_CI_SLACK_TOKEN")
    return os.getenv(var)


def _cfg_resolve_channel(config: dict) -> str:
    """Walk the config routing rules and return the first matching channel.

    Supported condition keys (all ANDed within a rule):
      ref_pattern   -- regex matched against $CI_COMMIT_REF_NAME
      variable      -- "ENV_VAR=value" equality check
      pipeline_source -- matched against $CI_PIPELINE_SOURCE
      mr_description_checkbox -- substring checked in $CI_MERGE_REQUEST_DESCRIPTION
      default       -- rule value used as-is (always matches)

    Falls back to '#isaac-sim-ci' if no rule matches.
    """
    rules = config.get("slack", {}).get("routing", [])
    for rule in rules:
        if "default" in rule:
            return rule["default"]
        cond = rule.get("condition", {})
        match = True
        if "ref_pattern" in cond:
            ref = os.getenv("CI_COMMIT_REF_NAME", "")
            if not re.search(cond["ref_pattern"], ref):
                match = False
        if match and "variable" in cond:
            var_expr = cond["variable"]
            k, _, v = var_expr.partition("=")
            if os.getenv(k, "") != v:
                match = False
        if match and "pipeline_source" in cond:
            if os.getenv("CI_PIPELINE_SOURCE", "") != cond["pipeline_source"]:
                match = False
        if match and "mr_description_checkbox" in cond:
            desc = os.getenv("CI_MERGE_REQUEST_DESCRIPTION", "")
            label = cond["mr_description_checkbox"]
            # Only match when the checkbox is checked: "- [x] <label>" (case-insensitive x).
            if not re.search(r"-\s*\[[xX]\]\s*" + re.escape(label), desc):
                match = False
        if match:
            return rule.get("channel", "#isaac-sim-ci")
    return "#isaac-sim-ci"
