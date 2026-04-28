---
name: doc-snippets
description: Author and runtime-test Python code samples shown in Isaac Sim user docs. Use when the user asks to add a code example to an RST page, fix an inline `.. code-block:: python` block, or run the doc snippet test runner. Covers the .py + literalinclude convention, async vs SimulationApp snippet styles, the test runner, and common runtime pitfalls.
---

# Authoring and testing doc snippets

## The rule

**Every Python code sample shown in a user-facing RST doc must live as a real `.py` file under `docs/isaacsim/snippets/<category>/<rst_stem>/<name>.py` and be embedded with `.. literalinclude::`.** Inline `.. code-block:: python` is **not** an acceptable pattern in this repo and should be fixed when found, regardless of who introduced it.

Why:

- Inline blocks aren't picked up by the snippet test runner, so they silently rot when an API changes.
- Real `.py` files can be linted, formatted, and runtime-verified.
- Existing snippets follow this convention (`docs/isaacsim/snippets/`); inconsistency makes the docs harder to maintain.

## Layout

For an RST file at `docs/isaacsim/<category>/<rst_stem>.rst`, snippets go in `docs/isaacsim/snippets/<category>/<rst_stem>/`. Match the existing tree:

```
docs/isaacsim/sensors/isaacsim_sensors_rtx_lidar.rst
  ↳ docs/isaacsim/snippets/sensors/isaacsim_sensors_rtx_lidar/
      create_an_rtx_lidar_through_the_lidar_class.py
      set_lidar_tick_rate.py
      set_lidar_aux_output_level.py
      ...

docs/isaacsim/ros2_tutorials/tutorial_ros2_rtx_radar.rst
  ↳ docs/isaacsim/snippets/ros2_tutorials/tutorial_ros2_rtx_radar/
      programmatic_setup.py
```

Naming: lowercase, snake_case, descriptive verb-based file names (`set_lidar_tick_rate.py`, `disable_lidar_scan_accumulation.py`, `attach_debug_draw_writer.py`). Don't repeat the directory in the filename.

In the RST, replace the inline block:

```rst
.. literalinclude:: ../snippets/<category>/<rst_stem>/<name>.py
    :language: python
```

The `..` is relative to the RST file, so e.g. `docs/isaacsim/sensors/foo.rst` references `../snippets/sensors/foo/<name>.py`.

## Two snippet flavors

### Async (Script Editor) — most snippets

These assume an active Kit session and stage. They do **not** import `SimulationApp` and are not standalone scripts. Used when illustrating an API call from inside the running app. Most existing snippets are this flavor.

The test runner discovers async snippets automatically once `./format_code.sh` runs.

### SimulationApp (standalone) — full end-to-end

These wrap the snippet with `SimulationApp(...)` and can be run via `./python.sh <snippet>.py`. Used for "complete tutorial" examples. Existing example:

```
docs/isaacsim/snippets/sensors/isaacsim_sensors_rtx_annotators/collect_data_with_lidar_sensor.py
```

SimulationApp snippets are **not** auto-discovered. They must be registered in `tests/doc_snippets/premake5-tests.lua` to get a generated test target.

## Authoring workflow

1. Write the snippet `.py` file in the right snippet directory. Make it **self-contained** — see Pitfalls below.
2. Update the RST to use `.. literalinclude::` instead of `.. code-block:: python`.
3. **Run the formatter**: `./format_code.sh`. This formats the new `.py` file *and* registers async snippets with the test runner.
4. **Non-clean rebuild**: `./build.sh --no-docker -j12` (sandbox) or `./build.sh -j12` (with linbuild outside sandbox). Incremental — only takes ~25s. This generates / updates the per-test stub scripts under `_build/<platform>/<config>/tests/doc_snippets/`.
5. **Run the async test, filtered to the touched RST stem**:
   ```bash
   cd _build/linux-x86_64/release/tests/doc_snippets
   ./tests-nativepython-testing-doc_snippets.test_snippets_async.sh -f <rst_stem>
   ```
   Filter is the RST file's basename without `.rst` (e.g. `isaacsim_sensors_rtx_radar`, `tutorial_ros2_rtx_lidar`).
6. **For SimulationApp snippets**: register the snippet in `tests/doc_snippets/premake5-tests.lua`, rebuild, then run the generated `tests-nativepython-testing-doc_snippets.<category>.<rst_stem>.<name>.sh` from the build directory.
7. **Docs build** (`./tools/build_docs.sh`) verifies the `literalinclude` paths resolve.

## Self-containment requirements

Each snippet runs in a fresh, empty stage. A snippet that worked as part of an inline block series often won't work standalone because variables don't carry across blocks anymore. Concrete patterns:

### Don't reference variables from prior blocks

If the inline RST had two blocks where block 2 referenced `lidar` from block 1, extract them as **two snippets that each create their own `lidar`**.

### Use root-level prim paths

The empty test stage has no `/World` prim. `Lidar.create("/World/Lidar", ...)` raises `ValueError: Parent /World is not a valid prim`. Either:

- Use a root-level path: `Lidar.create("/Lidar", ...)`, `Radar(path="/Radar", ...)`, etc.
- Or explicitly `UsdGeom.Xform.Define(stage, "/World")` first.

The root-level pattern is preferred for terseness; users in real apps already have `/World`.

### Enable Motion BVH for any radar snippet

`Radar(...)` raises `RuntimeError: RTX Radar requires Motion BVH to be enabled.` if the carb settings aren't set. Every radar snippet needs this preamble:

```python
import carb
settings = carb.settings.get_settings()
settings.set("/renderer/raytracingMotion/enabled", True)
settings.set("/renderer/raytracingMotion/enableHydraEngineMasking", True)
settings.set("/renderer/raytracingMotion/enabledForHydraEngines", "0,1,2,3,4")
```

### Enable extensions that register OG nodes / writers / annotators

The test framework starts a minimal Kit. Snippets that use OG node types or Replicator writers from extensions outside the minimal set will fail with `OmniGraphError: Could not create node using unrecognized type ...` or `ValueError: Unsupported writer ...`.

Enable the providing extension(s) at the top of the snippet:

```python
import omni.kit.app
ext_mgr = omni.kit.app.get_app().get_extension_manager()
ext_mgr.set_extension_enabled_immediate("isaacsim.core.nodes", True)
ext_mgr.set_extension_enabled_immediate("isaacsim.ros2.nodes", True)
```

Examples seen in this repo:

- `draw-point-cloud` writer → enable `isaacsim.sensors.rtx.nodes`
- `isaacsim.ros2.bridge.ROS2RtxRadarHelper` OG node → enable `isaacsim.ros2.nodes`
- `isaacsim.core.nodes.IsaacCreateRenderProduct` and friends → enable `isaacsim.core.nodes`

### Provide example values for "math demo" snippets

A snippet that demonstrates a one-liner (e.g. recombining a uint64 from two uint32s) needs to define example inputs so it actually runs:

```python
# Example values you'd get from a PointCloud2 message.
timestamp_0 = 0xCAFEBABE
timestamp_1 = 0x12345678

ts_uint64_ns = (int(timestamp_1) << 32) | int(timestamp_0)
```

## When the test runner is right and the snippet is wrong

If a snippet that looked fine in the RST fails when extracted, the failure is almost always one of the four pitfalls above. Before debugging deeper, check in this order:

1. Is it referencing an undefined variable? → make it self-contained.
2. Is it using `/World/...`? → switch to root-level path or define `/World`.
3. Is it a radar snippet? → add the Motion BVH preamble.
4. Is it referencing an OG node, writer, or annotator that's not in the minimal Kit? → enable the providing extension explicitly.

## Auditing for inline blocks

To find any remaining `.. code-block:: python` violations across the user docs:

```bash
grep -rln "code-block:: ?python" docs/isaacsim/
```

For each hit, follow the authoring workflow above. Group the cleanup into a single commit (no extension version bump needed for pure docs changes).

## Don't forget

- **Pure-docs changes don't need extension version bumps or CHANGELOG entries.** The version-bump rule applies to changes under `source/`. Pure changes under `docs/` (including new snippet `.py` files) are exempt.
- **Don't run multiple Kit / Isaac Sim processes in parallel.** The async test runner spawns Kit; run one filter at a time, not several in parallel.
- **The test runner kills and restarts the stage between snippet runs.** Don't expect side effects to persist across snippets in the same filter.
