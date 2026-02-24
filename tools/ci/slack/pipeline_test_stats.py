#!/usr/bin/env python3
"""
Fetch and display test pass/fail/error statistics for GitLab pipelines.
Shows a table of finished pipelines with their test report summaries.
Generates a stacked bar chart visualization using Plotly.
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import gitlab

# Manually do chrome sync for kaleido to make sure chrome driver is present
import kaleido
import plotly.graph_objects as go
from dotenv import load_dotenv
from plotly.subplots import make_subplots

kaleido.get_chrome_sync()

# Load environment variables from .env file
load_dotenv()

# GitLab configuration from environment
PRIVATE_TOKEN = os.getenv("ISAAC_MAINTAINER_RO_TOKEN", os.getenv("CI_GITLAB_API_TOKEN"))
if PRIVATE_TOKEN is None:
    PRIVATE_TOKEN = os.getenv("PRIVATE_TOKEN")
GITLAB_URL = os.getenv("GITLAB_URL", "https://gitlab-master.nvidia.com")
PROJECT_ID = os.getenv("CI_PROJECT_ID")
if PROJECT_ID is None:
    PROJECT_ID = os.getenv("PROJECT_ID")

# Number of threads for parallel fetching
MAX_WORKERS = 10


def get_gitlab_client(quiet: bool = False) -> Optional[gitlab.Gitlab]:
    """
    Create and authenticate a GitLab client.

    Args:
        quiet: If True, suppress non-error output

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


def fetch_pipeline_data(gl: gitlab.Gitlab, pipeline) -> Tuple[int, Optional[Dict], bool]:
    """
    Fetch test report and check for bump-version job for a single pipeline.
    Thread-safe function for parallel execution.

    Args:
        gl: GitLab client (each thread should use its own)
        pipeline: Pipeline object with basic info

    Returns:
        Tuple of (pipeline_id, test_stats dict or None, has_bump_version)
    """
    try:
        project = gl.projects.get(PROJECT_ID)
        pipeline_obj = project.pipelines.get(pipeline.id)

        # Check for bump-version job
        jobs = pipeline_obj.jobs.list(per_page=100, get_all=True)
        has_bump_version = any("bump-version" in job.name.lower() for job in jobs)

        if has_bump_version:
            return (pipeline.id, None, True)

        # Fetch test report summary (lighter weight, more reliable)
        try:
            summary = pipeline_obj.test_report_summary.get()

            # Get summary stats from test_report_summary
            if hasattr(summary, "total"):
                total_data = summary.total
                if hasattr(total_data, "count"):
                    test_stats = {
                        "total": total_data.count,
                        "success": getattr(total_data, "success", 0),
                        "failed": getattr(total_data, "failed", 0),
                        "error": getattr(total_data, "error", 0),
                        "skipped": getattr(total_data, "skipped", 0),
                    }
                else:
                    test_stats = {
                        "total": total_data.get("count", 0),
                        "success": total_data.get("success", 0),
                        "failed": total_data.get("failed", 0),
                        "error": total_data.get("error", 0),
                        "skipped": total_data.get("skipped", 0),
                    }
            elif hasattr(summary, "_attrs") and "total" in summary._attrs:
                total_data = summary._attrs["total"]
                test_stats = {
                    "total": total_data.get("count", 0),
                    "success": total_data.get("success", 0),
                    "failed": total_data.get("failed", 0),
                    "error": total_data.get("error", 0),
                    "skipped": total_data.get("skipped", 0),
                }
            else:
                # Fallback for dict response
                total_data = summary.get("total", {}) if isinstance(summary, dict) else {}
                test_stats = {
                    "total": total_data.get("count", 0),
                    "success": total_data.get("success", 0),
                    "failed": total_data.get("failed", 0),
                    "error": total_data.get("error", 0),
                    "skipped": total_data.get("skipped", 0),
                }

            # Get per-suite (job) stats from test_suites in summary
            suites = []
            if hasattr(summary, "test_suites"):
                suite_list = summary.test_suites
            elif hasattr(summary, "_attrs") and "test_suites" in summary._attrs:
                suite_list = summary._attrs["test_suites"]
            elif isinstance(summary, dict) and "test_suites" in summary:
                suite_list = summary["test_suites"]
            else:
                suite_list = []

            for suite in suite_list:
                if hasattr(suite, "name"):
                    suite_name = suite.name
                    suite_data = {
                        "name": suite_name,
                        "success": getattr(suite, "success", 0),
                        "failed": getattr(suite, "failed", 0),
                        "error": getattr(suite, "error", 0),
                        "skipped": getattr(suite, "skipped", 0),
                    }
                else:
                    suite_name = suite.get("name", "Unknown")
                    suite_data = {
                        "name": suite_name,
                        "success": suite.get("success", 0),
                        "failed": suite.get("failed", 0),
                        "error": suite.get("error", 0),
                        "skipped": suite.get("skipped", 0),
                    }

                # test_report_summary doesn't include individual test cases
                # We'll need to fetch full test_report for heatmap view
                suite_data["test_cases"] = []
                suites.append(suite_data)

            test_stats["suites"] = suites

            return (pipeline.id, test_stats, False)
        except Exception:
            return (pipeline.id, None, False)

    except Exception:
        return (pipeline.id, None, False)


def fetch_full_test_report(gl: gitlab.Gitlab, pipeline_id: int) -> Optional[List[Dict]]:
    """
    Fetch full test report with suite counts and test cases for a pipeline.
    Used for job-grouped chart and heatmap view.

    Args:
        gl: GitLab client
        pipeline_id: Pipeline ID

    Returns:
        List of suite dicts with counts and test_cases, or None on failure
    """
    try:
        project = gl.projects.get(PROJECT_ID)
        pipeline_obj = project.pipelines.get(pipeline_id)
        test_report = pipeline_obj.test_report.get()

        suites = []
        if hasattr(test_report, "test_suites"):
            suite_list = test_report.test_suites
        elif hasattr(test_report, "_attrs") and "test_suites" in test_report._attrs:
            suite_list = test_report._attrs["test_suites"]
        elif isinstance(test_report, dict) and "test_suites" in test_report:
            suite_list = test_report["test_suites"]
        else:
            suite_list = []

        for suite in suite_list:
            if hasattr(suite, "name"):
                suite_name = suite.name
                suite_data = {
                    "name": suite_name,
                    "success": getattr(suite, "success_count", 0),
                    "failed": getattr(suite, "failed_count", 0),
                    "error": getattr(suite, "error_count", 0),
                    "skipped": getattr(suite, "skipped_count", 0),
                }
                test_cases_raw = getattr(suite, "test_cases", [])
            else:
                suite_name = suite.get("name", "Unknown")
                suite_data = {
                    "name": suite_name,
                    "success": suite.get("success_count", 0),
                    "failed": suite.get("failed_count", 0),
                    "error": suite.get("error_count", 0),
                    "skipped": suite.get("skipped_count", 0),
                }
                test_cases_raw = suite.get("test_cases", [])

            test_cases = []
            for tc in test_cases_raw:
                if hasattr(tc, "name"):
                    system_output = getattr(tc, "system_output", "") or ""
                    stack_trace = getattr(tc, "stack_trace", "") or ""
                    tc_data = {
                        "name": tc.name,
                        "status": getattr(tc, "status", "unknown"),
                        "classname": getattr(tc, "classname", ""),
                        "system_output": system_output,
                        "stack_trace": stack_trace,
                    }
                else:
                    system_output = tc.get("system_output", "") or ""
                    stack_trace = tc.get("stack_trace", "") or ""
                    tc_data = {
                        "name": tc.get("name", "Unknown"),
                        "status": tc.get("status", "unknown"),
                        "classname": tc.get("classname", ""),
                        "system_output": system_output,
                        "stack_trace": stack_trace,
                    }
                test_cases.append(tc_data)

            suite_data["test_cases"] = test_cases
            suites.append(suite_data)

        return suites
    except Exception:
        return None


def is_timeout(tc: Dict) -> bool:
    """
    Check if a test case failure was due to a timeout.

    Args:
        tc: Test case dict with status, system_output, stack_trace

    Returns:
        True if the test appears to have timed out
    """
    # Common timeout indicators in error messages
    timeout_patterns = [
        "timed out",
        "timeout",
        "process timed out",
        "exceeded time limit",
        "deadline exceeded",
        "took too long",
        "time limit",
    ]

    # Check system_output and stack_trace for timeout patterns
    output = (tc.get("system_output", "") or "").lower()
    trace = (tc.get("stack_trace", "") or "").lower()
    combined = output + " " + trace

    return any(pattern in combined for pattern in timeout_patterns)


def get_finished_pipelines(
    gl: gitlab.Gitlab,
    branch: str = "develop",
    limit: int = 20,
    quiet: bool = False,
    variable_filters: Optional[Dict[str, str]] = None,
    pipeline_sources: Optional[List[str]] = None,
) -> List[Dict]:
    """
    Get finished pipelines for a branch with their test report stats.
    Skips pipelines that contain a bump-version job.
    Uses threading for parallel fetching with progress bar.

    Args:
        gl: Authenticated GitLab client
        branch: Branch name to filter pipelines
        limit: Maximum number of pipelines to return (after filtering)
        quiet: If True, suppress progress bar and non-error output
        variable_filters: Optional dict of variable_name: expected_value to filter pipelines
        pipeline_sources: Optional list of acceptable pipeline sources (e.g., ["push", "web", "schedule"])

    Returns:
        List of pipeline info dicts with test stats
    """
    project = gl.projects.get(PROJECT_ID)

    # Fetch finished pipelines (success, failed)
    finished_statuses = ["success", "failed"]

    if not quiet:
        print(f"\nFetching pipelines for branch '{branch}'...")

    # Use iterator to paginate through pipelines
    pipelines_iter = project.pipelines.list(ref=branch, per_page=100, order_by="id", sort="desc", iterator=True)

    # Process pipelines in batches until we have enough valid ones
    pipelines_data = []
    bump_version_count = 0
    batch_size = 50

    # Conditionally import and use tqdm
    if not quiet:
        from tqdm import tqdm

        pbar = tqdm(total=limit, desc="Fetching pipeline data", unit="pipeline")
    else:
        pbar = None

    try:
        while len(pipelines_data) < limit:
            # Collect next batch of finished pipelines
            batch = []
            for p in pipelines_iter:
                if p.status in finished_statuses:
                    batch.append(p)
                if len(batch) >= batch_size:
                    break

            if not batch:
                # No more pipelines available
                break

            # Fetch data for this batch in parallel
            batch_results = {}
            batch_bump_version = set()

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                future_to_pipeline = {
                    executor.submit(
                        fetch_pipeline_data, gitlab.Gitlab(url=GITLAB_URL, private_token=PRIVATE_TOKEN), p
                    ): p
                    for p in batch
                }

                for future in as_completed(future_to_pipeline):
                    pipeline = future_to_pipeline[future]
                    try:
                        pipeline_id, test_stats, has_bump_version = future.result()

                        if has_bump_version:
                            batch_bump_version.add(pipeline_id)
                        else:
                            batch_results[pipeline_id] = test_stats
                    except Exception:
                        pass

            # Add valid pipelines from this batch (maintaining order)
            for pipeline in batch:
                if len(pipelines_data) >= limit:
                    break

                if pipeline.id in batch_bump_version:
                    bump_version_count += 1
                    continue

                # Only add if we have actual test stats (not None)
                if pipeline.id in batch_results and batch_results[pipeline.id] is not None:
                    # Check pipeline source filter if provided
                    if pipeline_sources:
                        if pipeline.source not in pipeline_sources:
                            continue

                    # Check variable filters if provided
                    if variable_filters:
                        # Fetch full pipeline object to get variables
                        full_pipeline = project.pipelines.get(pipeline.id)
                        pipeline_vars = {var.key: var.value for var in full_pipeline.variables.list(get_all=True)}

                        # Check if all filters match
                        matches = all(pipeline_vars.get(key) == value for key, value in variable_filters.items())

                        if not matches:
                            continue

                    pipeline_info = {
                        "id": pipeline.id,
                        "status": pipeline.status,
                        "ref": pipeline.ref,
                        "created_at": pipeline.created_at,
                        "web_url": pipeline.web_url,
                        "test_stats": batch_results[pipeline.id],
                    }
                    pipelines_data.append(pipeline_info)
                    if pbar:
                        pbar.update(1)
    finally:
        if pbar:
            pbar.close()

    if bump_version_count and not quiet:
        print(f"Skipped {bump_version_count} pipelines with bump-version jobs")

    return pipelines_data


def print_pipeline_table(pipelines: List[Dict]):
    """
    Print a formatted table of pipelines with test stats.

    Args:
        pipelines: List of pipeline info dicts
    """
    if not pipelines:
        print("\nNo finished pipelines found.")
        return

    # Table header
    print("\n" + "=" * 130)
    print(f"{'Pipeline ID':>12} {'Status':>10} {'Pass':>8} {'Fail':>8} {'Error':>8} {'Skip':>8} {'Total':>8}   {'URL'}")
    print("=" * 130)

    for p in pipelines:
        stats = p.get("test_stats")

        if stats:
            pass_count = stats["success"]
            fail_count = stats["failed"]
            error_count = stats["error"]
            skip_count = stats["skipped"]
            total_count = stats["total"]
        else:
            pass_count = "-"
            fail_count = "-"
            error_count = "-"
            skip_count = "-"
            total_count = "-"

        print(
            f"{p['id']:>12} {p['status']:>10} {pass_count:>8} {fail_count:>8} {error_count:>8} {skip_count:>8} {total_count:>8}   {p['web_url']}"
        )

    print("=" * 130)

    # Summary
    pipelines_with_stats = [p for p in pipelines if p.get("test_stats")]
    print(f"\nTotal pipelines shown: {len(pipelines)}")
    print(f"Pipelines with test reports: {len(pipelines_with_stats)}")


def create_stacked_bar_chart(pipelines: List[Dict], output_file: str = "pipeline_test_chart.html", quiet: bool = False):
    """
    Create a stacked bar chart of test results per pipeline.

    Args:
        pipelines: List of pipeline info dicts with test stats
        output_file: Path to save the HTML chart
        quiet: If True, suppress output and don't open browser
    """
    # Filter to only pipelines with test stats and reverse for chronological order
    pipelines_with_stats = [p for p in pipelines if p.get("test_stats")]
    pipelines_with_stats = list(reversed(pipelines_with_stats))  # Oldest first

    if not pipelines_with_stats:
        print("\nNo pipelines with test data to chart.")
        return

    # Extract data for chart - use list indices for x-axis, custom tick labels for display
    x_indices = list(range(len(pipelines_with_stats)))

    # Build tick labels - HTML version (with line breaks) and PNG version (date only)
    tick_labels_html = []
    tick_labels_png = []
    for p in pipelines_with_stats:
        created_at = p.get("created_at", "")
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                date_str = dt.strftime("%m/%d %H:%M")
                tick_labels_html.append(f"#{p['id']}<br>{date_str}")
                tick_labels_png.append(date_str)
            except Exception:
                tick_labels_html.append(f"#{p['id']}")
                tick_labels_png.append(f"#{p['id']}")
        else:
            tick_labels_html.append(f"#{p['id']}")
            tick_labels_png.append(f"#{p['id']}")

    fails = [p["test_stats"]["failed"] for p in pipelines_with_stats]
    errors = [p["test_stats"]["error"] for p in pipelines_with_stats]
    urls = [p["web_url"] for p in pipelines_with_stats]

    # Create stacked bar chart
    fig = go.Figure()

    # Add traces in order: fails on bottom, then errors (no skips)
    fig.add_trace(
        go.Bar(
            name="Failed",
            x=x_indices,
            y=fails,
            marker_color="#e74c3c",
            customdata=urls,
            hovertemplate="<b>%{text}</b><br>Failed: %{y}<extra></extra>",
            text=tick_labels_html,
        )
    )

    fig.add_trace(
        go.Bar(
            name="Errors",
            x=x_indices,
            y=errors,
            marker_color="#e67e22",
            customdata=urls,
            hovertemplate="<b>%{text}</b><br>Errors: %{y}<extra></extra>",
            text=tick_labels_html,
        )
    )

    # Update layout
    fig.update_layout(
        barmode="stack",
        title={"text": "Pipeline Test Results", "x": 0.5, "xanchor": "center", "font": {"size": 24}},
        xaxis_title="Pipeline",
        yaxis_title="Test Count",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        template="plotly_dark",
        width=1400,
        height=600,
        margin=dict(l=60, r=20, t=80, b=80),
    )

    # Set custom tick labels with HTML rendering
    fig.update_xaxes(
        tickmode="array",
        tickvals=x_indices,
        ticktext=tick_labels_html,
        tickangle=45 if len(tick_labels_html) > 10 else 0,
    )

    # Build test report URLs for each pipeline
    import json as json_module

    test_report_urls = [f"{p['web_url']}/test_report" for p in pipelines_with_stats]

    # Save base HTML first
    fig.write_html(output_file, include_plotlyjs=True, full_html=True, div_id="plotly-chart")

    # Read the HTML and inject click handler before closing body tag
    with open(output_file, "r") as f:
        html_content = f.read()

    click_js = f"""
<script>
var defined_urls = {json_module.dumps(test_report_urls)};
var plot = document.getElementById('plotly-chart');
plot.on('plotly_click', function(data) {{
    var pointIndex = data.points[0].pointIndex;
    if (defined_urls[pointIndex]) {{
        window.open(defined_urls[pointIndex], '_blank');
    }}
}});
</script>
</body>"""

    html_content = html_content.replace("</body>", click_js)

    with open(output_file, "w") as f:
        f.write(html_content)

    if not quiet:
        print(f"\nChart saved to: {output_file} (standalone HTML, click bars to open test report)")

    # Also save as PNG with simpler labels (date only, no overlap)
    fig.update_xaxes(ticktext=tick_labels_png)
    png_file = output_file.replace(".html", ".png")
    fig.write_image(png_file, scale=2)
    if not quiet:
        print(f"Chart saved to: {png_file}")

    # Open HTML file in browser (only if not quiet)
    if not quiet:
        import webbrowser

        webbrowser.open(f"file://{os.path.abspath(output_file)}")


def _strip_inline_from_job_name(name: str) -> str:
    """If job name contains ', inline]', normalize to ']' so inline and after_script jobs match."""
    if ", inline]" in name:
        return name.replace(", inline]", "]")
    return name


def parse_job_name(job_name: str) -> Tuple[str, str, str]:
    """
    Parse a job name into its components: base name, OS, and bucket (matrix args).

    Args:
        job_name: Full job name like "tests-linux-x86_64-pythontests [arg1, arg2]"

    Returns:
        Tuple of (base_name, os_name, bucket)
        e.g., ("pythontests", "linux", "arg1, arg2")
    """
    job_name = _strip_inline_from_job_name(job_name)

    # Extract bucket from square brackets
    bucket = ""
    base = job_name
    if "[" in job_name:
        bracket_start = job_name.index("[")
        bracket_end = job_name.rindex("]") if "]" in job_name else len(job_name)
        bucket = job_name[bracket_start + 1 : bracket_end].strip()
        base = job_name[:bracket_start].strip()

    # Detect OS from base name
    os_name = "other"
    if "linux" in base.lower():
        os_name = "linux"
    elif "windows" in base.lower():
        os_name = "windows"

    # Extract the test type (last part of base name after OS info)
    # e.g., "tests-linux-x86_64-pythontests" -> "pythontests"
    parts = base.split("-")
    # Find the test type - usually the last meaningful part
    test_type = base
    if len(parts) >= 2:
        # Skip "tests" prefix and OS/arch parts
        test_type = parts[-1] if parts[-1] not in ("x86_64", "aarch64", "arm64") else parts[-2]

    return (test_type, os_name, bucket)


def create_job_grouped_chart(
    pipelines: List[Dict], output_file: str = "pipeline_test_by_job.html", quiet: bool = False
):
    """
    Create a chart showing combined fails/errors by bucket (matrix args) for each pipeline.
    Each bucket gets the same color, with adjacent bars for different OSes.

    Args:
        pipelines: List of pipeline info dicts with test stats including suites
        output_file: Path to save the HTML chart
        quiet: If True, suppress output and don't open browser
    """
    # Filter to only pipelines with test stats
    pipelines_with_stats = [p for p in pipelines if p.get("test_stats")]
    pipelines_with_stats = list(reversed(pipelines_with_stats))  # Oldest first

    if not pipelines_with_stats:
        print("\nNo pipelines with test data to chart.")
        return

    # Fetch full test_report for suite data (test_report_summary may not have it)
    if not quiet:
        print("\nFetching full test reports for job-grouped chart...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_pipeline = {
            executor.submit(
                fetch_full_test_report, gitlab.Gitlab(url=GITLAB_URL, private_token=PRIVATE_TOKEN), p["id"]
            ): p
            for p in pipelines_with_stats
        }

        if not quiet:
            from tqdm import tqdm

            pbar = tqdm(total=len(future_to_pipeline), desc="Fetching test reports", unit="pipeline")
        else:
            pbar = None

        try:
            for future in as_completed(future_to_pipeline):
                p = future_to_pipeline[future]
                try:
                    suites = future.result()
                    if suites is not None:
                        p["test_stats"]["suites"] = suites
                except Exception:
                    pass
                if pbar:
                    pbar.update(1)
        finally:
            if pbar:
                pbar.close()

    # Filter to only pipelines that have suite data
    pipelines_with_stats = [p for p in pipelines_with_stats if p["test_stats"].get("suites")]

    if not pipelines_with_stats:
        print("\nNo pipelines with per-job test data to chart.")
        return

    # Collect all unique buckets and OSes across all pipelines
    all_buckets = set()
    all_oses = set()
    for p in pipelines_with_stats:
        for suite in p["test_stats"].get("suites", []):
            test_type, os_name, bucket = parse_job_name(suite["name"])
            if bucket:  # Only include jobs with matrix args
                all_buckets.add(bucket)
                all_oses.add(os_name)

    # Sort for consistent ordering
    all_buckets = sorted(all_buckets)
    all_oses = sorted(all_oses)  # e.g., ['linux', 'windows']

    if not all_buckets:
        if not quiet:
            print("\nNo bucket data found in test reports.")
        return

    # Build pipeline labels - HTML version and PNG version
    pipeline_labels_html = []
    pipeline_labels_png = []
    for p in pipelines_with_stats:
        created_at = p.get("created_at", "")
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                date_str = dt.strftime("%m/%d %H:%M")
                pipeline_labels_html.append(f"#{p['id']}<br>{date_str}")
                pipeline_labels_png.append(date_str)
            except Exception:
                pipeline_labels_html.append(f"#{p['id']}")
                pipeline_labels_png.append(f"#{p['id']}")
        else:
            pipeline_labels_html.append(f"#{p['id']}")
            pipeline_labels_png.append(f"#{p['id']}")

    x_indices = list(range(len(pipelines_with_stats)))

    # Create figure with grouped bars
    fig = go.Figure()

    # Generate colors for each bucket
    colors = [
        "#e74c3c",
        "#e67e22",
        "#f1c40f",
        "#2ecc71",
        "#1abc9c",
        "#3498db",
        "#9b59b6",
        "#34495e",
        "#e91e63",
        "#00bcd4",
        "#8bc34a",
        "#ff5722",
        "#795548",
        "#607d8b",
        "#673ab7",
    ]

    # Track all traces for URL mapping
    trace_info = []  # List of (bucket, os, job_names_per_pipeline) for URL mapping

    # For each bucket, create bar traces for each OS (same color, stacked together)
    # This creates stacked bars where same-bucket segments are adjacent in the stack
    for bucket_idx, bucket in enumerate(all_buckets):
        color = colors[bucket_idx % len(colors)]

        for os_idx, os_name in enumerate(all_oses):
            # Extract combined fails + errors for this bucket+OS across all pipelines
            combined = []
            matching_job_names = []  # Track actual job names for URL mapping

            for p in pipelines_with_stats:
                total = 0
                job_name_for_pipeline = None
                for suite in p["test_stats"].get("suites", []):
                    _, suite_os, suite_bucket = parse_job_name(suite["name"])
                    if suite_bucket == bucket and suite_os == os_name:
                        total += suite.get("failed", 0) + suite.get("error", 0)
                        job_name_for_pipeline = suite["name"]
                combined.append(total)
                matching_job_names.append(job_name_for_pipeline)

            # Shorten bucket name for display
            short_bucket = bucket
            if len(short_bucket) > 25:
                short_bucket = bucket[:22] + "..."

            # Display name includes OS
            display_name = f"{short_bucket} ({os_name})"

            fig.add_trace(
                go.Bar(
                    name=display_name,
                    x=x_indices,
                    y=combined,
                    marker_color=color,  # Same color for same bucket
                    hovertemplate=f"<b>{display_name}</b><br>Fails+Errors: %{{y}}<extra></extra>",
                )
            )

            # Track for URL mapping
            trace_info.append((bucket, os_name, matching_job_names))

    # Update layout - stacked bars (one column per pipeline)
    fig.update_layout(
        barmode="stack",
        title={"text": "Pipeline Fails + Errors by Bucket", "x": 0.5, "xanchor": "center", "font": {"size": 24}},
        xaxis_title="Pipeline",
        yaxis_title="Fails + Errors",
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        template="plotly_dark",
        width=1400,
        height=600,
        margin=dict(l=60, r=250, t=80, b=80),  # More room for legend
    )

    # Set custom tick labels
    fig.update_xaxes(tickmode="array", tickvals=x_indices, ticktext=pipeline_labels_html, tickangle=45)

    # Build URL mapping: for each trace, map pipeline index to test report URL
    import json as json_module
    from urllib.parse import quote

    # Create a mapping from (trace_index, pipeline_index) -> URL
    url_map = {}
    for trace_idx, (bucket, os_name, job_names) in enumerate(trace_info):
        url_map[trace_idx] = {}
        for pipeline_idx, job_name in enumerate(job_names):
            if job_name:
                encoded_job = quote(job_name, safe="")
                url_map[trace_idx][
                    pipeline_idx
                ] = f"{pipelines_with_stats[pipeline_idx]['web_url']}/test_report?job_name={encoded_job}"

    # Save base HTML first
    fig.write_html(output_file, include_plotlyjs=True, full_html=True, div_id="plotly-chart")

    # Read the HTML and inject click handler before closing body tag
    with open(output_file, "r") as f:
        html_content = f.read()

    click_js = f"""
<script>
var url_map = {json_module.dumps(url_map)};
var plot = document.getElementById('plotly-chart');
plot.on('plotly_click', function(data) {{
    var pointIndex = data.points[0].pointIndex;
    var curveNumber = data.points[0].curveNumber;
    if (url_map[curveNumber] && url_map[curveNumber][pointIndex]) {{
        window.open(url_map[curveNumber][pointIndex], '_blank');
    }}
}});
</script>
</body>"""

    html_content = html_content.replace("</body>", click_js)

    with open(output_file, "w") as f:
        f.write(html_content)

    if not quiet:
        print(f"\nJob-grouped chart saved to: {output_file} (standalone HTML, click bars to open job test report)")

    # Also save as PNG with simpler labels (date only)
    fig.update_xaxes(ticktext=pipeline_labels_png)
    png_file = output_file.replace(".html", ".png")
    fig.write_image(png_file, scale=2)
    if not quiet:
        print(f"Chart saved to: {png_file}")

    # Open HTML file in browser (only if not quiet)
    if not quiet:
        import webbrowser

        webbrowser.open(f"file://{os.path.abspath(output_file)}")


def create_test_heatmap(
    pipelines: List[Dict],
    output_file: str = "pipeline_test_heatmap.html",
    exclude_patterns: Optional[List[str]] = None,
    quiet: bool = False,
    debug_output: bool = False,
    subtitle: Optional[str] = None,
):
    """
    Create a heatmap showing individual test pass/fail status across pipelines.
    Each job gets its own heatmap with tests as rows and pipelines as columns.

    Args:
        pipelines: List of pipeline info dicts with test stats including test cases
        output_file: Path to save the HTML chart
        exclude_patterns: List of substrings to exclude jobs by (e.g., ["integration-nightly"])
        quiet: If True, suppress output and don't open browser
        debug_output: If True, print detailed debug information about subplot allocation
        subtitle: Optional second line title (subtitle) for the heatmap chart
    """
    if exclude_patterns is None:
        exclude_patterns = []

    def should_exclude_job(job_name: str) -> bool:
        """Check if a job should be excluded based on substring patterns."""
        return any(pattern in job_name for pattern in exclude_patterns)

    # Filter to only pipelines with test stats and suites
    pipelines_with_stats = [p for p in pipelines if p.get("test_stats") and p["test_stats"].get("suites")]
    pipelines_with_stats = list(reversed(pipelines_with_stats))  # Oldest first

    if not pipelines_with_stats:
        print("\nNo pipelines with test case data to chart.")
        return

    # Check if we need to fetch full test case data (test_report_summary doesn't include it)
    needs_full_fetch = False
    for p in pipelines_with_stats:
        for suite in p["test_stats"].get("suites", []):
            if not suite.get("test_cases"):
                needs_full_fetch = True
                break
        if needs_full_fetch:
            break

    if needs_full_fetch:
        if not quiet:
            print("\nFetching full test case data for heatmap...")

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_pipeline = {
                executor.submit(
                    fetch_full_test_report, gitlab.Gitlab(url=GITLAB_URL, private_token=PRIVATE_TOKEN), p["id"]
                ): p
                for p in pipelines_with_stats
            }

            if not quiet:
                from tqdm import tqdm

                pbar = tqdm(total=len(future_to_pipeline), desc="Fetching test cases", unit="pipeline")
            else:
                pbar = None

            try:
                for future in as_completed(future_to_pipeline):
                    p = future_to_pipeline[future]
                    try:
                        suites = future.result()
                        if suites:
                            # Replace suite data with full data including test_cases
                            p["test_stats"]["suites"] = suites
                    except Exception:
                        pass
                    if pbar:
                        pbar.update(1)
            finally:
                if pbar:
                    pbar.close()

    # Filter out pipelines that don't have any test cases (would show as blank columns)
    # This happens when test reports are missing or incomplete
    pipelines_with_test_cases = []
    for p in pipelines_with_stats:
        has_test_cases = False
        for suite in p["test_stats"].get("suites", []):
            if suite.get("test_cases"):
                has_test_cases = True
                break
        if has_test_cases:
            pipelines_with_test_cases.append(p)

    if not pipelines_with_test_cases:
        if not quiet:
            print("\nNo pipelines with test case data to display in heatmap.")
        return

    # Use the filtered list for the rest of the function
    pipelines_with_stats = pipelines_with_test_cases

    if not quiet and len(pipelines_with_test_cases) < len(pipelines):
        skipped = len(pipelines) - len(pipelines_with_test_cases)
        print(f"Filtered out {skipped} pipelines without test case data")

    # Collect all jobs and their test cases (normalize job name so ", inline]" is stripped for grouping)
    job_tests = {}  # job_name -> set of test names
    excluded_jobs = set()
    for p in pipelines_with_stats:
        for suite in p["test_stats"].get("suites", []):
            job_name = _strip_inline_from_job_name(suite["name"])
            if should_exclude_job(job_name):
                excluded_jobs.add(job_name)
                continue
            if job_name not in job_tests:
                job_tests[job_name] = set()
            for tc in suite.get("test_cases", []):
                # Only track tests that have failed/errored at least once
                if tc["status"] in ("failed", "error"):
                    job_tests[job_name].add(tc["name"])

    if excluded_jobs and not quiet:
        print(
            f"Excluded {len(excluded_jobs)} jobs matching patterns: {', '.join(sorted(excluded_jobs)[:5])}{'...' if len(excluded_jobs) > 5 else ''}"
        )

    # Filter to only jobs with failing tests
    job_tests = {k: sorted(v) for k, v in job_tests.items() if v}

    if not job_tests:
        if not quiet:
            print("\nNo failing tests found across pipelines.")
        return

    # Build pipeline labels - HTML version and PNG version
    pipeline_labels_html = []
    pipeline_labels_png = []
    for p in pipelines_with_stats:
        created_at = p.get("created_at", "")
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                date_str = dt.strftime("%m/%d %H:%M")
                pipeline_labels_html.append(f"#{p['id']}<br>{date_str}")
                pipeline_labels_png.append(date_str)
            except Exception:
                pipeline_labels_html.append(f"#{p['id']}")
                pipeline_labels_png.append(f"#{p['id']}")
        else:
            pipeline_labels_html.append(f"#{p['id']}")
            pipeline_labels_png.append(f"#{p['id']}")

    # Create a separate heatmap for each job
    all_jobs = sorted(job_tests.keys())

    # Strip "tests-" prefix from job names if all jobs have it
    def strip_common_prefix(names):
        if all(name.startswith("tests-") for name in names):
            return [name[6:] for name in names]  # Remove "tests-" (6 chars)
        return names

    display_jobs = strip_common_prefix(all_jobs)

    # Calculate total rows needed for subplot heights
    total_tests = sum(len(tests) for tests in job_tests.values())

    # Create subplots - one per job (use display names for titles)
    # Give each subplot a height proportional to its test count (no cap)
    test_counts = [len(job_tests[job]) for job in all_jobs]

    # DEBUG: Print subplot information
    if debug_output:
        print("\n" + "=" * 80)
        print("HEATMAP SUBPLOT HEIGHT ALLOCATION")
        print("=" * 80)
        print(f"Total failing tests across all jobs: {total_tests}")
        print(f"Number of jobs with failing tests: {len(all_jobs)}")
        print(f"Number of pipelines being displayed: {len(pipelines_with_stats)}")
        print("\nPer-job breakdown:")
        for idx, job_name in enumerate(all_jobs):
            count = test_counts[idx]
            display_name = display_jobs[idx]
            percentage = (count / total_tests * 100) if total_tests > 0 else 0
            print(f"  {display_name:60s} | Tests: {count:4d} ({percentage:5.1f}%)")
        print("=" * 80 + "\n")

    # Normalize to fractions that sum to 1.0
    total_height_units = sum(test_counts)
    row_heights = [count / total_height_units for count in test_counts]

    num_rows = len(all_jobs)
    # Calculate vertical spacing - need room for titles between subplots
    # Allocate 30 pixels per title, calculate as fraction of total height
    pixels_per_test = 30  # Target height per test row
    title_pixels = 40  # Height for each subplot title
    total_pixel_height = (pixels_per_test * total_tests) + (title_pixels * num_rows)

    # Vertical spacing as fraction of figure height
    if num_rows > 1:
        spacing_pixels = title_pixels
        vertical_spacing = spacing_pixels / total_pixel_height
        # Cap at safe maximum
        max_spacing = 0.9 / (num_rows - 1)
        vertical_spacing = min(vertical_spacing, max_spacing)
    else:
        vertical_spacing = 0.1

    fig = make_subplots(
        rows=num_rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=vertical_spacing,
        subplot_titles=display_jobs,
        row_heights=row_heights,
    )

    for job_idx, job_name in enumerate(all_jobs):
        row = job_idx + 1
        test_names = job_tests[job_name]

        # DEBUG: Show actual row count being added
        if debug_output and len(test_names) > 20:
            print(f"DEBUG: Adding {len(test_names)} rows to subplot for {display_jobs[job_idx]}")

        # Build the heatmap data matrix
        # Rows = tests, Columns = pipelines
        # Values (0-5 scale for clean colorscale mapping):
        # 0 = failed (red), 1 = error (purple), 2 = timeout (cyan),
        # 3 = not run (dark gray), 4 = skipped (light gray), 5 = pass (green)
        z_data = []
        hover_text = []

        # Constants for z values
        Z_FAILED = 0
        Z_ERROR = 1
        Z_TIMEOUT = 2
        Z_NOT_RUN = 3
        Z_SKIPPED = 4
        Z_PASS = 5

        for test_name in test_names:
            row_data = []
            row_hover = []

            for p in pipelines_with_stats:
                # Find this test in this pipeline's suite (match normalized job name)
                tc_found = None
                for suite in p["test_stats"].get("suites", []):
                    if _strip_inline_from_job_name(suite["name"]) == job_name:
                        for tc in suite.get("test_cases", []):
                            if tc["name"] == test_name:
                                tc_found = tc
                                break
                    if tc_found is not None:
                        break

                if tc_found is None:
                    row_data.append(Z_NOT_RUN)
                    row_hover.append(f"{test_name}<br>Status: NOT RUN<br>Pipeline: #{p['id']}")
                elif tc_found["status"] == "success":
                    row_data.append(Z_PASS)
                    row_hover.append(f"{test_name}<br>Status: PASS<br>Pipeline: #{p['id']}")
                elif tc_found["status"] == "failed":
                    row_data.append(Z_FAILED)
                    row_hover.append(f"{test_name}<br>Status: FAILED<br>Pipeline: #{p['id']}")
                elif tc_found["status"] == "error":
                    # Check if it's a timeout
                    if is_timeout(tc_found):
                        row_data.append(Z_TIMEOUT)
                        row_hover.append(f"{test_name}<br>Status: TIMEOUT<br>Pipeline: #{p['id']}")
                    else:
                        row_data.append(Z_ERROR)
                        row_hover.append(f"{test_name}<br>Status: ERROR<br>Pipeline: #{p['id']}")
                elif tc_found["status"] == "skipped":
                    row_data.append(Z_SKIPPED)
                    row_hover.append(f"{test_name}<br>Status: SKIPPED<br>Pipeline: #{p['id']}")
                else:
                    # Unknown status - treat as not run but show actual status
                    row_data.append(Z_NOT_RUN)
                    row_hover.append(f"{test_name}<br>Status: {tc_found['status']}<br>Pipeline: #{p['id']}")

            z_data.append(row_data)
            hover_text.append(row_hover)

        # Truncate long test names for y-axis labels
        # Show the END of the name (most specific part) rather than the beginning
        y_labels = []
        for name in test_names:
            if len(name) > 60:
                # Show last 57 chars + "..." at the start to preserve the unique part
                y_labels.append("..." + name[-57:])
            else:
                y_labels.append(name)

        # Use numeric y-indices to prevent Plotly from reordering categorical y-values
        # This ensures hover_text stays aligned with z_data
        y_indices = list(range(len(test_names)))

        # Create discrete colorscale with sharp boundaries at each integer value
        # Using zmin=-0.5 and zmax=5.5 so each integer (0-5) falls in the center of its color band
        # Total range = 6, each band = 1/6 ≈ 0.1667
        # Boundaries: 0→0.1667, 0.1667→0.3333, 0.3333→0.5, 0.5→0.6667, 0.6667→0.8333, 0.8333→1.0
        b = 1 / 6  # boundary width
        fig.add_trace(
            go.Heatmap(
                z=z_data,
                x=list(range(len(pipelines_with_stats))),
                y=y_indices,
                colorscale=[
                    [0.0, "#e74c3c"],  # 0 = red (failed)
                    [b - 0.001, "#e74c3c"],
                    [b, "#9b59b6"],  # 1 = purple (error)
                    [2 * b - 0.001, "#9b59b6"],
                    [2 * b, "#00bcd4"],  # 2 = cyan (timeout)
                    [3 * b - 0.001, "#00bcd4"],
                    [3 * b, "#3d3d3d"],  # 3 = dark gray (not run)
                    [4 * b - 0.001, "#3d3d3d"],
                    [4 * b, "#7f8c8d"],  # 4 = light gray (skipped)
                    [5 * b - 0.001, "#7f8c8d"],
                    [5 * b, "#2ecc71"],  # 5 = green (pass)
                    [1.0, "#2ecc71"],
                ],
                zmin=-0.5,
                zmax=5.5,
                showscale=False,
                hovertext=hover_text,
                hovertemplate="%{hovertext}<extra></extra>",
                xgap=2,
                ygap=2,
            ),
            row=row,
            col=1,
        )

    # Update layout - use the calculated total height
    base_height = 150  # For title and margins

    legend_line = (
        '<sup style="font-size:12px">🟢 Pass | ⬜ Skipped | ⬛ Not Run | 🔵 Timeout | 🟣 Error | 🔴 Failed</sup>'
    )
    title_text = "Test Results Heatmap by Job"
    if subtitle:
        title_text += f'<br><span style="font-size:14px">{subtitle}</span>'
    title_text += f"<br>{legend_line}"

    # Extra top margin when subtitle is present so title + subtitle + legend don't overlap the chart
    top_margin = 160 if subtitle else 100

    fig.update_layout(
        title={
            "text": title_text,
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 24},
        },
        template="plotly_dark",
        height=max(400, base_height + total_pixel_height),
        width=1400,  # Wider chart
        margin=dict(l=300, r=20, t=top_margin, b=80),
    )

    # Add y-axis configuration for each subplot
    # We need to set tick labels for each subplot since we're using numeric y-indices
    for job_idx, job_name in enumerate(all_jobs):
        row = job_idx + 1
        test_names = job_tests[job_name]

        # Rebuild y_labels for this job (same logic as above)
        y_labels = []
        for name in test_names:
            if len(name) > 60:
                y_labels.append("..." + name[-57:])
            else:
                y_labels.append(name)

        fig.update_yaxes(
            title_text="Test Cases",
            title_font=dict(size=10),
            tickfont=dict(size=9),
            tickmode="array",
            tickvals=list(range(len(test_names))),
            ticktext=y_labels,
            row=row,
            col=1,
        )

    # Set x-axis tick labels on bottom subplot only
    fig.update_xaxes(
        tickmode="array",
        tickvals=list(range(len(pipelines_with_stats))),
        ticktext=pipeline_labels_html,
        tickangle=45,
        row=num_rows,
        col=1,
    )

    # Build URL mapping for heatmap clicks
    # Map (job_index, pipeline_index) -> test report URL with job filter
    import json as json_module
    from urllib.parse import quote

    url_map = {}
    for job_idx, job_name in enumerate(all_jobs):
        url_map[job_idx] = {}
        for p_idx, p in enumerate(pipelines_with_stats):
            encoded_job = quote(job_name, safe="")
            url_map[job_idx][p_idx] = f"{p['web_url']}/test_report?job_name={encoded_job}"

    # Save base HTML first
    fig.write_html(output_file, include_plotlyjs=True, full_html=True, div_id="plotly-chart")

    # Read the HTML and inject click handler before closing body tag
    with open(output_file, "r") as f:
        html_content = f.read()

    click_js = f"""
<script>
var url_map = {json_module.dumps(url_map)};
var plot = document.getElementById('plotly-chart');
plot.on('plotly_click', function(data) {{
    var curveNumber = data.points[0].curveNumber;
    var x = data.points[0].x;
    if (url_map[curveNumber] && url_map[curveNumber][x]) {{
        window.open(url_map[curveNumber][x], '_blank');
    }}
}});
</script>
</body>"""

    html_content = html_content.replace("</body>", click_js)

    with open(output_file, "w") as f:
        f.write(html_content)

    if not quiet:
        print(f"\nTest heatmap saved to: {output_file} (standalone HTML, click cells to open job test report)")

    # Also save as PNG with simpler labels (date only)
    fig.update_xaxes(ticktext=pipeline_labels_png, row=num_rows, col=1)
    png_file = output_file.replace(".html", ".png")
    fig.write_image(png_file, scale=1)
    if not quiet:
        print(f"Chart saved to: {png_file}")

    # Open HTML file in browser (only if not quiet)
    if not quiet:
        import webbrowser

        webbrowser.open(f"file://{os.path.abspath(output_file)}")


def run(
    branch: str = "develop",
    limit: int = 150,
    stacked_chart: bool = True,
    output_chart: str = "pipeline_test_chart.html",
    by_job: bool = False,
    heatmap: bool = False,
    exclude_patterns: Optional[List[str]] = None,
    quiet: bool = False,
    debug_output: bool = False,
    variable_filters: Optional[Dict[str, str]] = None,
    pipeline_sources: Optional[List[str]] = None,
    heatmap_subtitle: Optional[str] = None,
):
    """
    Main function to fetch and display pipeline test stats.

    Args:
        branch: Branch name to filter pipelines
        limit: Maximum number of pipelines to fetch
        output_chart: Path to save the HTML chart
        by_job: If True, also create a chart grouped by job
        heatmap: If True, also create a heatmap of individual test results
        exclude_patterns: List of substrings to exclude jobs from heatmap
        quiet: If True, suppress all non-error output, progress bars, and browser opening
        debug_output: If True, print detailed debug information
        variable_filters: Optional dict of variable_name: expected_value to filter pipelines
        pipeline_sources: Optional list of acceptable pipeline sources (e.g., ["push", "web", "schedule"])
        heatmap_subtitle: Optional second line title for the heatmap chart
    """

    kaleido.get_chrome_sync()

    if not quiet:
        print(f"\nConnecting to GitLab at {GITLAB_URL}...")
    gl = get_gitlab_client(quiet=quiet)
    if not gl:
        return

    pipelines = get_finished_pipelines(
        gl, branch, limit, quiet=quiet, variable_filters=variable_filters, pipeline_sources=pipeline_sources
    )
    if not quiet:
        print_pipeline_table(pipelines)
    if stacked_chart:
        create_stacked_bar_chart(pipelines, output_chart, quiet=quiet)

    if by_job:
        job_chart_file = output_chart.replace(".html", "_by_job.html")
        create_job_grouped_chart(pipelines, job_chart_file, quiet=quiet)

    if heatmap:
        heatmap_file = output_chart.replace(".html", "_heatmap.html")
        create_test_heatmap(
            pipelines,
            heatmap_file,
            exclude_patterns=exclude_patterns,
            quiet=quiet,
            debug_output=debug_output,
            subtitle=heatmap_subtitle,
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Display test pass/fail/error statistics for GitLab pipelines",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment variables (can be set in .env file):
  PRIVATE_TOKEN        GitLab API token (required)
  GITLAB_URL           GitLab server URL (default: https://gitlab-master.nvidia.com)
  PROJECT_ID           Target project ID (required)

Examples:
  # Show last 20 pipelines from develop branch
  python pipeline_test_stats.py

  # Show last 50 pipelines from develop branch
  python pipeline_test_stats.py --limit 50

  # Show pipelines from a different branch
  python pipeline_test_stats.py --branch main

  # Show pipelines with per-job breakdown
  python pipeline_test_stats.py --by-job

  # Show pipelines with test heatmap (individual test pass/fail)
  python pipeline_test_stats.py --heatmap

  # Show heatmap but exclude jobs containing "integration-nightly"
  python pipeline_test_stats.py --heatmap --exclude integration-nightly

  # Exclude multiple patterns from heatmap
  python pipeline_test_stats.py --heatmap --exclude integration-nightly --exclude slow-tests

  # Show all visualizations
  python pipeline_test_stats.py --by-job --heatmap

  # Show pipelines from feature branch with custom output
  python pipeline_test_stats.py --branch feature-xyz --limit 10 --output my_chart.html

  # Filter pipelines by variable value (e.g., only pipelines where ISAAC_SIM_VERSION=2024.1.0)
  python pipeline_test_stats.py --filter ISAAC_SIM_VERSION,2024.1.0

  # Filter by multiple variables
  python pipeline_test_stats.py --filter BUILD_TYPE,release --filter PLATFORM,linux

  # Filter by pipeline source (e.g., only show pipelines triggered by push or web)
  python pipeline_test_stats.py --source push,web

  # Combine filters
  python pipeline_test_stats.py --source schedule --filter BUILD_TYPE,nightly
""",
    )
    parser.add_argument(
        "--branch", "-b", type=str, default="develop", help="Branch name to filter pipelines (default: develop)"
    )
    parser.add_argument(
        "--limit", "-n", type=int, default=20, help="Maximum number of pipelines to fetch (default: 20)"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="pipeline_test_chart.html",
        help="Output file for the chart (default: pipeline_test_chart.html)",
    )
    parser.add_argument("--by-job", "-j", action="store_true", help="Also create a chart grouped by job/test suite")
    parser.add_argument(
        "--heatmap", "-m", action="store_true", help="Also create a heatmap of individual test results per job"
    )
    parser.add_argument(
        "--exclude",
        "-e",
        action="append",
        dest="exclude_patterns",
        metavar="PATTERN",
        default=[],
        help="Exclude jobs containing PATTERN from heatmap (can be used multiple times)",
    )
    parser.add_argument(
        "--filter",
        "-f",
        action="append",
        dest="variable_filters",
        metavar="NAME,VALUE",
        default=[],
        help="Filter pipelines by variable (format: NAME,VALUE). Can be used multiple times for multiple filters.",
    )
    parser.add_argument(
        "--source",
        "-s",
        type=str,
        metavar="SOURCE1,SOURCE2,...",
        help='Filter pipelines by source (comma-separated list, e.g., "push,web,schedule"). Common sources: push, web, schedule, api, trigger, pipeline, chat, merge_request_event, external_pull_request_event, parent_pipeline',
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress all non-error output, progress bars, and browser opening"
    )
    parser.add_argument(
        "--debug-output", "-d", action="store_true", help="Print detailed debug information about heatmap generation"
    )
    parser.add_argument(
        "--heatmap-title",
        type=str,
        default=None,
        metavar="TEXT",
        help="Second line title (subtitle) for the heatmap chart (only used with --heatmap)",
    )

    args = parser.parse_args()

    # Parse variable filters from NAME,VALUE format into dict
    variable_filters_dict = None
    if args.variable_filters:
        variable_filters_dict = {}
        for filter_str in args.variable_filters:
            if "," not in filter_str:
                parser.error(f"Invalid filter format: '{filter_str}'. Expected format: NAME,VALUE")
            parts = filter_str.split(",", 1)  # Split on first comma only
            if len(parts) != 2:
                parser.error(f"Invalid filter format: '{filter_str}'. Expected format: NAME,VALUE")
            name, value = parts
            variable_filters_dict[name.strip()] = value.strip()

    # Parse pipeline sources from comma-separated list
    pipeline_sources_list = None
    if args.source:
        pipeline_sources_list = [s.strip() for s in args.source.split(",") if s.strip()]

    run(
        branch=args.branch,
        limit=args.limit,
        output_chart=args.output,
        by_job=args.by_job,
        heatmap=args.heatmap,
        exclude_patterns=args.exclude_patterns,
        quiet=args.quiet,
        debug_output=args.debug_output,
        variable_filters=variable_filters_dict,
        pipeline_sources=pipeline_sources_list,
        heatmap_subtitle=args.heatmap_title,
    )
