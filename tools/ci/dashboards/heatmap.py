# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
"""Heatmap generation for CI pipeline test results.

Extracted from ci_dashboard.py — produces an interactive HTML (+ optional PNG)
heatmap showing per-test pass/fail status across recent pipelines.
"""
from __future__ import annotations

import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

try:
    import gitlab as _gitlab
except ImportError:
    _gitlab = None  # type: ignore[assignment]

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None  # type: ignore[assignment]


from .parsing import strip_inline_job_name as _strip_inline_job_name


def _heatmap_gitlab_base_url(web_url: str) -> str:
    """Strip '/-/pipelines/<id>' suffix to get the project base URL."""
    return re.sub(r"/-/pipelines/\d+$", "", web_url)


def _heatmap_is_timeout(tc: dict) -> bool:
    """Return True if this test case appears to have timed out."""
    patterns = ("timed out", "timeout", "process timed out", "exceeded time limit",
                "deadline exceeded", "took too long", "time limit")
    text = ((tc.get("system_output") or "") + " " + (tc.get("stack_trace") or "")).lower()
    return any(p in text for p in patterns)


def _heatmap_variable_filter_matches(
    pipeline_vars: dict[str, str],
    variable_filters: dict[str, str | list],
) -> bool:
    """Return True if all *variable_filters* are satisfied by *pipeline_vars*."""
    for key, fval in variable_filters.items():
        pval = pipeline_vars.get(key)
        if isinstance(fval, list):
            if pval not in fval:
                return False
        elif pval != fval:
            return False
    return True


def _heatmap_fetch_pipeline_data(gl: object, project_id: str, pipeline: object) -> tuple:
    """Fetch test report summary for one pipeline (thread-safe).

    Returns *(pipeline_id, test_stats_dict | None, has_bump_version)*.
    """
    try:
        project = gl.projects.get(project_id)  # type: ignore[attr-defined]
        pipeline_obj = project.pipelines.get(pipeline.id)  # type: ignore[attr-defined]

        jobs = pipeline_obj.jobs.list(per_page=100, get_all=True)
        if any("bump-version" in j.name.lower() for j in jobs):
            return pipeline.id, None, True  # type: ignore[attr-defined]

        summary = pipeline_obj.test_report_summary.get()

        if hasattr(summary, "_attrs") and "total" in summary._attrs:
            td = summary._attrs["total"]
        elif hasattr(summary, "total"):
            td = summary.total if not hasattr(summary.total, "get") else summary.total
        else:
            td = summary.get("total", {}) if isinstance(summary, dict) else {}

        if isinstance(td, dict):
            test_stats: dict = {
                "total": td.get("count", 0), "success": td.get("success", 0),
                "failed": td.get("failed", 0), "error": td.get("error", 0),
                "skipped": td.get("skipped", 0),
            }
        else:
            test_stats = {
                "total": getattr(td, "count", 0), "success": getattr(td, "success", 0),
                "failed": getattr(td, "failed", 0), "error": getattr(td, "error", 0),
                "skipped": getattr(td, "skipped", 0),
            }

        if hasattr(summary, "test_suites"):
            suite_list = summary.test_suites
        elif hasattr(summary, "_attrs") and "test_suites" in summary._attrs:
            suite_list = summary._attrs["test_suites"]
        elif isinstance(summary, dict) and "test_suites" in summary:
            suite_list = summary["test_suites"]
        else:
            suite_list = []

        suites = []
        for s in suite_list:
            if hasattr(s, "name"):
                sd: dict = {"name": s.name, "success": getattr(s, "success", 0),
                            "failed": getattr(s, "failed", 0), "error": getattr(s, "error", 0),
                            "skipped": getattr(s, "skipped", 0), "test_cases": []}
            else:
                sd = {"name": s.get("name", "Unknown"), "success": s.get("success", 0),
                      "failed": s.get("failed", 0), "error": s.get("error", 0),
                      "skipped": s.get("skipped", 0), "test_cases": []}
            suites.append(sd)

        test_stats["suites"] = suites
        return pipeline.id, test_stats, False  # type: ignore[attr-defined]
    except Exception:
        return pipeline.id, None, False  # type: ignore[attr-defined]


def _heatmap_fetch_full_test_report(gl: object, project_id: str, pipeline_id: int) -> list | None:
    """Fetch full test report (with individual test cases) for one pipeline."""
    try:
        project = gl.projects.get(project_id)  # type: ignore[attr-defined]
        pipeline_obj = project.pipelines.get(pipeline_id)
        report = pipeline_obj.test_report.get()

        if hasattr(report, "test_suites"):
            suite_list = report.test_suites
        elif hasattr(report, "_attrs") and "test_suites" in report._attrs:
            suite_list = report._attrs["test_suites"]
        elif isinstance(report, dict) and "test_suites" in report:
            suite_list = report["test_suites"]
        else:
            suite_list = []

        suites: list[dict] = []
        for s in suite_list:
            if hasattr(s, "name"):
                sd: dict = {"name": s.name, "success": getattr(s, "success_count", 0),
                            "failed": getattr(s, "failed_count", 0),
                            "error": getattr(s, "error_count", 0),
                            "skipped": getattr(s, "skipped_count", 0)}
                raw_cases = getattr(s, "test_cases", [])
            else:
                sd = {"name": s.get("name", "Unknown"), "success": s.get("success_count", 0),
                      "failed": s.get("failed_count", 0), "error": s.get("error_count", 0),
                      "skipped": s.get("skipped_count", 0)}
                raw_cases = s.get("test_cases", [])

            cases: list[dict] = []
            for tc in raw_cases:
                if hasattr(tc, "name"):
                    cases.append({"name": tc.name, "status": getattr(tc, "status", "unknown"),
                                  "classname": getattr(tc, "classname", ""),
                                  "system_output": getattr(tc, "system_output", "") or "",
                                  "stack_trace": getattr(tc, "stack_trace", "") or ""})
                else:
                    cases.append({"name": tc.get("name", "Unknown"),
                                  "status": tc.get("status", "unknown"),
                                  "classname": tc.get("classname", ""),
                                  "system_output": tc.get("system_output", "") or "",
                                  "stack_trace": tc.get("stack_trace", "") or ""})
            sd["test_cases"] = cases
            suites.append(sd)
        return suites
    except Exception:
        return None


def _heatmap_get_finished_pipelines(
    gl: object,
    project_id: str,
    branch: str = "develop",
    limit: int = 100,
    quiet: bool = False,
    variable_filters: dict | None = None,
    pipeline_sources: list[str] | None = None,
) -> list[dict]:
    """Get finished pipelines with test-report summaries (parallel fetch via python-gitlab)."""
    project = gl.projects.get(project_id)  # type: ignore[attr-defined]
    gitlab_url = os.getenv("GITLAB_URL", "https://gitlab-master.nvidia.com")
    token = os.getenv("ISAAC_MAINTAINER_RO_TOKEN") or os.getenv("CI_GITLAB_API_TOKEN") or ""

    if not quiet:
        print(f"\nFetching pipelines for branch '{branch}'...")

    pipelines_iter = project.pipelines.list(
        ref=branch, per_page=100, order_by="id", sort="desc", iterator=True)
    pipelines_data: list[dict] = []
    bump_count = 0

    pbar = None
    if not quiet:
        try:
            from tqdm import tqdm
            pbar = tqdm(total=limit, desc="Fetching pipeline data", unit="pipeline")
        except ImportError:
            pass

    try:
        while len(pipelines_data) < limit:
            batch: list = []
            for p in pipelines_iter:
                if p.status in ("success", "failed"):
                    batch.append(p)
                if len(batch) >= 50:
                    break
            if not batch:
                break

            batch_results: dict[int, dict | None] = {}
            batch_bumps: set[int] = set()

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {
                    executor.submit(
                        _heatmap_fetch_pipeline_data,
                        _gitlab.Gitlab(url=gitlab_url, private_token=token),  # type: ignore[union-attr]
                        project_id, p,
                    ): p
                    for p in batch
                }
                for future in as_completed(futures):
                    try:
                        pid, stats, is_bump = future.result()
                        if is_bump:
                            batch_bumps.add(pid)
                        else:
                            batch_results[pid] = stats
                    except Exception:
                        pass

            for p in batch:
                if len(pipelines_data) >= limit:
                    break
                if p.id in batch_bumps:
                    bump_count += 1
                    continue
                if p.id in batch_results and batch_results[p.id] is not None:
                    if pipeline_sources and p.source not in pipeline_sources:
                        continue
                    if variable_filters:
                        full_p = project.pipelines.get(p.id)
                        pvars = {v.key: v.value for v in full_p.variables.list(get_all=True)}
                        if not _heatmap_variable_filter_matches(pvars, variable_filters):
                            continue
                    pipelines_data.append({
                        "id": p.id, "status": p.status, "ref": p.ref,
                        "created_at": p.created_at, "web_url": p.web_url,
                        "test_stats": batch_results[p.id],
                    })
                    if pbar:
                        pbar.update(1)
    finally:
        if pbar:
            pbar.close()

    if bump_count and not quiet:
        print(f"Skipped {bump_count} pipelines with bump-version jobs")
    return pipelines_data


def _heatmap_create_chart(
    gl: object,
    project_id: str,
    pipelines: list[dict],
    output_file: str = "pipeline_test_chart_heatmap.html",
    exclude_patterns: list[str] | None = None,
    include_patterns: list[str] | None = None,
    quiet: bool = False,
    subtitle: str | None = None,
) -> None:
    """Create an interactive test heatmap (HTML + PNG). Adapted from pipeline_test_stats.py."""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        print("ERROR: plotly not installed. Install with: pip install plotly", file=sys.stderr)
        return

    _kaleido = None
    try:
        import kaleido
        kaleido.get_chrome_sync()
        _kaleido = kaleido
    except ImportError:
        if not quiet:
            print("Warning: kaleido not installed; PNG generation will be skipped.", file=sys.stderr)

    if exclude_patterns is None:
        exclude_patterns = []

    def should_exclude(name: str) -> bool:
        if include_patterns and not any(p in name for p in include_patterns):
            return True
        return any(p in name for p in exclude_patterns)

    pipelines_with_stats = [p for p in pipelines
                            if p.get("test_stats") and p["test_stats"].get("suites")]
    pipelines_with_stats = list(reversed(pipelines_with_stats))

    if not pipelines_with_stats:
        if not quiet:
            print("\nNo pipelines with test data to chart.")
        return

    # Fetch full test cases if needed
    needs_full = any(
        not suite.get("test_cases")
        for p in pipelines_with_stats
        for suite in p["test_stats"].get("suites", [])
    )
    if needs_full:
        if not quiet:
            print("\nFetching full test case data for heatmap...")
        pbar2 = None
        if not quiet:
            try:
                from tqdm import tqdm
                pbar2 = tqdm(total=len(pipelines_with_stats), desc="Fetching test cases", unit="pipeline")
            except ImportError:
                pass

        gitlab_url = os.getenv("GITLAB_URL", "https://gitlab-master.nvidia.com")
        token = os.getenv("ISAAC_MAINTAINER_RO_TOKEN") or os.getenv("CI_GITLAB_API_TOKEN") or ""

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures2 = {
                executor.submit(
                    _heatmap_fetch_full_test_report,
                    _gitlab.Gitlab(url=gitlab_url, private_token=token),  # type: ignore[union-attr]
                    project_id, p["id"],
                ): p
                for p in pipelines_with_stats
            }
            try:
                for future in as_completed(futures2):
                    p = futures2[future]
                    try:
                        suites = future.result()
                        if suites:
                            p["test_stats"]["suites"] = suites
                    except Exception:
                        pass
                    if pbar2:
                        pbar2.update(1)
            finally:
                if pbar2:
                    pbar2.close()

    pipelines_with_stats = [
        p for p in pipelines_with_stats
        if any(s.get("test_cases") for s in p["test_stats"].get("suites", []))
    ]
    if not pipelines_with_stats:
        if not quiet:
            print("\nNo pipelines with test case data to display.")
        return

    # Build job->failing-tests map
    job_tests: dict[str, set[str]] = {}
    for p in pipelines_with_stats:
        for suite in p["test_stats"].get("suites", []):
            jname = _strip_inline_job_name(suite["name"])
            if should_exclude(jname):
                continue
            job_tests.setdefault(jname, set())
            for tc in suite.get("test_cases", []):
                if tc["status"] in ("failed", "error"):
                    job_tests[jname].add(tc["name"])

    job_tests_sorted = {k: sorted(v) for k, v in job_tests.items() if v}
    if not job_tests_sorted:
        if not quiet:
            print("\nNo failing tests found across pipelines.")
        return

    # x-axis labels
    pipeline_labels_html, pipeline_labels_png = [], []
    for p in pipelines_with_stats:
        try:
            dt = datetime.fromisoformat(p.get("created_at", "").replace("Z", "+00:00"))
            ds = dt.strftime("%m/%d %H:%M")
            pipeline_labels_html.append(f"#{p['id']}<br>{ds}")
            pipeline_labels_png.append(ds)
        except Exception:
            pipeline_labels_html.append(f"#{p['id']}")
            pipeline_labels_png.append(f"#{p['id']}")

    all_jobs = sorted(job_tests_sorted)
    display_jobs = [j[6:] if j.startswith("tests-") else j for j in all_jobs] \
        if all(j.startswith("tests-") for j in all_jobs) else all_jobs

    test_counts = [len(job_tests_sorted[j]) for j in all_jobs]
    total_tests = sum(test_counts) or 1
    row_heights = [c / total_tests for c in test_counts]
    num_rows = len(all_jobs)
    pixels_per_test, title_pixels = 30, 40
    total_px = pixels_per_test * total_tests + title_pixels * num_rows
    vspacing = min(title_pixels / total_px, 0.9 / max(num_rows - 1, 1)) if num_rows > 1 else 0.1

    fig = make_subplots(
        rows=num_rows, cols=1, shared_xaxes=True,
        vertical_spacing=vspacing, subplot_titles=display_jobs, row_heights=row_heights,
    )

    Z_FAILED, Z_ERROR, Z_TIMEOUT, Z_NOT_RUN, Z_SKIPPED, Z_PASS = 0, 1, 2, 3, 4, 5
    b = 1 / 6
    colorscale = [
        [0.0, "#e74c3c"],      [b - 0.001, "#e74c3c"],
        [b, "#9b59b6"],        [2*b - 0.001, "#9b59b6"],
        [2*b, "#00bcd4"],      [3*b - 0.001, "#00bcd4"],
        [3*b, "#3d3d3d"],      [4*b - 0.001, "#3d3d3d"],
        [4*b, "#7f8c8d"],      [5*b - 0.001, "#7f8c8d"],
        [5*b, "#2ecc71"],      [1.0, "#2ecc71"],
    ]

    for job_idx, job_name in enumerate(all_jobs):
        test_names = job_tests_sorted[job_name]
        z_data = []
        for tname in test_names:
            row_data = []
            for p in pipelines_with_stats:
                tc_found = None
                for suite in p["test_stats"].get("suites", []):
                    if _strip_inline_job_name(suite["name"]) == job_name:
                        for tc in suite.get("test_cases", []):
                            if tc["name"] == tname:
                                tc_found = tc
                                break
                    if tc_found is not None:
                        break
                if tc_found is None:
                    row_data.append(Z_NOT_RUN)
                elif tc_found["status"] == "success":
                    row_data.append(Z_PASS)
                elif tc_found["status"] == "failed":
                    row_data.append(Z_FAILED)
                elif tc_found["status"] == "error":
                    row_data.append(Z_TIMEOUT if _heatmap_is_timeout(tc_found) else Z_ERROR)
                elif tc_found["status"] == "skipped":
                    row_data.append(Z_SKIPPED)
                else:
                    row_data.append(Z_NOT_RUN)
            z_data.append(row_data)

        y_labels = ["..." + n[-57:] if len(n) > 60 else n for n in test_names]
        fig.add_trace(
            go.Heatmap(
                z=z_data, x=list(range(len(pipelines_with_stats))),
                y=list(range(len(test_names))), colorscale=colorscale,
                zmin=-0.5, zmax=5.5, showscale=False, hoverinfo="none", xgap=2, ygap=2,
            ),
            row=job_idx + 1, col=1,
        )
        fig.update_yaxes(
            title_text="Test Cases", title_font=dict(size=10), tickfont=dict(size=9),
            tickmode="array", tickvals=list(range(len(test_names))), ticktext=y_labels,
            row=job_idx + 1, col=1,
        )

    legend_line = (
        '<sup style="font-size:12px">'
        "🟢 Pass | ⬜ Skipped | ⬛ Not Run | 🔵 Timeout | 🟣 Error | 🔴 Failed"
        "</sup>"
    )
    title_text = "Test Results Heatmap by Job"
    if subtitle:
        title_text += f'<br><span style="font-size:14px">{subtitle}</span>'
    title_text += f"<br>{legend_line}"

    fig.update_layout(
        title={"text": title_text, "x": 0.5, "xanchor": "center", "font": {"size": 24}},
        template="plotly_dark",
        height=max(400, 150 + pixels_per_test * total_tests + title_pixels * num_rows),
        width=1400,
        margin=dict(l=300, r=20, t=160 if subtitle else 100, b=80),
    )
    fig.update_xaxes(
        tickmode="array", tickvals=list(range(len(pipelines_with_stats))),
        ticktext=pipeline_labels_html, tickangle=45, row=num_rows, col=1,
    )

    # Inject click + hover JS into the standalone HTML
    base_url = _heatmap_gitlab_base_url(pipelines_with_stats[0]["web_url"])
    pipeline_ids = [p["id"] for p in pipelines_with_stats]
    trace_test_names = [job_tests_sorted[j] for j in all_jobs]
    status_labels = ["FAILED", "ERROR", "TIMEOUT", "NOT RUN", "SKIPPED", "PASS"]

    fig.write_html(output_file, include_plotlyjs=True, full_html=True, div_id="plotly-chart")
    with open(output_file) as f:
        html = f.read()

    click_js = f"""
<script>
var base_url = {json.dumps(base_url)};
var pipeline_ids = {json.dumps(pipeline_ids)};
var job_names = {json.dumps(all_jobs)};
var trace_test_names = {json.dumps(trace_test_names)};
var status_labels = {json.dumps(status_labels)};
var plot = document.getElementById('plotly-chart');
var hoverTip = null;
function esc(s) {{ var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }}
function showHoverTip(msg, x, y) {{
  if (!hoverTip) {{
    hoverTip = document.createElement('div');
    hoverTip.style.cssText = 'position:fixed;z-index:9999;padding:8px 12px;background:rgba(42,42,42,0.95);color:#f0f0f0;border:1px solid #fff;border-radius:4px;font-size:13px;pointer-events:none;width:max-content;';
    document.body.appendChild(hoverTip);
  }}
  hoverTip.innerHTML = msg;
  hoverTip.style.left = (x + 12) + 'px';
  hoverTip.style.top = (y + 12) + 'px';
  hoverTip.style.display = 'block';
}}
function hideHoverTip() {{ if (hoverTip) hoverTip.style.display = 'none'; }}
plot.on('plotly_hover', function(data) {{
  if (!data.points || !data.points.length) return;
  var pt = data.points[0], evt = data.event;
  var names = trace_test_names[pt.curveNumber];
  var pid = pipeline_ids[pt.x];
  var status = status_labels[Math.round(pt.z)] || String(pt.z);
  var name = (names && names[pt.y] !== undefined) ? names[pt.y] : ('Row ' + pt.y);
  var msg = '<span style="white-space:nowrap">' + esc(name) + '</span><br>Status: ' + esc(status) + '<br>Pipeline: #' + esc(String(pid));
  showHoverTip(msg, evt ? evt.clientX : 20, evt ? evt.clientY : 80);
}});
plot.on('plotly_unhover', function() {{ hideHoverTip(); }});
plot.on('plotly_click', function(data) {{
  var cn = data.points[0].curveNumber, x = data.points[0].x;
  var job = job_names[cn];
  if (job !== undefined && pipeline_ids[x] !== undefined) {{
    window.open(base_url + '/-/pipelines/' + pipeline_ids[x] + '/test_report?job_name=' + encodeURIComponent(job), '_blank');
  }}
}});
</script>
</body>"""
    with open(output_file, "w") as f:
        f.write(html.replace("</body>", click_js))

    if not quiet:
        print(f"\nTest heatmap saved to: {output_file}")

    if _kaleido is not None:
        fig.update_xaxes(ticktext=pipeline_labels_png, row=num_rows, col=1)
        png_file = output_file.replace(".html", ".png")
        # Chrome/kaleido reliably renders up to ~8k pixels tall; a full-resolution
        # heatmap with hundreds of failing tests (e.g. IsaacLab) can blow past
        # that and fail silently with an empty error.  Cap the PNG height —
        # the interactive HTML still shows every row at full resolution.
        PNG_MAX_HEIGHT = 8000
        original_height = fig.layout.height
        if original_height and original_height > PNG_MAX_HEIGHT:
            fig.update_layout(height=PNG_MAX_HEIGHT)
        try:
            fig.write_image(png_file, scale=1)
            if not quiet:
                print(f"Chart saved to: {png_file}")
        except Exception as exc:
            import traceback
            print(f"Warning: PNG export failed: {type(exc).__name__}: {exc!r}",
                  file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
        finally:
            if original_height and original_height > PNG_MAX_HEIGHT:
                fig.update_layout(height=original_height)


def run_heatmap_mode(args, config: dict) -> None:
    """Generate the heatmap HTML (and PNG) for the dashboard output directory.

    Reads job include/exclude patterns and ``limit`` from
    ``config.slack.heatmap`` and writes
    ``pipeline_test_chart_{namespace_prefix}_heatmap.html/.png`` to
    ``args.output_dir``.
    """
    from pathlib import Path
    from .regression import PipelineType, detect_pipeline_type

    hcfg = config.get("slack", {}).get("heatmap", {})
    excl = list(hcfg.get("exclude_job_patterns") or [])
    incl = list(hcfg.get("include_job_patterns") or [])

    prefix = config.get("namespace_prefix", "heatmap")
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    # run_pipeline_test_stats appends "_heatmap.html" to the chart stem, so pass
    # the base name (without the "_heatmap" suffix) here.
    output_chart = str(out_dir / f"pipeline_test_chart_{prefix}.html")

    branch = (args.branch
              or os.getenv("CI_MERGE_REQUEST_TARGET_BRANCH_NAME")
              or os.getenv("CI_COMMIT_REF_NAME")
              or "develop")

    # Kit-downstream pipelines run as source=pipeline; filtering by source=push
    # would drop them entirely, so match on UPSTREAM_PIPELINE_SOURCE instead.
    pipeline_type = detect_pipeline_type(os.getenv("CI_PIPELINE_SOURCE", ""))
    if pipeline_type in (PipelineType.KIT_NIGHTLY, PipelineType.KIT_POST_MERGE):
        variable_filters: dict | None = {"UPSTREAM_PIPELINE_SOURCE": ["nightly", "post_merge"]}
        pipeline_sources: list[str] | None = None
    else:
        variable_filters = None
        pipeline_sources = ["push"]

    pid = args.include_pipeline_id or os.getenv("CI_PIPELINE_ID")
    include_pipeline_id: int | None = None
    if pid:
        try:
            include_pipeline_id = int(pid)
        except (TypeError, ValueError):
            include_pipeline_id = None

    subtitle = f"Pipeline for branch {branch} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    run_pipeline_test_stats(
        heatmap=True,
        quiet=False,
        output_chart=output_chart,
        exclude_patterns=excl or None,
        include_patterns=incl or None,
        limit=hcfg.get("limit", 100),
        branch=branch,
        pipeline_sources=pipeline_sources,
        variable_filters=variable_filters,
        heatmap_subtitle=subtitle,
        include_pipeline_id=include_pipeline_id,
    )


def run_pipeline_test_stats(
    branch: str = "develop",
    limit: int = 100,
    heatmap: bool = True,
    output_chart: str = "pipeline_test_chart.html",
    exclude_patterns: list[str] | None = None,
    include_patterns: list[str] | None = None,
    quiet: bool = True,
    variable_filters: dict | None = None,
    pipeline_sources: list[str] | None = None,
    heatmap_subtitle: str | None = None,
    include_pipeline_id: int | None = None,
) -> None:
    """Fetch pipeline data and generate a test heatmap. Called by the slack subcommand."""
    if _gitlab is None:
        print("ERROR: python-gitlab not installed. Install with: pip install python-gitlab", file=sys.stderr)
        return

    token = os.getenv("ISAAC_MAINTAINER_RO_TOKEN") or os.getenv("CI_GITLAB_API_TOKEN") or ""
    gitlab_url = os.getenv("GITLAB_URL", "https://gitlab-master.nvidia.com")
    project_id = os.getenv("CI_PROJECT_ID", "")

    if not token or not project_id:
        print("ERROR: CI_GITLAB_API_TOKEN and CI_PROJECT_ID must be set.", file=sys.stderr)
        return

    gl = _gitlab.Gitlab(url=gitlab_url, private_token=token)
    try:
        gl.auth()
    except Exception as exc:
        print(f"ERROR: GitLab auth failed: {exc}", file=sys.stderr)
        return

    pipelines = _heatmap_get_finished_pipelines(
        gl, project_id, branch, limit,
        quiet=quiet, variable_filters=variable_filters, pipeline_sources=pipeline_sources,
    )

    if include_pipeline_id is not None:
        try:
            project = gl.projects.get(project_id)
            pipeline_obj = project.pipelines.get(include_pipeline_id)
            _, test_stats, _ = _heatmap_fetch_pipeline_data(gl, project_id, pipeline_obj)
            included: dict = {
                "id": pipeline_obj.id, "status": pipeline_obj.status, "ref": pipeline_obj.ref,
                "created_at": pipeline_obj.created_at, "web_url": pipeline_obj.web_url,
                "test_stats": test_stats,
            }
            pipelines = [p for p in pipelines if p["id"] != include_pipeline_id]
            pipelines.insert(0, included)
        except Exception as exc:
            if not quiet:
                print(f"Warning: could not fetch include pipeline {include_pipeline_id}: {exc}")

    if heatmap:
        heatmap_file = output_chart.replace(".html", "_heatmap.html")
        _heatmap_create_chart(
            gl, project_id, pipelines, heatmap_file,
            exclude_patterns=exclude_patterns, include_patterns=include_patterns,
            quiet=quiet, subtitle=heatmap_subtitle,
        )
