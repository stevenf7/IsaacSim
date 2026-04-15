# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
"""API client wrappers for GitHub and GitLab used by CI dashboard tooling."""

from __future__ import annotations

import os
import sys
import time
from collections.abc import Generator

# Optional: requests is only needed in fetch mode
try:
    import requests as _requests
except ImportError:
    _requests = None

# ---------------------------------------------------------------------------
# Token resolution
# ---------------------------------------------------------------------------

_GITLAB_TOKEN_VARS: tuple[str, ...] = ("GITLAB_AUTH_TOKEN", "GITLAB_TOKEN", "GITLAB_API_TOKEN")
_GITHUB_TOKEN_VARS: tuple[str, ...] = ("GITHUB_NVIDIA_DEV_TOKEN", "GITHUB_TOKEN", "GITHUB_API_TOKEN")

GITHUB_BASE_URL = "https://api.github.com/repos/isaac-sim/IsaacLab"


def _resolve_token(var_names: tuple[str, ...]) -> tuple[str, str | None]:
    """Return (value, var_name) for the first non-empty env var in *var_names*."""
    for var in var_names:
        val = os.environ.get(var, "")
        if val:
            return val, var
    return "", None


# ---------------------------------------------------------------------------
# GitHubClient
# ---------------------------------------------------------------------------


class GitHubClient:
    def __init__(self, token: str | None = None, verbose: bool = False,
                 base_url: str | None = None) -> None:
        if _requests is None:
            print("Error: 'requests' package is required for the fetch-github subcommand.", file=sys.stderr)
            print("Install it with:  pip install requests", file=sys.stderr)
            sys.exit(1)
        self.session = _requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
        else:
            print(
                "\n\u26a0  WARNING: No GitHub token provided.\n"
                "   Rate limit: 60 req/hr (unauthenticated) vs 5000/hr (authenticated).\n"
                "   Set GITHUB_NVIDIA_DEV_TOKEN, GITHUB_TOKEN, or GITHUB_API_TOKEN for full throughput.\n",
                file=sys.stderr,
            )
        self.verbose = verbose
        # base_url is the repo-level API root, e.g.
        # "https://api.github.com/repos/isaac-sim/IsaacLab"
        self.base_url = base_url or GITHUB_BASE_URL

    def _check_rate_limit(self, response: _requests.Response) -> None:
        remaining = int(response.headers.get("X-RateLimit-Remaining", 999))
        if remaining <= 5:
            reset_ts = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
            wait = max(0, reset_ts - time.time()) + 2
            print(f"\u23f3 GitHub rate limit low ({remaining} remaining). Sleeping {wait:.0f}s\u2026", file=sys.stderr)
            time.sleep(wait)

    def get(self, path: str, **kwargs) -> _requests.Response:
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        if self.verbose:
            print(f"  GH GET {url}", file=sys.stderr)
        resp = self.session.get(url, **kwargs)
        self._check_rate_limit(resp)
        resp.raise_for_status()
        return resp

    def get_json(self, path: str, **kwargs) -> dict:
        return self.get(path, **kwargs).json()


# ---------------------------------------------------------------------------
# GitLabClient
# ---------------------------------------------------------------------------


class GitLabClient:
    def __init__(self, gitlab_url: str, token: str | None = None, verbose: bool = False) -> None:
        if _requests is None:
            print("Error: 'requests' package is required for the fetch-gitlab subcommand.", file=sys.stderr)
            print("Install it with:  pip install requests", file=sys.stderr)
            sys.exit(1)

        self.base_url = f"{gitlab_url.rstrip('/')}/api/v4"
        self.session = _requests.Session()
        if token:
            self.session.headers["PRIVATE-TOKEN"] = token
        else:
            print(
                "\n\u26a0  WARNING: No GitLab token provided.\n"
                "   Set GITLAB_AUTH_TOKEN, GITLAB_TOKEN, or GITLAB_API_TOKEN for authenticated access.\n"
                "   Without a token, most NVIDIA GitLab endpoints will return 401.\n",
                file=sys.stderr,
            )
        self.verbose = verbose

    def get(self, path: str, retries: int = 3, **kwargs) -> _requests.Response:
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        if self.verbose:
            print(f"  GET {url}", file=sys.stderr)
        for attempt in range(retries):
            try:
                resp = self.session.get(url, **kwargs)
                resp.raise_for_status()
                return resp
            except Exception:
                if attempt == retries - 1:
                    raise
                time.sleep(1 * (attempt + 1))

    def get_json(self, path: str, **kwargs) -> dict:
        return self.get(path, **kwargs).json()

    def get_paginated(self, path: str, params: dict | None = None, max_pages: int = 20) -> Generator:
        """Yield all items from a paginated list endpoint."""
        params = dict(params or {})
        params.setdefault("per_page", 100)
        page = 1
        while page <= max_pages:
            params["page"] = page
            items = self.get_json(path, params=params)
            if not items:
                break
            yield from items
            if len(items) < params["per_page"]:
                break
            page += 1
