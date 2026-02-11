# Kit Packages, Packman, and Isaac Sim Dependencies

## Packman Overview

Packman is NVIDIA's package manager for native dependencies. It uses XML files to
declare dependencies and fetches packages from a CDN (cloudfront).

### Key Concepts

- **`*.packman.xml`** — Declares dependencies with package name, version, and link path.
- **`*.packman.xml.user`** — Overrides the corresponding `.xml` file. When packman
  finds a `.user` file, it processes that **instead of** the original `.xml` file.
  The `.user` file must include ALL dependencies (not just overrides), because it
  fully replaces the original.
- **`<package>`** — Tells packman to fetch a package from the CDN by name and version.
- **`<source path>`** — Tells packman to use a local directory instead of fetching.
- **`<import>`** with `<filter>` — Imports specific dependencies from another packman
  XML file, inheriting the package versions defined there.
- **Packman variables** — `${config}`, `${platform_target}`, `${platform_target_abi}`
  are resolved at runtime based on the build configuration and platform.

### Version String Format for Kit Packages

Kit packages use a structured version format:

```
{semantic_version}+{branch}.{build_number}.{commit_hash}.gl.{platform}.{config}
```

Example: `110.0.0+feature.269045.221d0dfe.gl.manylinux_2_35_x86_64.release`

- `110.0.0` — Semantic version (may differ between package types)
- `feature` — Git branch name
- `269045` — Build number (NOT a GitLab pipeline ID)
- `221d0dfe` — Short Git commit SHA of the Kit repo
- `gl` — Built by GitLab
- `manylinux_2_35_x86_64` — Platform
- `release` — Build configuration

The `omniverse-kit` 7z has a slightly different format with an extra USD version tag:
`110.0.0+feature.269429.bc3400f2.usd_25.11_3.12.gl.manylinux_2_35_x86_64.release`

All packages built from the same Kit commit share the same
`{branch}.{build_number}.{commit_hash}` triple, though the semantic version may vary
between different package types (e.g. `omniverse-kit` might be `110.1.0` while
`kit-kernel` and `generic-model-output` are `110.0.0`).


## How Isaac Sim Depends on Kit

Isaac Sim's Kit dependencies fall into three categories:

### Category 1: Kit SDK (direct packman package)

**File**: `deps/kit-sdk.packman.xml`

```xml
<package name="kit-kernel" version="110.0.0+feature.269045.221d0dfe.gl.${platform_target_abi}.${config}"/>
```

This is the core Kit SDK. It gets extracted to `_build/{platform}/{config}/kit/`.

### Category 2: Auto-matching deps (imported from Kit SDK)

**File**: `deps/kit-sdk-deps.packman.xml`

These deps are imported from the Kit SDK's own packman files via `<import>`:

```xml
<import path="../_build/${platform_target}/${config}/kit/dev/all-deps.packman.xml">
    <filter include="python" />
    <filter include="carb_sdk_plugins" />
    <filter include="usd-${config}" />
    ...
</import>
```

Because they are imported from the Kit SDK directory, they **automatically match**
whatever Kit SDK version is installed. No manual version pinning needed.

Similarly, **RTX plugins** in `source/internal_extensions/deps/rtx-plugins.packman.xml`
are imported from the Kit SDK's `rtx-target-deps.packman.xml.user`, so they also
auto-match the Kit SDK.

### Category 3: Pinned Kit deps (hardcoded in Isaac Sim)

**File**: `deps/isaac-sim.packman.xml`

```xml
<package name="generic-model-output" version="110.0.0+feature.269045.221d0dfe.gl.${platform_target_abi}.${config}"/>
<package name="sensor-checker" version="110.0.0+feature.269045.221d0dfe.gl.${platform_target_abi}.${config}"/>
```

These packages are **hardcoded** in Isaac Sim's packman files with a specific Kit
commit. They do NOT auto-match the Kit SDK. When the Kit SDK changes, these must be
explicitly overridden or updated.


## Kit Build Artifacts

The Kit `kit-build-release-linux-x86_64` job produces artifacts at
`kit/_builtpackages/` containing:

| Package                  | Format | Description                |
|--------------------------|--------|----------------------------|
| `omniverse-kit@*.7z`    | 7z     | Full Kit SDK distribution  |
| `generic-model-output@*.zip` | zip | Generic model output lib  |
| `sensor-checker@*.zip`  | zip    | Sensor checker lib         |
| `omniverse_kit-*.whl`   | whl    | Kit Python wheel           |
| `generic_model_output-*.whl` | whl | GMO Python wheel         |
| `sensor_checker-*.whl`  | whl    | Sensor checker Python wheel|
| `test_runner@*.zip`     | zip    | Test runner                |
| `*+latest.txt`          | txt    | Latest version markers     |

All versioned artifacts from the same build share the same
`{branch}.{build_number}.{commit_hash}` triple.


## CI Override Mechanism (develop-kit-tot)

When Kit triggers an Isaac Sim pipeline on the `develop-kit-tot` branch, the goal
is to test whether the upstream Kit commit breaks Isaac Sim. The build must use
**all** Kit packages from the upstream commit, not the pinned versions.

### Pipeline Flow

1. Kit pipeline builds Kit packages (e.g. `kit-build-release-linux-x86_64`)
2. Kit triggers Isaac Sim via `trigger-pipeline-isaac-sim` job, passing
   `UPSTREAM_PIPELINE_ID=$CI_PIPELINE_ID`
3. Isaac Sim's `build_isaac.py` detects `CI_PIPELINE_SOURCE == "pipeline"` and
   honors the provided `UPSTREAM_PIPELINE_ID`
4. Isaac Sim's `build_isaac_from_kit.py` downloads Kit build artifacts via the
   GitLab API and creates packman `.user` overrides

Note: GitLab does not support passing artifacts across projects in multi-project
pipelines. Isaac Sim downloads Kit artifacts itself using the GitLab API with the
pipeline ID passed via variables.

### What `build_isaac_from_kit.py` Overrides

**Kit SDK** — `deps/kit-sdk.packman.xml.user`:
- Extracts `omniverse-kit@*.7z` to `_kit/`
- Creates `.user` with `<source path>` pointing to the extracted SDK
- Category 2 deps (auto-matching) automatically follow

**Kit dep packages** — `deps/isaac-sim.packman.xml.user`:
- Extracts `generic-model-output@*.zip` and `sensor-checker@*.zip` from the
  same Kit build artifacts to `_kit_deps/`
- Reads the original `isaac-sim.packman.xml` and replaces the `<package>`
  elements for these Kit deps with `<source path>` elements pointing to the
  locally extracted directories
- All non-Kit deps (nv_ros2, lula, octomap, etc.) are preserved as-is

### Adding New Kit Dep Overrides

If a new Kit-versioned package is added to `isaac-sim.packman.xml`, add its
packman package name and local directory name to the `KIT_DEP_PACKAGES` dict
in `tools/ci/upstream_kit_build/build_isaac_from_kit.py`:

```python
KIT_DEP_PACKAGES: dict[str, str] = {
    "generic-model-output": "generic_model_output",
    "sensor-checker": "sensor_checker",
    "new-kit-package": "new_kit_package",  # <-- add here
}
```

The package must also be present in the Kit build artifacts at
`kit/_builtpackages/` for the override to work.
