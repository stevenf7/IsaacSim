---
name: debug-with-local-kit
description: Debug Isaac Sim issues using a local Kit build. Use when the user needs to add debug statements to Kit, step through Kit code, build Kit from source, link Isaac Sim against a local Kit build, or investigate issues in Kit's rendering, multitick, or sensor pipeline code.
---

# Debug Isaac Sim with a Local Kit Build

Workflow for building Kit from source and linking Isaac Sim against it to debug issues that originate in Kit internals.

## Step 1 — Determine Kit Version

Read `deps/kit-sdk.packman.xml` to find the Kit version this branch builds against. The `<package>` tag (or commented-out tag if already using a local source) contains a version string like:

```
110.1.0+feature.282856.d2ba2620.gl.manylinux_2_35_x86_64.release
```

Extract the release number and changelist to form a git tag: `110.1.0-282856`.

**Pattern**: `<major>.<minor>.<patch>+feature.<changelist>.<sha>...` → tag `<major>.<minor>.<patch>-<changelist>`

## Step 2 — Locate or Clone Kit Repository

Check for an existing local clone (typical location: `../kit` relative to the Isaac Sim workspace).

**Prompt the user** to confirm:
- The path to their local Kit repo, OR
- Whether to clone a fresh copy

If cloning:

```bash
git clone ssh://git@gitlab-master.nvidia.com:12051/omniverse/kit.git ../kit
```

## Step 3 — Check Out the Matching Tag

For an existing repo, fetch first to ensure the tag is available:

```bash
cd <kit_repo_path>
git fetch --tags
git checkout <tag>    # e.g. 110.1.0-282856
```

If the checkout fails due to local changes, **prompt the user** to resolve them (stash, commit, or discard), then resume.

## Step 4 — Build Kit

The Kit repo has two sub-repos:

1. **`rendering/`** — rendering plugins (e.g. `rtx.sensors.lidar.core`, `rtx.rtsensor`, `carb.scenerenderer-rtx`, `omni.sensorscheduling`)
2. **`kit/`** — Kit kernel and core extensions (e.g. `omni.usd.core`, `omni.sensors.nv.lidar`)

The top-level `./repo.sh build` builds both sub-repos in the correct order.

### Build command

From the Kit repo root:

```bash
cd <kit_repo>
./repo.sh build
```

### Agent execution notes

- The build requires `required_permissions: ["all"]` (network access for packman, writes outside workspace).
- The build is long-running (typically 5–20 minutes). Use `block_until_ms: 0` to background it, then monitor the terminal file.
- After backgrounding, poll the terminal file with exponential backoff (e.g. sleep 30s, 60s, 120s). Look for `exit_code` in the footer or error messages.
- A successful build ends with exit code 0.
- If the build fails, read the last ~100 lines of the terminal file to find the error.

## Step 5 — Link Isaac Sim to the Local Kit Build

In the Isaac Sim workspace, edit `deps/kit-sdk.packman.xml`:

**Before** (using packman package):
```xml
<project toolsVersion="5.6">
  <dependency name="kit_sdk_${config}" linkPath="../_build/${platform_target}/${config}/kit" tags="${config} non-redist">
    <package name="kit-kernel" version="110.1.0+feature.282856.d2ba2620.gl.${platform_target_abi}.${config}" platforms="..." />
  </dependency>
</project>
```

**After** (using local build):
```xml
<project toolsVersion="5.6">
  <dependency name="kit_sdk_${config}" linkPath="../_build/${platform_target}/${config}/kit" tags="${config} non-redist">
    <!-- <package name="kit-kernel" version="110.1.0+feature.282856.d2ba2620.gl.${platform_target_abi}.${config}" platforms="..." /> -->
    <source path="<absolute_path_to_kit_repo>/kit/_build/${platform_target}/${config}"/>
  </dependency>
</project>
```

**Important**: The `<source>` path points to the **`kit/` sub-repo's** build output (`kit/kit/_build/...`), not the top-level or rendering build output. Comment out (don't delete) the original `<package>` tag so it can be restored later.

Then rebuild Isaac Sim:

```bash
cd <isaac_sim_workspace>
./build.sh
```

Isaac Sim build also requires `required_permissions: ["all"]` and should be backgrounded with monitoring.

## Step 6 — Iterate on Debugging

Changes to Kit source are now picked up by Isaac Sim after rebuilding Kit (and Isaac Sim if C++ changed). Typical debugging activities:

- **Add debug logging** to Kit code (e.g. `CARB_LOG_INFO(...)` in C++, `carb.log_info()` in Python). Use `#include <cinttypes>` for `PRIu64` when logging `uint64_t` values.
- **Static analysis** of Kit rendering/multitick/sensor pipeline code
- **Add Tracy profiling zones** to narrow down timing issues
- **Modify Kit behavior** to test hypotheses

### Rebuild cycle (agent-executable)

After each Kit source change, the agent should:

1. **Rebuild Kit**: `cd <kit_repo> && ./repo.sh build` (use `required_permissions: ["all"]`, `block_until_ms: 0`)
   - Monitor the build to completion before proceeding.

2. **Rebuild Isaac Sim** (if Kit C++ interfaces or plugins changed):
   ```bash
   cd <isaac_sim_workspace>
   ./build.sh
   ```
   (use `required_permissions: ["all"]`, `block_until_ms: 0`, monitor to completion)

3. **Rerun the failing test or benchmark** and collect logs for analysis.

### Python-only Kit changes

If the change is Python-only (e.g. editing a `.py` file inside a Kit extension), no rebuild is needed — just rerun the test.

## Restoring the Packman Package

When done debugging, restore `deps/kit-sdk.packman.xml` by uncommenting the `<package>` tag and removing (or commenting out) the `<source>` tag. Then rebuild Isaac Sim.
