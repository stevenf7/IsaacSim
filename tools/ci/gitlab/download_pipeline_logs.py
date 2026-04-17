#!/usr/bin/env python3
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

"""Download job logs from a GitLab pipeline for offline analysis.

Given a pipeline ID, this script fetches jobs from the GitLab API and downloads:
  1) Job traces (stdout/stderr) as `job_trace.log`
  2) Log-like files from artifacts archives (`*.log`, `*.txt`)

By default, only test-like stages are included to focus on failure triage.
The resulting `download_report.json` contains both pipeline-level metadata and
per-job download results so downstream analyzers can explain what was selected,
skipped, or blocked by auth/API errors.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

import requests

DEFAULT_TEST_STAGES = {"test", "nightly-test", "external-test", "prod-test", "deploy-test"}
DEFAULT_TOKEN_ENV_CANDIDATES = (
    "ISAAC_MAINTAINER_RO_TOKEN",
    "CI_GITLAB_API_TOKEN",
    "GITLAB_API_TOKEN",
    "GITLAB_TOKEN",
)


def _sanitize_name(name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", name.strip())
    return safe[:120] if safe else "unknown_job"


def _find_latest_pipeline(
    gitlab_url: str,
    project_id: int,
    headers: dict[str, str],
    ref: str,
    statuses: tuple[str, ...] = ("failed", "success"),
) -> dict[str, Any]:
    """Find the most recent finished pipeline for *ref* (branch name).

    Searches the given *statuses* in order so that failed pipelines are
    preferred (the common triage case).  Returns the first match.
    """
    for status in statuses:
        url = f"{gitlab_url}/api/v4/projects/{project_id}/pipelines"
        params: dict[str, Any] = {
            "ref": ref,
            "status": status,
            "per_page": 1,
            "order_by": "id",
            "sort": "desc",
        }
        pipelines = _request_json(url, headers, params=params)
        if pipelines:
            return pipelines[0]

    raise ValueError(
        f"No finished pipeline found for ref '{ref}' on {gitlab_url} "
        f"(project {project_id}).  Tried statuses: {statuses}"
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download logs from a GitLab pipeline")
    pipeline_group = parser.add_mutually_exclusive_group(required=True)
    pipeline_group.add_argument("--pipeline-id", type=int, help="GitLab pipeline ID")
    pipeline_group.add_argument(
        "--pipeline-url",
        help="GitLab pipeline URL (e.g. https://host/group/project/-/pipelines/12345)",
    )
    pipeline_group.add_argument(
        "--ref",
        help="Branch name — automatically find the latest finished pipeline for this ref (e.g. develop)",
    )
    parser.add_argument(
        "--project-id",
        type=int,
        default=None,
        help="GitLab project ID (defaults to CI_PROJECT_ID env var)",
    )
    parser.add_argument(
        "--gitlab-url",
        default="https://gitlab-master.nvidia.com",
        help="GitLab base URL",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: pipeline_<id>_logs)",
    )
    parser.add_argument(
        "--token-env",
        default=None,
        help=(
            "Environment variable holding PRIVATE-TOKEN. "
            "If omitted, checks ISAAC_MAINTAINER_RO_TOKEN, CI_GITLAB_API_TOKEN, "
            "GITLAB_API_TOKEN, then GITLAB_TOKEN."
        ),
    )
    parser.add_argument(
        "--all-jobs",
        action="store_true",
        help="Include all pipeline jobs (default filters to test-like stages)",
    )
    parser.add_argument(
        "--job-name-regex",
        default=None,
        help="Optional regex filter for job names",
    )
    parser.add_argument(
        "--no-traces",
        action="store_true",
        help="Disable downloading job trace logs",
    )
    parser.add_argument(
        "--no-artifacts",
        action="store_true",
        help="Disable downloading and extracting artifacts",
    )
    parser.add_argument(
        "--traces-only",
        action="store_true",
        help="Alias for --no-artifacts when only job traces are needed",
    )
    parser.add_argument(
        "--keep-artifact-zip",
        action="store_true",
        help="Keep downloaded artifacts.zip files after extraction",
    )
    return parser.parse_args()


def _parse_pipeline_url(pipeline_url: str) -> tuple[str, str, int]:
    parsed = urlparse(pipeline_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Invalid pipeline URL: {pipeline_url}")

    path = parsed.path.strip("/")
    match = re.search(r"(.+)/-/pipelines/(\d+)$", path)
    if not match:
        raise ValueError("Pipeline URL must look like https://<host>/<group>/<project>/-/pipelines/<id>")

    project_path = match.group(1)
    pipeline_id = int(match.group(2))
    gitlab_url = f"{parsed.scheme}://{parsed.netloc}"
    return gitlab_url, project_path, pipeline_id


def _request_json(url: str, headers: dict[str, str], params: dict[str, Any] | None = None) -> Any:
    response = requests.get(url, headers=headers, params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def _resolve_token(args: argparse.Namespace) -> tuple[str, str]:
    if args.token_env:
        token = os.getenv(args.token_env)
        if token is None:
            raise ValueError(f"{args.token_env} environment variable is not set")
        return token, args.token_env

    for env_name in DEFAULT_TOKEN_ENV_CANDIDATES:
        token = os.getenv(env_name)
        if token:
            return token, env_name

    searched = ", ".join(DEFAULT_TOKEN_ENV_CANDIDATES)
    raise ValueError("GitLab token not found. Set --token-env or one of these environment variables: " f"{searched}")


def _list_pipeline_jobs(
    gitlab_url: str, project_id: int, pipeline_id: int, headers: dict[str, str]
) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    page = 1
    while True:
        jobs_url = f"{gitlab_url}/api/v4/projects/{project_id}/pipelines/{pipeline_id}/jobs"
        page_jobs = _request_json(jobs_url, headers, params={"per_page": 100, "page": page})
        if not page_jobs:
            break
        jobs.extend(page_jobs)
        page += 1
    return jobs


def _download_to_file(url: str, headers: dict[str, str], out_path: Path, timeout: int = 300) -> None:
    with requests.get(url, headers=headers, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        with out_path.open("wb") as out_f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    out_f.write(chunk)


def _extract_log_files(artifact_zip_path: Path, destination_dir: Path) -> list[str]:
    extracted: list[str] = []
    with zipfile.ZipFile(artifact_zip_path, "r") as zf:
        for member in zf.infolist():
            if member.is_dir():
                continue
            lower_name = member.filename.lower()
            if lower_name.endswith(".log") or lower_name.endswith(".txt"):
                zf.extract(member, destination_dir)
                extracted.append(member.filename)
    return extracted


def _select_jobs(args: argparse.Namespace, jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = jobs
    if not args.all_jobs:
        selected = [job for job in selected if job.get("stage") in DEFAULT_TEST_STAGES]
    if args.job_name_regex:
        pattern = re.compile(args.job_name_regex)
        selected = [job for job in selected if pattern.search(job.get("name", ""))]
    return selected


def _selection_summary(
    args: argparse.Namespace, jobs: list[dict[str, Any]], selected_jobs: list[dict[str, Any]]
) -> dict[str, Any]:
    selected_ids = {job["id"] for job in selected_jobs}
    skipped_jobs = [job for job in jobs if job["id"] not in selected_ids]
    return {
        "selected_count": len(selected_jobs),
        "skipped_count": len(skipped_jobs),
        "selected_stage_filter": sorted(DEFAULT_TEST_STAGES) if not args.all_jobs else "all",
        "job_name_regex": args.job_name_regex,
        "skipped_jobs": [
            {
                "job_id": job["id"],
                "name": job.get("name", "unknown"),
                "stage": job.get("stage"),
                "status": job.get("status"),
            }
            for job in skipped_jobs
        ],
    }


def _resolve_project_id_env(args: argparse.Namespace) -> tuple[str, int]:
    """Return (gitlab_url, project_id) from args or environment."""
    gitlab_url = args.gitlab_url
    project_id = args.project_id
    if project_id is None:
        env_project_id = os.getenv("CI_PROJECT_ID")
        if env_project_id is None:
            raise ValueError("Provide --project-id or set CI_PROJECT_ID")
        project_id = int(env_project_id)
    return gitlab_url, project_id


def _resolve_project_id(
    args: argparse.Namespace,
    headers: dict[str, str],
) -> tuple[str, int, int]:
    if args.pipeline_url:
        gitlab_url, project_path, pipeline_id = _parse_pipeline_url(args.pipeline_url)
        if args.project_id is not None:
            project_id = args.project_id
        else:
            project_api = f"{gitlab_url}/api/v4/projects/{quote(project_path, safe='')}"
            project = _request_json(project_api, headers)
            project_id = int(project["id"])
        return gitlab_url, project_id, pipeline_id

    if getattr(args, "ref", None):
        gitlab_url, project_id = _resolve_project_id_env(args)
        pipeline = _find_latest_pipeline(gitlab_url, project_id, headers, args.ref)
        pipeline_id = int(pipeline["id"])
        print(f"Resolved --ref {args.ref} → pipeline {pipeline_id} ({pipeline.get('status', 'unknown')})")
        return gitlab_url, project_id, pipeline_id

    if args.pipeline_id is None:
        raise ValueError("Provide --pipeline-id, --pipeline-url, or --ref")

    gitlab_url, project_id = _resolve_project_id_env(args)
    return gitlab_url, project_id, args.pipeline_id


def main() -> None:
    args = _parse_args()
    if args.traces_only:
        args.no_artifacts = True

    token, token_source = _resolve_token(args)
    headers = {"PRIVATE-TOKEN": token}
    gitlab_url, project_id, pipeline_id = _resolve_project_id(args, headers)

    output_dir = Path(args.output_dir or f"pipeline_{pipeline_id}_logs")
    output_dir.mkdir(parents=True, exist_ok=True)

    pipeline_api_url = f"{gitlab_url}/api/v4/projects/{project_id}/pipelines/{pipeline_id}"
    pipeline = _request_json(pipeline_api_url, headers)
    print(f"Pipeline: {pipeline['web_url']} ({pipeline.get('status', 'unknown')})")
    print(
        "Download mode: "
        f"traces={'enabled' if not args.no_traces else 'disabled'}, "
        f"artifacts={'disabled' if args.no_artifacts else 'enabled'}"
    )
    print(f"Auth token source: {token_source}")

    jobs = _list_pipeline_jobs(gitlab_url, project_id, pipeline_id, headers)
    selected_jobs = _select_jobs(args, jobs)
    print(f"Found {len(jobs)} jobs; selected {len(selected_jobs)}")

    report_jobs: list[dict[str, Any]] = []
    for job in selected_jobs:
        job_id = job["id"]
        job_name = job.get("name", "unknown")
        job_dir = output_dir / f"{job_id}_{_sanitize_name(job_name)}"
        job_dir.mkdir(parents=True, exist_ok=True)

        job_record: dict[str, Any] = {
            "job_id": job_id,
            "name": job_name,
            "stage": job.get("stage"),
            "status": job.get("status"),
            "web_url": job.get("web_url"),
            "trace_url": f"{gitlab_url}/api/v4/projects/{project_id}/jobs/{job_id}/trace",
            "artifacts_url": f"{gitlab_url}/api/v4/projects/{project_id}/jobs/{job_id}/artifacts",
            "downloaded_trace": False,
            "downloaded_artifacts": False,
            "artifacts_available": bool(job.get("artifacts_file") and job["artifacts_file"].get("filename")),
            "extracted_log_files": [],
            "errors": [],
        }

        (job_dir / "job_metadata.json").write_text(json.dumps(job_record, indent=2), encoding="utf-8")

        if not args.no_traces:
            trace_path = job_dir / "job_trace.log"
            try:
                _download_to_file(job_record["trace_url"], headers, trace_path, timeout=180)
                job_record["downloaded_trace"] = True
            except requests.RequestException as exc:
                job_record["errors"].append(f"trace download failed: {exc}")

        if job_record["artifacts_available"] and not args.no_artifacts:
            artifact_zip = job_dir / "artifacts.zip"
            try:
                _download_to_file(job_record["artifacts_url"], headers, artifact_zip, timeout=300)
                job_record["downloaded_artifacts"] = True
                extracted = _extract_log_files(artifact_zip, job_dir / "artifact_logs")
                job_record["extracted_log_files"] = extracted
                if not args.keep_artifact_zip:
                    artifact_zip.unlink(missing_ok=True)
            except (requests.RequestException, zipfile.BadZipFile) as exc:
                job_record["errors"].append(f"artifact handling failed: {exc}")

        (job_dir / "job_metadata.json").write_text(json.dumps(job_record, indent=2), encoding="utf-8")
        report_jobs.append(job_record)
        print(
            f"Processed job {job_id} ({job_name}) - trace={job_record['downloaded_trace']} "
            f"artifacts={job_record['downloaded_artifacts']} logs={len(job_record['extracted_log_files'])}"
        )

    report_path = output_dir / "download_report.json"
    report = {
        "pipeline": {
            "pipeline_id": pipeline_id,
            "project_id": project_id,
            "gitlab_url": gitlab_url,
            "web_url": pipeline.get("web_url"),
            "status": pipeline.get("status"),
        },
        "workflow": {
            "token_source": token_source,
            "traces_enabled": not args.no_traces,
            "artifacts_enabled": not args.no_artifacts,
            "keep_artifact_zip": args.keep_artifact_zip,
        },
        "selection": _selection_summary(args, jobs, selected_jobs),
        "jobs": report_jobs,
        "counts": {
            "jobs_total": len(jobs),
            "jobs_selected": len(selected_jobs),
            "jobs_with_trace": sum(1 for job in report_jobs if job["downloaded_trace"]),
            "jobs_with_artifacts": sum(1 for job in report_jobs if job["downloaded_artifacts"]),
            "jobs_with_errors": sum(1 for job in report_jobs if job["errors"]),
        },
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote report: {report_path}")


if __name__ == "__main__":
    main()
