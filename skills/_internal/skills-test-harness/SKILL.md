---
name: skills-test-harness
description: Validate and test the scripts and snippets shipped by this repo's skills/. Use when a skill script or snippet is added or changed, when the discovery-driven test runner under tools/isaac/skills_tests fails, or when deciding whether a failure means a missing prerequisite, missing test scaffolding, or a real bug in the skill script.
---

# Skills Test Harness

Discovery-driven pytest suite that auto-finds every script and fenced snippet under `skills/` and executes them by kind. It lives at `tools/isaac/skills_tests/`. Mechanics (kinds, run specs, fixtures) are documented in the module docstrings — read those rather than a copy here:

- `tools/isaac/skills_tests/_discovery.py` — script classification (the kinds).
- `tools/isaac/skills_tests/_manifest.py` — per-script run specs (the scaffolding surface).
- `tools/isaac/skills_tests/run_skill_tests.sh` — runner, tiers, env contract (header comment).

Adding a script or snippet needs **no new test code** — discovery picks it up. At most, add one data entry to `_manifest.py` if the script needs arguments, a scene, rendering, or a specific assertion.

## Run

```bash
tools/isaac/skills_tests/run_skill_tests.sh         # all tiers (default)
tools/isaac/skills_tests/run_skill_tests.sh unit    # one tier, for faster local iteration
```

- Tiers: `static` (no runtime), `unit` (pure Python), `remote` (running python_server), `standalone` (built Isaac launcher + shell + OmniGraph).
- CI runs the full suite — its machines build the repo, launch the sim, and have a GPU, so every prerequisite is present. There is no reduced "CI subset". The single-tier selectors exist only for faster local iteration.
- The `remote` tier needs a python_server. It **autostarts one** when none is reachable and a build is present: the `sim_server` fixture launches `isaac-sim.sh --no-window --no-ros-env --enable isaacsim.code_editor.python_server` for the session and tears it down after. An already-running server is reused (and left running). Override target with `ISAACSIM_HOST` / `ISAACSIM_PORT`; disable autostart with `ISAACSIM_AUTOSTART=0`; tune the wait with `ISAACSIM_STARTUP_TIMEOUT` (default 300s). With no build present it still FAILS with remediation.
- The `standalone` tier's SimulationApp scripts need a build (`_build/.../python.sh`); `SKIP_HEAVY=1` opts out of heavy GPU renders for local runs (CI leaves it unset).

## Model (read once)

Each script is classified — `shell`, `batch`, `standalone`, `client`, `remote`, `library_sim`, `pure` — and run by a generic per-kind executor; snippets are syntax-checked. Scripts needing args/scene/render/assertions declare them as data in `_manifest.py`. The gate `test_every_script_is_covered` fails if a script lands in an unhandled kind, or a new `library_sim` script lacks a dedicated test. A missing prerequisite does **not** skip: it FAILS with remediation text, the run continues, and a full pass/fail list is printed. (Exception: the `remote` tier first tries to satisfy its own prerequisite by autostarting a headless server when a build is present; it only fails when no build exists or the server never comes up.)

## Triage: a discovered test failed — which kind of problem is it?

Three outcomes only: provide the **environment**, add **scaffolding** (`_manifest.py` or a bespoke test), or fix the **script**. Reproduce the script in isolation with its *documented* inputs, then match the signature:

| Failure signature | Verdict | Fix |
|---|---|---|
| "not reachable at …:8226" / "No Isaac Sim python launcher" / "missing dependency X" | environment | build the repo (remote tier then autostarts its own server) / `pip install`; or start a server manually / set `ISAACSIM_AUTOSTART=0` to use an external one |
| `no execution spec` (shell) | scaffolding | add a `SHELL` entry, or mark `static_only` / `bespoke` |
| coverage-map: unhandled kind, or `library_sim` with no test | scaffolding | fix `classify`, or add a mocked bespoke test (+ `COVERED_LIBRARY_SIM`) |
| server `status:error` from the script's own guard (e.g. "prim_path is required") | scaffolding | add `args=[...]` (+ `scene` / `render`) to `_manifest.py` |
| `ModuleNotFoundError` for an optional extension (e.g. `isaacsim.test.utils`) | scaffolding | enable it in setup (`render=True` / scene fixture) |
| `NameError` / `ImportError` for a name the script never defines or imports | script bug | add the import / helper to the script |
| wrong-type / wrong-API error (e.g. indexing a `wp.array`, `Quatd(list)`) | script bug | fix the call |
| error whose message names the fix and a normal user would hit it | script bug (robustness) | fix the script |
| wrong values / `AssertionError` in a behavioral test | script bug | fix the logic |

Rule of thumb: if the script *documents* the input the harness didn't supply, it is scaffolding. If it fails under documented, normal usage — a missing import, a wrong API call, or an edge a general-purpose tool should handle — it is a script bug.

`library_sim` scripts (import `omni` / `pxr` at top level, no runnable entry — e.g. the namespacing factory in `isaac-sim-ros2-bridge`) can never be smoke-run, so they are always covered by a mocked bespoke test.

## Scaffolding order

Prefer the cheapest that works: `_manifest.py` data (`REMOTE` / `STANDALONE` / `SHELL` / `PURE_HELP`) → `_discovery.classify` (only if a script is misclassified) → a bespoke test (mock / fixture / logic correctness only). Editing the script before ruling out a missing manifest entry is the common triage mistake.

## New test files

`tools/isaac/**` is in `repo_format` scope. Any new `.py` / `.sh` under the harness needs the full Apache preamble (`repo.toml` `license_preamble` + `license_text`) and must pass `ruff` at line length 120 (the existing files set the baseline). Run `./format_code.sh` before committing.
