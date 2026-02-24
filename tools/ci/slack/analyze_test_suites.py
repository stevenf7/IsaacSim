#!/usr/bin/env python3
"""
Analyze test reports from GitLab pipelines and find regressions.
Compares a test pipeline against a baseline pipeline.
"""

import json
import os
from typing import Dict, Optional, Tuple

import gitlab
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# GitLab configuration from environment
PRIVATE_TOKEN = os.getenv("CI_GITLAB_API_TOKEN")
GITLAB_URL = os.getenv("GITLAB_URL", "https://gitlab-master.nvidia.com")
PROJECT_ID = os.getenv("CI_PROJECT_ID")

# Source configuration - how to find the test pipeline
SOURCE_TYPE = os.getenv("SOURCE_TYPE")  # 'branch', 'mr', or 'pipeline'
SOURCE_VALUE = os.getenv("SOURCE_VALUE")  # The branch name, MR IID, or pipeline ID

# Baseline configuration
BASELINE_TYPE = os.getenv("BASELINE_TYPE")  # 'branch', 'mr', or 'pipeline'
BASELINE_VALUE = os.getenv("BASELINE_VALUE")  # The branch name, MR IID, or pipeline ID
BASELINE_PROJECT_ID = os.getenv("BASELINE_PROJECT_ID")  # Optional, defaults to PROJECT_ID


def get_gitlab_client(quiet: bool = False) -> Optional[gitlab.Gitlab]:
    """
    Create and authenticate a GitLab client.

    Args:
        quiet: If True, suppress non-error console output

    Returns:
        Authenticated GitLab client or None if authentication fails
    """
    if not PRIVATE_TOKEN:
        print("ERROR: PRIVATE_TOKEN not set. Please add it to your .env file.")
        return None

    if not PROJECT_ID:
        print("ERROR: PROJECT_ID not set. Please add it to your .env file.")
        return None

    gl = gitlab.Gitlab(url=GITLAB_URL, private_token=PRIVATE_TOKEN)

    try:
        gl.auth()
        if gl.user is None:
            print("ERROR: GitLab authentication failed!")
            return None
        if not quiet:
            print(f"Authenticated as: {gl.user.username}")
        return gl
    except Exception as e:
        print(f"ERROR: GitLab authentication failed: {e}")
        return None


def get_pipeline(
    gl: gitlab.Gitlab, source_type: str, source_value: str, project_id: str = None, quiet: bool = False
) -> Tuple[Optional[dict], Optional[dict]]:
    """
    Get a pipeline based on source type (branch, mr, or pipeline).

    Args:
        gl: Authenticated GitLab client
        source_type: One of 'branch', 'mr', or 'pipeline'
        source_value: The branch name, MR IID, or pipeline ID
        project_id: Optional project ID (defaults to PROJECT_ID env var)
        quiet: If True, suppress non-error console output

    Returns:
        Tuple of (pipeline object, pipeline_info dict) or (None, None) if not found
    """
    pid = project_id or PROJECT_ID

    try:
        project = gl.projects.get(pid)

        if source_type == "branch":
            pipelines = project.pipelines.list(ref=source_value, per_page=1, order_by="id", sort="desc", get_all=False)
            if not pipelines:
                print(f"No pipelines found for branch: {source_value} (project: {pid})")
                return None, None
            pipeline = pipelines[0]
            if not quiet:
                print(
                    f"Found pipeline: #{pipeline.id} ({pipeline.status}) for branch '{source_value}' (project: {pid})"
                )
            info = {
                "id": pipeline.id,
                "web_url": pipeline.web_url,
                "project_id": pid,
                "source_type": "branch",
                "source_value": source_value,
            }
            return pipeline, info

        elif source_type == "mr":
            mr_iid = int(source_value)
            mr = project.mergerequests.get(mr_iid)
            mr_pipelines = mr.pipelines.list(per_page=1, order_by="id", sort="desc", get_all=False)
            if not mr_pipelines:
                print(f"No pipelines found for MR !{mr_iid} (project: {pid})")
                return None, None
            pipeline = project.pipelines.get(mr_pipelines[0].id)
            if not quiet:
                print(
                    f"Found pipeline: #{pipeline.id} ({pipeline.status}) for MR !{mr_iid} '{mr.title}' (project: {pid})"
                )
            info = {
                "id": pipeline.id,
                "web_url": pipeline.web_url,
                "project_id": pid,
                "source_type": "mr",
                "source_value": mr_iid,
                "mr_title": mr.title,
            }
            return pipeline, info

        elif source_type == "pipeline":
            pipeline_id = int(source_value)
            pipeline = project.pipelines.get(pipeline_id)
            if not quiet:
                print(f"Found pipeline: #{pipeline.id} ({pipeline.status}) (project: {pid})")
            info = {
                "id": pipeline.id,
                "web_url": pipeline.web_url,
                "project_id": pid,
                "source_type": "pipeline",
                "source_value": pipeline_id,
            }
            return pipeline, info

        else:
            print(f"ERROR: Invalid source type '{source_type}'. Must be 'branch', 'mr', or 'pipeline'.")
            return None, None

    except Exception as e:
        print(f"ERROR: Failed to get pipeline for {source_type}={source_value} (project: {pid}): {e}")
        return None, None


def fetch_test_report_from_pipeline(gl: gitlab.Gitlab, pipeline_id: int, project_id: str = None) -> Optional[dict]:
    """
    Fetch the test report JSON from a GitLab pipeline.

    Args:
        gl: Authenticated GitLab client
        pipeline_id: ID of the pipeline to fetch test report from
        project_id: Optional project ID (defaults to PROJECT_ID env var)

    Returns:
        Test report data as dictionary or None if failed
    """
    pid = project_id or PROJECT_ID
    try:
        project = gl.projects.get(pid)
        pipeline = project.pipelines.get(pipeline_id)

        # Get the test report using the test_report API
        test_report = pipeline.test_report.get()

        # Convert to dict if it's a gitlab object
        if hasattr(test_report, "asdict"):
            return test_report.asdict()
        elif hasattr(test_report, "_attrs"):
            return dict(test_report._attrs)
        else:
            # Already a dict or dict-like
            return dict(test_report)

    except Exception as e:
        print(f"ERROR: Failed to fetch test report for pipeline #{pipeline_id}: {e}")
        return None


def analyze_test_data(data: dict, name: str = "test_report", quiet: bool = False) -> Optional[Dict]:
    """
    Analyze test report data from a dictionary.

    Args:
        data: Test report data dictionary
        name: Name to identify this report
        quiet: If True, suppress non-error console output

    Returns:
        Analysis data dictionary or None if failed
    """
    if not quiet:
        print(f"\nProcessing: {name}")

    try:
        # Extract test suites and count test cases
        suite_counts = {}
        suite_unique_counts = {}
        suite_pass_counts = {}
        suite_fail_counts = {}
        suite_error_counts = {}
        suite_skip_counts = {}
        all_test_case_names = set()

        if "test_suites" in data:
            for suite in data["test_suites"]:
                suite_name = suite.get("name", "Unknown")
                test_cases = suite.get("test_cases", [])
                test_case_count = len(test_cases)
                suite_counts[suite_name] = test_case_count

                # Get pass/fail counts from suite level if available
                suite_pass_counts[suite_name] = suite.get("success_count", 0)
                suite_fail_counts[suite_name] = suite.get("failed_count", 0)
                suite_error_counts[suite_name] = suite.get("error_count", 0)
                suite_skip_counts[suite_name] = suite.get("skipped_count", 0)

                # Collect unique test case names per suite
                suite_unique_names = set()
                for test_case in test_cases:
                    test_case_name = test_case.get("name", "")
                    if test_case_name:
                        suite_unique_names.add(test_case_name)
                        all_test_case_names.add(test_case_name)

                suite_unique_counts[suite_name] = len(suite_unique_names)

            # Calculate totals
            total_pass = sum(suite_pass_counts.values())
            total_fail = sum(suite_fail_counts.values())
            total_error = sum(suite_error_counts.values())
            total_skip = sum(suite_skip_counts.values())

            result = {
                "suite_counts": suite_counts,
                "suite_unique_counts": suite_unique_counts,
                "suite_pass_counts": suite_pass_counts,
                "suite_fail_counts": suite_fail_counts,
                "suite_error_counts": suite_error_counts,
                "suite_skip_counts": suite_skip_counts,
                "unique_test_cases": len(all_test_case_names),
                "total_test_cases": sum(suite_counts.values()),
                "total_pass": total_pass,
                "total_fail": total_fail,
                "total_error": total_error,
                "total_skip": total_skip,
            }

            # Print summary
            if not quiet:
                print(f"  Total test suites: {len(suite_counts)}")
                print(f"  Total test cases: {sum(suite_counts.values())}")
                print(f"  Unique test cases: {len(all_test_case_names)}")
                print(f"  Pass: {total_pass}, Fail: {total_fail}, Error: {total_error}, Skip: {total_skip}")

            return result
        else:
            print(f"  Warning: 'test_suites' key not found in {name}")
            return None

    except Exception as e:
        print(f"  Error: {e}")
        return None


def _strip_inline_from_job_name(name: str) -> str:
    """If job name contains ', inline]', normalize to ']' so inline and after_script jobs match."""
    if ", inline]" in name:
        return name.replace(", inline]", "]")
    return name


def normalize_suite_name(suite_name: str) -> tuple:
    """
    Normalize a suite name to extract platform and test category for matching.

    Args:
        suite_name: The suite name to normalize

    Returns:
        Tuple of (platform, category_key) for matching
    """
    import re

    suite_name = _strip_inline_from_job_name(suite_name)

    # Extract platform (linux/windows)
    platform = "linux" if "linux" in suite_name.lower() else "windows"

    # Check if it's a matrix-style name with square brackets
    bracket_match = re.search(r"\[(.*?)\]", suite_name)
    if bracket_match:
        # Extract content from brackets
        bracket_content = bracket_match.group(1)
        # Split by comma and clean up
        parts = [p.strip() for p in bracket_content.split(",")]

        # Remove common flags like '-b' and 'inline'
        parts = [p for p in parts if p not in ["-b", "inline"]]

        # Take first 2 elements if available, otherwise 1
        if len(parts) >= 2:
            category_key = "-".join(parts[:2])
        elif len(parts) == 1:
            category_key = parts[0]
        else:
            category_key = suite_name
    else:
        # For baseline-style names, extract the category after the last hyphen pattern
        # e.g., "test-linux-x86_64-pythontests-core" -> "pythontests-core"
        # or "test-linux-x86_64-nativepythontests-api" -> "nativepythontests-api"
        parts = suite_name.split("-")

        # Find where the test type starts (pythontests, nativepythontests, etc.)
        for i, part in enumerate(parts):
            if "pythontests" in part or "benchmarks" in part or "isaaclab" in part:
                category_key = "-".join(parts[i:])
                break
        else:
            category_key = suite_name

    return (platform, category_key)


def print_combined_table(results: Dict[str, Dict]):
    """
    Print a combined table showing baseline and test side-by-side.

    Args:
        results: Dictionary with 'baseline' and 'test' keys containing analysis data
    """
    # Get baseline and test data - support both new format and legacy filename-based format
    baseline_data = results.get("baseline")
    test_data = results.get("test")

    # Fallback to legacy filename-based lookup
    if not baseline_data or not test_data:
        for filename, data in results.items():
            if "baseline" in filename.lower():
                baseline_data = data
            elif "matrix" in filename.lower() or "test" in filename.lower():
                test_data = data

    if not baseline_data and not test_data:
        print("\nCould not find baseline or test data for combined table")
        return

    baseline_suites = baseline_data.get("suite_counts", {}) if baseline_data else {}
    baseline_unique = baseline_data.get("suite_unique_counts", {}) if baseline_data else {}
    baseline_pass = baseline_data.get("suite_pass_counts", {}) if baseline_data else {}
    baseline_fail = baseline_data.get("suite_fail_counts", {}) if baseline_data else {}
    baseline_error = baseline_data.get("suite_error_counts", {}) if baseline_data else {}
    test_suites = test_data.get("suite_counts", {}) if test_data else {}
    test_unique = test_data.get("suite_unique_counts", {}) if test_data else {}
    test_pass = test_data.get("suite_pass_counts", {}) if test_data else {}
    test_fail = test_data.get("suite_fail_counts", {}) if test_data else {}
    test_error = test_data.get("suite_error_counts", {}) if test_data else {}

    # Create mappings from normalized names to actual suite names
    baseline_map = {}  # (platform, category) -> suite_name
    test_map = {}  # (platform, category) -> suite_name
    baseline_reverse = {}  # suite_name -> key (for detecting what was mapped)
    test_reverse = {}  # suite_name -> key

    for suite_name in baseline_suites.keys():
        key = normalize_suite_name(suite_name)
        if key in baseline_map:
            print(f"WARNING: Multiple baseline suites map to {key}:")
            print(f"  - {baseline_map[key]}")
            print(f"  - {suite_name}")
        baseline_map[key] = suite_name
        baseline_reverse[suite_name] = key

    for suite_name in test_suites.keys():
        key = normalize_suite_name(suite_name)
        if key in test_map:
            print(f"WARNING: Multiple test suites map to {key}:")
            print(f"  - {test_map[key]}")
            print(f"  - {suite_name}")
        test_map[key] = suite_name
        test_reverse[suite_name] = key

    # Get all unique normalized keys
    all_keys = set(baseline_map.keys()) | set(test_map.keys())

    # Sort by platform (linux first) then by category
    sorted_keys = sorted(all_keys, key=lambda x: (0 if x[0] == "linux" else 1, x[1]))

    # Print combined table
    print("\n" + "=" * 180)
    print("COMBINED TEST SUITE COMPARISON")
    print("=" * 180)

    # Header
    header = f"  {'Test Suite':60} {'B.Total':>8} {'T.Total':>8} {'Diff':>8} {'Baseline':>20} {'Test':>20} {'Delta (P/F/E)':>18}"
    subheader = f"  {'':60} {'':>8} {'':>8} {'(T-B)':>8} {'Pass':>6} {'Fail':>6} {'Err':>6} {'Pass':>6} {'Fail':>6} {'Err':>6} {'':>18}"
    print(header)
    print(subheader)
    print(
        f"  {'-' * 60} {'-' * 8} {'-' * 8} {'-' * 8} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 18}"
    )

    for key in sorted_keys:
        # Get the actual suite names
        baseline_name = baseline_map.get(key, "")
        test_name = test_map.get(key, "")

        # Use baseline name if available, otherwise test name
        display_name = baseline_name if baseline_name else test_name

        # Get values
        baseline_total = baseline_suites.get(baseline_name, 0) if baseline_name else 0
        baseline_p = baseline_pass.get(baseline_name, 0) if baseline_name else 0
        baseline_f = baseline_fail.get(baseline_name, 0) if baseline_name else 0
        baseline_e = baseline_error.get(baseline_name, 0) if baseline_name else 0

        test_total = test_suites.get(test_name, 0) if test_name else 0
        test_p = test_pass.get(test_name, 0) if test_name else 0
        test_f = test_fail.get(test_name, 0) if test_name else 0
        test_e = test_error.get(test_name, 0) if test_name else 0

        # Calculate difference (only if both exist)
        if baseline_total > 0 and test_total > 0:
            diff = test_total - baseline_total
            diff_str = f"{diff:+d}" if diff != 0 else ""

            # Calculate delta for pass/fail/error
            delta_p = test_p - baseline_p
            delta_f = test_f - baseline_f
            delta_e = test_e - baseline_e

            # Only show delta if there are any changes
            if delta_p == 0 and delta_f == 0 and delta_e == 0:
                delta_str = ""
            else:
                delta_str = f"{delta_p:+d}/{delta_f:+d}/{delta_e:+d}"
        else:
            diff_str = "-"
            delta_str = "-"

        # Format values, show '-' if 0
        b_total_str = str(baseline_total) if baseline_total > 0 else "-"
        b_pass_str = str(baseline_p) if baseline_total > 0 else "-"
        b_fail_str = str(baseline_f) if baseline_total > 0 else "-"
        b_err_str = str(baseline_e) if baseline_total > 0 else "-"

        t_total_str = str(test_total) if test_total > 0 else "-"
        t_pass_str = str(test_p) if test_total > 0 else "-"
        t_fail_str = str(test_f) if test_total > 0 else "-"
        t_err_str = str(test_e) if test_total > 0 else "-"

        print(
            f"  {display_name:60} {b_total_str:>8} {t_total_str:>8} {diff_str:>8} {b_pass_str:>6} {b_fail_str:>6} {b_err_str:>6} {t_pass_str:>6} {t_fail_str:>6} {t_err_str:>6} {delta_str:>18}"
        )

    # Totals
    baseline_total_all = baseline_data.get("total_test_cases", 0) if baseline_data else 0
    baseline_pass_all = baseline_data.get("total_pass", 0) if baseline_data else 0
    baseline_fail_all = baseline_data.get("total_fail", 0) if baseline_data else 0
    baseline_error_all = baseline_data.get("total_error", 0) if baseline_data else 0

    test_total_all = test_data.get("total_test_cases", 0) if test_data else 0
    test_pass_all = test_data.get("total_pass", 0) if test_data else 0
    test_fail_all = test_data.get("total_fail", 0) if test_data else 0
    test_error_all = test_data.get("total_error", 0) if test_data else 0

    total_diff = test_total_all - baseline_total_all
    total_diff_str = f"{total_diff:+d}" if total_diff != 0 else "0"

    # Calculate total deltas
    total_delta_p = test_pass_all - baseline_pass_all
    total_delta_f = test_fail_all - baseline_fail_all
    total_delta_e = test_error_all - baseline_error_all
    total_delta_str = f"{total_delta_p:+d}/{total_delta_f:+d}/{total_delta_e:+d}"

    print(
        f"  {'-' * 60} {'-' * 8} {'-' * 8} {'-' * 8} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 18}"
    )
    print(
        f"  {'TOTAL':60} {baseline_total_all:>8} {test_total_all:>8} {total_diff_str:>8} {baseline_pass_all:>6} {baseline_fail_all:>6} {baseline_error_all:>6} {test_pass_all:>6} {test_fail_all:>6} {test_error_all:>6} {total_delta_str:>18}"
    )

    # Print mapping summary
    print("\n" + "=" * 105)
    print("MAPPING SUMMARY")
    print("=" * 105)

    matched = 0
    baseline_only = 0
    test_only = 0

    for key in sorted_keys:
        baseline_name = baseline_map.get(key, "")
        test_name = test_map.get(key, "")

        if baseline_name and test_name:
            matched += 1
        elif baseline_name:
            baseline_only += 1
        elif test_name:
            test_only += 1

    print(f"\nMatched suites (in both baseline and test): {matched}")
    print(f"Baseline-only suites (not found in test): {baseline_only}")
    print(f"Test-only suites (not found in baseline): {test_only}")

    if baseline_only > 0:
        print(f"\nBaseline-only suites:")
        for key in sorted_keys:
            baseline_name = baseline_map.get(key, "")
            test_name = test_map.get(key, "")
            if baseline_name and not test_name:
                print(f"  - {baseline_name}")

    if test_only > 0:
        print(f"\nTest-only suites:")
        for key in sorted_keys:
            baseline_name = baseline_map.get(key, "")
            test_name = test_map.get(key, "")
            if test_name and not baseline_name:
                print(f"  - {test_name}")


def strip_common_prefix_and_suffix(suite_names: list) -> dict:
    """
    Strip common prefix and suffix from suite names to save space.

    Args:
        suite_names: List of suite names

    Returns:
        Dictionary mapping original names to stripped names
    """
    if not suite_names:
        return {}

    result = {}
    for name in suite_names:
        stripped = name

        # Strip 'test-' prefix if all names have it
        if all(n.startswith("test-") for n in suite_names):
            if stripped.startswith("test-"):
                stripped = stripped[5:]

        # Strip ', inline]' so inline and after_script jobs display the same
        stripped = _strip_inline_from_job_name(stripped)

        result[name] = stripped

    return result


def generate_comparison_text(baseline_analysis: Dict, test_analysis: Dict) -> Tuple[str, str]:
    """
    Generate the combined test suite comparison table and mapping summary as separate strings.

    Args:
        baseline_analysis: Analysis data for baseline
        test_analysis: Analysis data for test

    Returns:
        Tuple of (comparison_table, mapping_summary)
    """
    baseline_suites = baseline_analysis.get("suite_counts", {})
    baseline_pass = baseline_analysis.get("suite_pass_counts", {})
    baseline_fail = baseline_analysis.get("suite_fail_counts", {})
    baseline_error = baseline_analysis.get("suite_error_counts", {})

    test_suites = test_analysis.get("suite_counts", {})
    test_pass = test_analysis.get("suite_pass_counts", {})
    test_fail = test_analysis.get("suite_fail_counts", {})
    test_error = test_analysis.get("suite_error_counts", {})

    # Strip common prefix and suffix from suite names
    all_suite_names = list(set(baseline_suites.keys()) | set(test_suites.keys()))
    name_mapping = strip_common_prefix_and_suffix(all_suite_names)

    # Calculate optimal column width based on longest display name
    max_display_name_length = max(len(display_name) for display_name in name_mapping.values()) if name_mapping else 60
    # Add a small buffer (2 chars) for readability, but cap at 60
    name_col_width = min(max_display_name_length + 2, 60)

    # Create mappings from normalized names
    baseline_map = {}
    test_map = {}

    for suite_name in baseline_suites.keys():
        key = normalize_suite_name(suite_name)
        baseline_map[key] = suite_name

    for suite_name in test_suites.keys():
        key = normalize_suite_name(suite_name)
        test_map[key] = suite_name

    # Get all unique normalized keys
    all_keys = set(baseline_map.keys()) | set(test_map.keys())
    sorted_keys = sorted(all_keys, key=lambda x: (0 if x[0] == "linux" else 1, x[1]))

    # Build comparison table
    comparison_lines = []
    # Calculate total width: name_col + 2 total columns (4 chars) + 1 diff column (4 chars) + 6 detail columns (6 chars each) + 1 delta column (18 chars) + spaces
    # Spaces between columns: 10 spaces total
    total_width = name_col_width + (4 * 3) + (6 * 6) + 18 + 10
    comparison_lines.append("=" * total_width)
    comparison_lines.append("COMBINED TEST SUITE COMPARISON")
    comparison_lines.append("=" * total_width)

    # Two-line headers to save space
    header_line1 = f"{'Test Suite':{name_col_width}} {'Base':>4} {'Test':>4} {'':>4} {'Baseline':>20} {'Test':>20} {'Delta (P/F/E)':>18}"
    header_line2 = f"{'':{name_col_width}} {'Tot':>4} {'Tot':>4} {'Diff':>4} {'Pass':>6} {'Fail':>6} {'Err':>6} {'Pass':>6} {'Fail':>6} {'Err':>6} {'':>18}"
    comparison_lines.append(header_line1)
    comparison_lines.append(header_line2)
    comparison_lines.append(
        f"{'-' * name_col_width} {'-' * 4} {'-' * 4} {'-' * 4} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 18}"
    )

    for key in sorted_keys:
        baseline_name = baseline_map.get(key, "")
        test_name = test_map.get(key, "")
        original_name = baseline_name if baseline_name else test_name
        display_name = name_mapping.get(original_name, original_name)

        b_total = baseline_suites.get(baseline_name, 0) if baseline_name else 0
        b_p = baseline_pass.get(baseline_name, 0) if baseline_name else 0
        b_f = baseline_fail.get(baseline_name, 0) if baseline_name else 0
        b_e = baseline_error.get(baseline_name, 0) if baseline_name else 0

        t_total = test_suites.get(test_name, 0) if test_name else 0
        t_p = test_pass.get(test_name, 0) if test_name else 0
        t_f = test_fail.get(test_name, 0) if test_name else 0
        t_e = test_error.get(test_name, 0) if test_name else 0

        if b_total > 0 and t_total > 0:
            diff = t_total - b_total
            diff_str = f"{diff:+d}" if diff != 0 else ""
            delta_p = t_p - b_p
            delta_f = t_f - b_f
            delta_e = t_e - b_e
            delta_str = f"{delta_p:+d}/{delta_f:+d}/{delta_e:+d}" if any([delta_p, delta_f, delta_e]) else ""
        else:
            diff_str = "-"
            delta_str = "-"

        b_total_str = str(b_total) if b_total > 0 else "-"
        b_pass_str = str(b_p) if b_total > 0 else "-"
        b_fail_str = str(b_f) if b_total > 0 else "-"
        b_err_str = str(b_e) if b_total > 0 else "-"

        t_total_str = str(t_total) if t_total > 0 else "-"
        t_pass_str = str(t_p) if t_total > 0 else "-"
        t_fail_str = str(t_f) if t_total > 0 else "-"
        t_err_str = str(t_e) if t_total > 0 else "-"

        comparison_lines.append(
            f"{display_name:{name_col_width}} {b_total_str:>4} {t_total_str:>4} {diff_str:>4} {b_pass_str:>6} {b_fail_str:>6} {b_err_str:>6} {t_pass_str:>6} {t_fail_str:>6} {t_err_str:>6} {delta_str:>18}"
        )

    # Totals
    b_total_all = baseline_analysis.get("total_test_cases", 0)
    b_pass_all = baseline_analysis.get("total_pass", 0)
    b_fail_all = baseline_analysis.get("total_fail", 0)
    b_error_all = baseline_analysis.get("total_error", 0)

    t_total_all = test_analysis.get("total_test_cases", 0)
    t_pass_all = test_analysis.get("total_pass", 0)
    t_fail_all = test_analysis.get("total_fail", 0)
    t_error_all = test_analysis.get("total_error", 0)

    total_diff = t_total_all - b_total_all
    total_diff_str = f"{total_diff:+d}" if total_diff != 0 else "0"

    total_delta_p = t_pass_all - b_pass_all
    total_delta_f = t_fail_all - b_fail_all
    total_delta_e = t_error_all - b_error_all
    total_delta_str = f"{total_delta_p:+d}/{total_delta_f:+d}/{total_delta_e:+d}"

    comparison_lines.append(
        f"{'-' * name_col_width} {'-' * 4} {'-' * 4} {'-' * 4} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 18}"
    )
    comparison_lines.append(
        f"{'TOTAL':{name_col_width}} {b_total_all:>4} {t_total_all:>4} {total_diff_str:>4} {b_pass_all:>6} {b_fail_all:>6} {b_error_all:>6} {t_pass_all:>6} {t_fail_all:>6} {t_error_all:>6} {total_delta_str:>18}"
    )

    # Build mapping summary
    mapping_lines = []
    mapping_lines.append("=" * 100)
    mapping_lines.append("MAPPING SUMMARY")
    mapping_lines.append("=" * 100)

    matched = sum(1 for k in sorted_keys if baseline_map.get(k) and test_map.get(k))
    baseline_only = sum(1 for k in sorted_keys if baseline_map.get(k) and not test_map.get(k))
    test_only = sum(1 for k in sorted_keys if test_map.get(k) and not baseline_map.get(k))

    mapping_lines.append("")
    mapping_lines.append(f"Matched suites (in both baseline and test): {matched}")
    mapping_lines.append(f"Baseline-only suites: {baseline_only}")
    mapping_lines.append(f"Test-only suites: {test_only}")

    if baseline_only > 0:
        mapping_lines.append("")
        mapping_lines.append("Baseline-only suites:")
        for key in sorted_keys:
            if baseline_map.get(key) and not test_map.get(key):
                mapping_lines.append(f"  - {baseline_map[key]}")

    if test_only > 0:
        mapping_lines.append("")
        mapping_lines.append("Test-only suites:")
        for key in sorted_keys:
            if test_map.get(key) and not baseline_map.get(key):
                mapping_lines.append(f"  - {test_map[key]}")

    return "\n".join(comparison_lines), "\n".join(mapping_lines)


def find_regressions_from_data(
    baseline_data: dict,
    test_data: dict,
    output_file: Optional[str] = None,
    test_pipeline_info: Optional[dict] = None,
    baseline_pipeline_info: Optional[dict] = None,
    baseline_analysis: Optional[Dict] = None,
    test_analysis: Optional[Dict] = None,
    quiet: bool = False,
) -> Tuple[list, str, list]:
    """
    Find test cases that fail/error in test data but pass in baseline.
    Optionally output to a file and return the report sections separately.

    Args:
        baseline_data: Baseline test report data dictionary
        test_data: Test report data dictionary to compare
        output_file: Path to the output file, or None to skip file output
        test_pipeline_info: Optional dict with 'id', 'web_url', 'project_id' for test pipeline
        baseline_pipeline_info: Optional dict with 'id', 'web_url', 'project_id' for baseline pipeline
        baseline_analysis: Optional analysis data for baseline (for comparison table)
        test_analysis: Optional analysis data for test (for comparison table)
        quiet: If True, suppress console output (default: False)

    Returns:
        Tuple of (regressions list, full report string, report sections list)
        Report sections list contains: [pipeline_info, comparison_table, mapping_summary, regressions_section]
    """
    # Build baseline map of (suite_name, test_name) -> status
    baseline_tests = {}
    for suite in baseline_data.get("test_suites", []):
        suite_name = suite.get("name", "Unknown")
        for test_case in suite.get("test_cases", []):
            test_name = test_case.get("name", "")
            status = test_case.get("status", "")
            if test_name:
                baseline_tests[(suite_name, test_name)] = status

    # Find regressions in test data
    regressions = []
    for suite in test_data.get("test_suites", []):
        suite_name = suite.get("name", "Unknown")
        for test_case in suite.get("test_cases", []):
            test_name = test_case.get("name", "")
            test_status = test_case.get("status", "")
            system_output = test_case.get("system_output", "")
            stack_trace = test_case.get("stack_trace", "")

            if not test_name:
                continue

            # Check if this test fails/errors in test data but passes in baseline
            if test_status in ("failed", "error"):
                baseline_status = baseline_tests.get((suite_name, test_name), None)

                if baseline_status == "success":
                    regressions.append(
                        {
                            "suite_name": suite_name,
                            "test_name": test_name,
                            "baseline_status": baseline_status,
                            "test_status": test_status,
                            "system_output": system_output or "",
                            "stack_trace": stack_trace or "",
                        }
                    )

    # Build pipeline info section
    pipeline_info_lines = []
    if baseline_pipeline_info or test_pipeline_info:
        pipeline_info_lines.append("PIPELINE INFORMATION")
        pipeline_info_lines.append("-" * 50)

        if baseline_pipeline_info:
            pipeline_info_lines.append(f"Baseline Pipeline: #{baseline_pipeline_info.get('id')}")
            pipeline_info_lines.append(f"  Project ID: {baseline_pipeline_info.get('project_id')}")
            source_type = baseline_pipeline_info.get("source_type")
            source_value = baseline_pipeline_info.get("source_value")
            if source_type == "mr":
                pipeline_info_lines.append(f"  Source: MR !{source_value}")
            elif source_type == "branch":
                pipeline_info_lines.append(f"  Source: Branch '{source_value}'")
            if baseline_pipeline_info.get("web_url"):
                pipeline_info_lines.append(f"  URL: {baseline_pipeline_info.get('web_url')}")

        pipeline_info_lines.append("")

        if test_pipeline_info:
            pipeline_info_lines.append(f"Test Pipeline: #{test_pipeline_info.get('id')}")
            pipeline_info_lines.append(f"  Project ID: {test_pipeline_info.get('project_id')}")
            source_type = test_pipeline_info.get("source_type")
            source_value = test_pipeline_info.get("source_value")
            if source_type == "mr":
                pipeline_info_lines.append(f"  Source: MR !{source_value}")
            elif source_type == "branch":
                pipeline_info_lines.append(f"  Source: Branch '{source_value}'")
            if test_pipeline_info.get("web_url"):
                pipeline_info_lines.append(f"  URL: {test_pipeline_info.get('web_url')}")

    pipeline_info_section = "\n".join(pipeline_info_lines) if pipeline_info_lines else ""

    # Build comparison table and mapping summary sections
    comparison_table_section = ""
    mapping_summary_section = ""
    if baseline_analysis and test_analysis:
        comparison_table_section, mapping_summary_section = generate_comparison_text(baseline_analysis, test_analysis)

    # Build regressions section
    regressions_lines = []
    regressions_lines.append("=" * 100)
    regressions_lines.append("REGRESSIONS: Tests that FAIL/ERROR in Test but PASS in Baseline")
    regressions_lines.append("=" * 100)
    regressions_lines.append("")
    regressions_lines.append(f"Total regressions found: {len(regressions)}")
    regressions_lines.append("")

    for i, reg in enumerate(regressions, 1):
        regressions_lines.append("-" * 100)
        regressions_lines.append(f"Regression #{i}")
        regressions_lines.append("-" * 100)
        regressions_lines.append(f"Suite:          {reg['suite_name']}")
        regressions_lines.append(f"Test Case:      {reg['test_name']}")
        regressions_lines.append(f"Baseline:       {reg['baseline_status']}")
        regressions_lines.append(f"Test:           {reg['test_status']}")
        regressions_lines.append("")

        if reg["system_output"]:
            regressions_lines.append("System Output:")
            regressions_lines.append("-" * 50)
            regressions_lines.append(reg["system_output"])
            regressions_lines.append("")

        if reg["stack_trace"]:
            regressions_lines.append("Stack Trace:")
            regressions_lines.append("-" * 50)
            regressions_lines.append(reg["stack_trace"])
            regressions_lines.append("")

        regressions_lines.append("")

    regressions_section = "\n".join(regressions_lines)

    # Build complete report
    report_parts = []
    report_parts.append("=" * 100)
    report_parts.append("TEST REGRESSION REPORT")
    report_parts.append("=" * 100)
    report_parts.append("")

    if pipeline_info_section:
        report_parts.append(pipeline_info_section)
        report_parts.append("")

    if comparison_table_section:
        report_parts.append("")
        report_parts.append(comparison_table_section)
        report_parts.append("")

    if mapping_summary_section:
        report_parts.append("")
        report_parts.append(mapping_summary_section)
        report_parts.append("")

    report_parts.append("")
    report_parts.append(regressions_section)

    report_string = "\n".join(report_parts)

    # Create sections list
    report_sections = [pipeline_info_section, comparison_table_section, mapping_summary_section, regressions_section]

    # Write to file if output_file is provided
    if output_file:
        with open(output_file, "w") as f:
            f.write(report_string)
        if not quiet:
            print(f"\nFound {len(regressions)} regressions")
            print(f"Output written to: {output_file}")
    else:
        if not quiet:
            print(f"\nFound {len(regressions)} regressions")

    return regressions, report_string, report_sections


def run(
    source_type: str,
    source_value: str,
    baseline_type: str,
    baseline_value: str,
    baseline_project_id: str = None,
    output_file: Optional[str] = None,
    quiet: bool = False,
):
    """
    Main function that fetches test reports from GitLab and compares them.

    Args:
        source_type: Type of source for test pipeline ('branch', 'mr', or 'pipeline')
        source_value: Value for source (branch name, MR IID, or pipeline ID)
        baseline_type: Type of source for baseline pipeline ('branch', 'mr', or 'pipeline')
        baseline_value: Value for baseline (branch name, MR IID, or pipeline ID)
        baseline_project_id: Optional project ID for baseline (defaults to PROJECT_ID)
        output_file: Optional path to write report to file (default: None, no file output)
        quiet: If True, suppress console output from regression analysis (default: False)
    """
    # Connect to GitLab
    if not quiet:
        print(f"\nConnecting to GitLab at {GITLAB_URL}...")
    gl = get_gitlab_client(quiet=quiet)
    if not gl:
        return

    effective_baseline_project = baseline_project_id or PROJECT_ID

    # Fetch baseline pipeline
    if not quiet:
        print(f"\nFetching baseline ({baseline_type}={baseline_value}, project: {effective_baseline_project})...")
    baseline_pipeline, baseline_pipeline_info = get_pipeline(
        gl, baseline_type, baseline_value, effective_baseline_project, quiet=quiet
    )
    if not baseline_pipeline:
        return

    if not quiet:
        print(f"Fetching test report from baseline pipeline #{baseline_pipeline.id}...")
    baseline_data = fetch_test_report_from_pipeline(gl, baseline_pipeline.id, effective_baseline_project)
    if not baseline_data:
        print("ERROR: Failed to fetch baseline test report")
        return

    baseline_analysis = analyze_test_data(baseline_data, f"baseline_pipeline_{baseline_pipeline.id}", quiet=quiet)
    if not baseline_analysis:
        print("ERROR: Failed to analyze baseline data")
        return

    # Fetch test pipeline
    if not quiet:
        print(f"\nFetching test ({source_type}={source_value}, project: {PROJECT_ID})...")
    test_pipeline, test_pipeline_info = get_pipeline(gl, source_type, source_value, PROJECT_ID, quiet=quiet)
    if not test_pipeline:
        return

    if not quiet:
        print(f"Fetching test report from test pipeline #{test_pipeline.id}...")
    test_data = fetch_test_report_from_pipeline(gl, test_pipeline.id, PROJECT_ID)
    if not test_data:
        print("ERROR: Failed to fetch test report")
        return

    test_analysis = analyze_test_data(test_data, f"test_pipeline_{test_pipeline.id}", quiet=quiet)
    if not test_analysis:
        print("ERROR: Failed to analyze test data")
        return

    # Print comparison
    results = {"baseline": baseline_analysis, "test": test_analysis}

    if not quiet:
        print_combined_table(results)

    # Write regression report
    regressions, report_string, report_sections = find_regressions_from_data(
        baseline_data,
        test_data,
        output_file=output_file,
        test_pipeline_info=test_pipeline_info,
        baseline_pipeline_info=baseline_pipeline_info,
        baseline_analysis=baseline_analysis,
        test_analysis=test_analysis,
        quiet=quiet,
    )

    return report_sections


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Compare test reports between two GitLab pipelines and find regressions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment variables (can be set in .env file):
  PRIVATE_TOKEN        GitLab API token (required)
  GITLAB_URL           GitLab server URL (default: https://gitlab-master.nvidia.com)
  PROJECT_ID           Target project ID for test pipeline (required)
  
  SOURCE_TYPE          How to find test pipeline: 'branch', 'mr', or 'pipeline'
  SOURCE_VALUE         The branch name, MR IID, or pipeline ID
  
  BASELINE_TYPE        How to find baseline pipeline: 'branch', 'mr', or 'pipeline'
  BASELINE_VALUE       The branch name, MR IID, or pipeline ID
  BASELINE_PROJECT_ID  Project ID for baseline (defaults to PROJECT_ID)

Examples:
  # Compare MR pipeline against a specific baseline pipeline
  python analyze_test_suites.py --source mr 1234 --baseline pipeline 40500930

  # Compare branch pipeline against another branch
  python analyze_test_suites.py --source branch feature-x --baseline branch develop

  # Compare MR against baseline in different project
  python analyze_test_suites.py --source mr 1234 --baseline pipeline 40500930 --baseline-project 29539

  # Compare two specific pipelines
  python analyze_test_suites.py --source pipeline 12345 --baseline pipeline 67890
  
  # Skip file output (for Slack posting or programmatic use)
  python analyze_test_suites.py --source mr 1234 --baseline pipeline 40500930 --no-output
  
  # Quiet mode with custom output file
  python analyze_test_suites.py --source mr 1234 --baseline pipeline 40500930 --output results.txt --quiet
""",
    )
    parser.add_argument(
        "--source",
        nargs=2,
        metavar=("TYPE", "VALUE"),
        help="Test pipeline source: TYPE is 'branch', 'mr', or 'pipeline'; VALUE is the identifier",
    )
    parser.add_argument(
        "--baseline",
        nargs=2,
        metavar=("TYPE", "VALUE"),
        help="Baseline pipeline source: TYPE is 'branch', 'mr', or 'pipeline'; VALUE is the identifier",
    )
    parser.add_argument(
        "--baseline-project",
        type=str,
        default=None,
        help="Project ID for baseline pipeline (default: same as PROJECT_ID)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="regressions.txt",
        help="Output file path for regression report (default: regressions.txt). Use --no-output to skip file output.",
    )
    parser.add_argument("--no-output", action="store_true", help="Skip writing output to file")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress regression analysis console output")

    args = parser.parse_args()

    # Get source from args or env vars
    if args.source:
        source_type, source_value = args.source
    elif SOURCE_TYPE and SOURCE_VALUE:
        source_type, source_value = SOURCE_TYPE, SOURCE_VALUE
    else:
        print("ERROR: Must specify --source or set SOURCE_TYPE and SOURCE_VALUE env vars")
        print("Use --help for usage information")
        exit(1)

    # Validate source type
    if source_type not in ("branch", "mr", "pipeline"):
        print(f"ERROR: Invalid source type '{source_type}'. Must be 'branch', 'mr', or 'pipeline'.")
        exit(1)

    # Get baseline from args or env vars
    if args.baseline:
        baseline_type, baseline_value = args.baseline
    elif BASELINE_TYPE and BASELINE_VALUE:
        baseline_type, baseline_value = BASELINE_TYPE, BASELINE_VALUE
    else:
        print("ERROR: Must specify --baseline or set BASELINE_TYPE and BASELINE_VALUE env vars")
        print("Use --help for usage information")
        exit(1)

    # Validate baseline type
    if baseline_type not in ("branch", "mr", "pipeline"):
        print(f"ERROR: Invalid baseline type '{baseline_type}'. Must be 'branch', 'mr', or 'pipeline'.")
        exit(1)

    baseline_project = args.baseline_project or BASELINE_PROJECT_ID

    # Determine output file
    output_file = None if args.no_output else args.output

    print("Comparing GitLab pipelines")
    print(f"  Test:     {source_type}={source_value} (project: {PROJECT_ID})")
    print(f"  Baseline: {baseline_type}={baseline_value} (project: {baseline_project or PROJECT_ID})")

    run(
        source_type,
        source_value,
        baseline_type,
        baseline_value,
        baseline_project,
        output_file=output_file,
        quiet=args.quiet,
    )
