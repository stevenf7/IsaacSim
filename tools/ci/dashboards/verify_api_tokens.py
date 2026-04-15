# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
"""Verify CI tokens can reach GitLab and GitHub APIs (no secrets printed)."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable

import requests

GITLAB_URL = os.environ.get("GITLAB_URL", "https://gitlab-master.nvidia.com").rstrip("/")

# Priority order: first successful credential wins.
GITLAB_ENV_VARS = ("GITLAB_AUTH_TOKEN", "GITLAB_TOKEN", "GITLAB_API_TOKEN")
GITHUB_ENV_VARS = ("GITHUB_NVIDIA_DEV_TOKEN", "GITHUB_TOKEN", "GITHUB_API_TOKEN")


def _warn_mismatched_values(pairs: list[tuple[str, str]], label: str) -> None:
    """If several env vars are non-empty and their values differ, print a warning (no secrets)."""
    nonempty = {n: v for n, v in pairs if v}
    if len(nonempty) <= 1:
        return
    if len(set(nonempty.values())) > 1:
        names = ", ".join(sorted(nonempty.keys()))
        print(
            f"Warning: multiple {label} token environment variables are set with different values "
            f"({names}). Trying each in priority order until one succeeds.",
            file=sys.stderr,
        )


def _gitlab_probe(token: str) -> requests.Response:
    return requests.get(
        f"{GITLAB_URL}/api/v4/user",
        headers={"PRIVATE-TOKEN": token},
        timeout=60,
    )


def _github_probe(token: str) -> requests.Response:
    return requests.get(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=60,
    )


def _check_api(label: str, env_vars: tuple[str, ...], probe_fn: Callable[[str], requests.Response], user_key: str) -> bool:
    pairs = [(n, os.environ.get(n, "").strip()) for n in env_vars]
    ordered = [(n, v) for n, v in pairs if v]
    if not ordered:
        print(f"No {label} token env vars set — skipping {label} API check")
        return True
    _warn_mismatched_values(ordered, label)
    last_body = ""
    last_code = 0
    for name, token in ordered:
        try:
            r = probe_fn(token)
        except requests.exceptions.RequestException as exc:
            print(f"{label} API attempt ({name}): network error — {exc}", file=sys.stderr)
            continue
        last_code = r.status_code
        last_body = r.text[:500]
        if r.status_code == 200:
            identity = r.json().get(user_key, "?")
            print(f"{label} API OK via {name} ({user_key}: {identity})")
            return True
        print(f"{label} API attempt ({name}): HTTP {r.status_code}", file=sys.stderr)
    if last_code:
        print(f"{label} API failed after {len(ordered)} attempt(s): last HTTP {last_code}", file=sys.stderr)
        print(last_body, file=sys.stderr)
    else:
        print(f"{label} API failed after {len(ordered)} attempt(s): all requests encountered network errors", file=sys.stderr)
    return False


def _check_gitlab() -> bool:
    return _check_api("GitLab", GITLAB_ENV_VARS, _gitlab_probe, "username")


def _check_github() -> bool:
    return _check_api("GitHub", GITHUB_ENV_VARS, _github_probe, "login")


def main() -> int:
    print("=== API token checks (dashboard fetch) ===")
    gl_ok = _check_gitlab()
    gh_ok = _check_github()
    ok = gl_ok and gh_ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
