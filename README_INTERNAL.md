# Omniverse Isaac Sim
This is where the Omniverse Isaac Sim application is developed.

* [Internal Documentation](https://omniverse.gitlab-master-pages.nvidia.com/isaac/omni_isaac_sim/develop/index.html)
* [Public Documentation](https://docs.isaacsim.omniverse.nvidia.com)
* Slack: [#omni-isaac-support](https://nvidia.slack.com/archives/CBDM22E5P)
* [Confluence](https://confluence.nvidia.com/display/OMNIVERSE/Omniverse+Isaac+Sim)

# Table of contents

[[_TOC_]]

# Getting Started

See [here](https://omniverse.gitlab-master-pages.nvidia.com/isaac/omni_isaac_sim/develop/installation/requirements.html) for general hardware and driver requirements

There are multiple ways to use isaac sim based on your workflow:

## Source (This repository)
See [Using The Source Repository](#using-the-source-repository) section below for how to compile source and set up `git lfs`
#### Branches:
* [Release/x.y](https://gitlab-master.nvidia.com/omniverse/isaac/omni_isaac_sim/-/branches?state=all&sort=updated_desc&search=release%2F): Current Release Candidates and Public Releases (rc.x)
* [Develop](https://gitlab-master.nvidia.com/omniverse/isaac/omni_isaac_sim/-/tree/develop): Latest internal codebase, updated daily (alpha.x, beta.x)
* [Tagged Releases](https://gitlab-master.nvidia.com/omniverse/isaac/omni_isaac_sim/-/tags): Older release commits are tagged here

Current public release: **4.2.0-rc.18**

> See [Isaac Sim Release Flow](https://docs.google.com/presentation/d/161QpSIxvXvAmZO1QeniJ-sMWdUhbX8iWUHpmg2sCHAA/edit?usp=sharing)

## Binary Builds (Packman Manual Download)
* [Stable RC Builds from Release branch](https://omnipackages.nvidia.com/packages/cloudfront/isaac-sim-standalone?query=rc)
* [Daily Alpha Builds from Develop branch](http://packman.ov.nvidia.com/packages/cloudfront/isaac-sim-standalone?query=alpha)
* [Daily Beta Builds from Develop branch](http://packman.ov.nvidia.com/packages/cloudfront/isaac-sim-standalone?query=beta)
* [Internal-only Builds from Develop branch (for internal tests/benchmarking)](https://omnipackages.nvidia.com/packages/cloudfront/isaac-sim-internal-standalone)

> Notes:
>  - Omniverse Launcher support is deprecated.
>  - Download and extract .zip to a folder then run ./isaac-sim.(sh/bat)

## Docker Containers (GitLab)

* Isaac Sim Stable RC: [gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim/isaac-sim:latest-x.y](https://gitlab-master.nvidia.com/omniverse/isaac/omni_isaac_sim/container_registry/53857?orderBy=NAME&sort=desc&search[]=rc) (Release branch, rc)
* Isaac Sim Daily: [gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim/isaac-sim:latest-develop](https://gitlab-master.nvidia.com/omniverse/isaac/omni_isaac_sim/container_registry/53857?orderBy=NAME&sort=desc&search[]=develop) (Develop branch, alpha/beta)

## Docker Containers (NGC)

* [Isaac Sim Public](https://catalog.ngc.nvidia.com/orgs/nvidia/containers/isaac-sim): ``nvcr.io/nvidia/isaac-sim:x.y.z``
* [Isaac Sim Internal](https://registry.ngc.nvidia.com/orgs/nvidian/containers/isaac-sim/tags): For anyone in the ``nvidian`` org in NGC.
  * Latest RC: ``nvcr.io/nvidian/isaac-sim:latest-x.y`` Built from the Release branch.
  * Latest Daily: ``nvcr.io/nvidian/isaac-sim:latest-develop`` Built from the Develop branch.

> Notes:
>  - Isaac Sim containers are now multi-arch. Docker will pull containers based on the host platforms. use the `--platform` flag to pull specific container.
>  - `*-x86_64` and `*-aarch64` tags are for specific arch/platforms.
>  - Access to [``nvidian``](https://docs.google.com/forms/d/e/1FAIpQLScHfy_rMaUwpDVF7vpUuZe68fKESB7CN8twnXQnrZSUZnAfFA/viewform) org in NGC. [#swngc-help](https://nvidia.enterprise.slack.com/archives/C7VGNG1V3)
>  - See [Branches](#branches)

## Python packages

* Python packages (**public**): [pypi.nvidia.com](https://pypi.nvidia.com)
  * See [Install Isaac Sim using PIP](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/install_python.html#installation-using-pip) for installation instructions.
* Python packages (**internal**: beta, release candidates, etc.): [urm.nvidia.com/artifactory/sw-isaacsim-pypi-local](https://urm.nvidia.com/artifactory/sw-isaacsim-pypi-local)
  * See the internal [README](https://urm.nvidia.com/artifactory/sw-isaacsim-pypi-local/README.html) for installation instructions.

## Native Python Sample Repository

For certain python only usecases we have a [separate repository](https://gitlab-master.nvidia.com/Isaac/omni_isaac_sim_python)

This repository will automatically pull a specific binary package from our packman repository and extract it for use in your branch/fork.
It is ideal if you want to write native python scripts and need place to work where the version of Isaac Sim is deterministic. See the repo for more information on usage.

# Developer Resources

See the [wiki section](https://gitlab-master.nvidia.com/omniverse/isaac/omni_isaac_sim/-/wikis/home) of this repo for developer resources and docs.

* [Filing Bugs And Requests](https://gitlab-master.nvidia.com/omniverse/isaac/omni_isaac_sim/-/wikis/Developer-Resources/Jira-Board#creating-a-new-issue)
* [Submitting a merge request](https://gitlab-master.nvidia.com/omniverse/isaac/omni_isaac_sim/-/wikis/Developer-Resources/Merge-Request)

## MR Pipeline Options

The MR description template includes checkboxes under **Pipeline Options** that control which CI jobs run. Check a box by replacing `[ ]` with `[x]` in the description before pushing.

| Checkbox | Effect |
|---|---|
| **User docs only change** | Skips builds, tests, and deploy stages. Only runs `check-code-format` and the lightweight docs build (`build-docs-only-mr`). **Only check this if your changes are exclusively in `/docs/isaacsim/\*`.** |
| **Build docs in MR pipelines** | Runs the full docs build (`build-docs-mr`) including user guide and API reference. Requires the linux release build. A preview link is posted as a job artifact. |
| **Generate containers in MR pipelines** | Builds and pushes Docker containers (x86_64 and aarch64) from the MR. Container tags include an `-mr` suffix. |
| **Post pipeline reports to slack** | Posts pipeline results to [#isaac-sim-ci-mr](https://nvidia.slack.com/archives/isaac-sim-ci-mr) when the pipeline finishes. |

> **Note:** These options are evaluated via regex against the MR description, so the checkbox text must remain unchanged for them to work.

# Running headless and connecting via a remote client

See [here](https://omniverse.gitlab-master-pages.nvidia.com/isaac/omni_isaac_sim/develop/installation/install_container.html) for more information on how to use the container.

# List of internal Nucleus servers:
* isaac-dev.ov.nvidia.com : http://isaac-dev.ov.nvidia.com/
    - For development work (most internal users use this)
    - Note: ov-isaac-dev.nvidia.com will redirect to the server above.

# Using the Omniverse cache service

## Cache Status
To check the status of your nucleus cache go to [localhost:3080/cache](http://localhost:3080/cache).

You can also clear your local cache from here and see used disk space

## Deleting previous installs

* Download and run the [launcher cleanup tool](https://docs.omniverse.nvidia.com/utilities/latest/cleanup-tool.html)
    * Run ``./launcher-cleanup``
    * This tool will delete any installed omniverse applications and will ask if you want to delete your local nucleus data.
    * Run with ``sudo`` if you have trouble installing cache from the launcher.

* If issues remain due to older omniverse installations
    * Run ``sudo apt remove 'omniverse*'`` to remove all previously installed omniverse packages.
    * You might need to manually delete `omniverse-cache-enabler`
        * use ``which omniverse-cache-enabler`` to determine the location. If it doesn't exist then you can go to the next step.
        * remove using ``sudo rm -rf /path/returned/from/above/omniverse-cache-enabler``

## Install Cache

* Download the internal [Integration](http://ov-launcher/exchange/app) Omniverse Launcher App
* Use ``chmod +x`` to make it executable if needed
* Once launched you will see Cache under the ``Exchange`` tab  and can install it from there. If there are failures you will see a red icon in the upper right.

## Starting Cache

After a reboot you will need to:
- Start Omniverse Launcher
- go to [localhost:3080/cache](http://localhost:3080/cache).
- Stop and Start the cache service
- Start Isaac Sim and use like normal

> If the cache icon in the upper right of isaac sim says ``CACHE: ON`` but becomes ``CACHE: OFF`` after startup, stop and start the cache service from the web ui. Isaac sim also need to be restarted




# Using The Source Repository

#### Linux/Windows
- Ubuntu 22.04 (linux-x86_64) / Ubuntu 24.04 (linux-x86_64) / Windows 10 version 1903 (windows-x86_64 and DXR) / Windows 11 Enterprise version 24H2 (windows-x86_64 and DXR)
- Install NVIDIA driver 535.129.03 (Linux)/ NVIDIA driver 537.58 (Windows: GameReady, Studio) / NVIDIA driver 537.70 (Windows: RTX/Quadro, Grid/vGPU)
    * [Linux] (https://docs.nvidia.com/datacenter/tesla/driver-installation-guide/index.html#ubuntu-installation)
    * [NVIDIA OMNIVERSE - Driver Requirements](https://developer.nvidia.com/omniverse/driver)
- Open a terminal on Linux or Command Prompt/PowerShell on Windows, and run nvidia-smi to confirm that NVIDIA drivers are installed correctly.
- Install [VS Code](https://code.visualstudio.com/)
- Install "git".
- Install "git-lfs":
    * Required for fetching data folder used in unit tests only.
    * Reboot your machine after installation.
    * Execute `git lfs install` once to enable LFS features after installation.
        * If you cloned the repo before above steps, you have to fetch the data with `git lfs pull` in the repo.
- [Fork omniverse isaac sim repository](https://gitlab-master.nvidia.com/omniverse/isaac/omni_isaac_sim/-/forks/new)
- Go to your newly created fork in GitLab, select
    * go to "Settings->Repository->Mirroring repositories"
        * set "Git repository URL" to https://gitlab-master.nvidia.com/omniverse/isaac/omni_isaac_sim.git
        * select "Pull" under "Mirror direction".
        * clear out the text under "Password".
        * check the "Overwrite diverged branches" checkbox.
    * go to "Settings->General->Visibility, project features, permissions"
        * ensure "Project Visibility" is set to "Public".
- Clone your fork to a local hard drive, make sure to use a NTFS drive on Windows (Carbonite uses symbolic links).
    * Prefer to clone the fork to the shortest file path possible (such as cloning directly to C:\\) as long file paths can lead to errors when building.
- Execute `./setup.sh` (Linux) which will install Docker. Logging out and back
  in is required to update your account's group membership to include "docker".
- Download Visual Studio Community 2026. Choose "Desktop development with C++". Use the default checklist.
    * Note that the Windows 11 SDK may take a while to fully install.
    * You may need to restart Visual Studio Code (or whatever IDE is in use) for Visual Studio and the SDK to process in terminal.
    * If build errors persist, please download Visual Studio Professional 2026 instead. Choose "Desktop development with C++" and use the default checklist.

## Building Isaac Sim

- Execute `./build.sh` (Linux) / `build.bat` (Windows)
- Use `--help` to get more information. You can run only parts of build process, e.g:
    * `build.bat -s` to only copy/link files
    * `build.bat -d` to build only debug configuration
    * `build.bat -r` to build only release configuration
    * `build.bat -x` to do a clean and rebuild

The build output will be found in the generated
`_build` folder and the make/solution files will be found in the generated `_compiler` directory. Occasionally, when
drastic project level changes are made, you may have to regenerate these files using `-x` option with the build
script.

- When using OpenGL on Linux, especially in workstations or desktops, it often defaults to using the NVIDIA drivers. However, on laptops, it may fall back to using the CPU's integrated graphics (i.e., not using the NVIDIA GPU). To make sure OpenGL is using the NVIDIA driver, follow these steps:

Install `mesa-utils` to get `glxinfo`:
```
sudo apt update
sudo apt install mesa-utils
```
Check if OpenGL is using the NVIDIA driver::
```
glxinfo | grep "OpenGL version"
```
The output should look like this: `OpenGL version string: <opengl_version> NVIDIA <nvidia_driver_version>`.
If the output is empty, try opening a new terminal and run the command again, or reboot your system.
If the output does not show "NVIDIA", then run the following commands:

```
sudo apt update
sudo apt install nvidia-prime
sudo prime-select nvidia
```
After that, check again with: `glxinfo | grep "OpenGL version"`, The output should now include "NVIDIA."


> NOTE: To build the project minimal configuration is needed. Any version of Windows 10 or Linux with Docker will do. Then
run the setup and build scripts as described here above. That's it. The specific version of Windows, NVIDIA driver,
and Vulkan are all runtime dependencies, not compile/link time dependencies. This allows Isaac Sim to build on stock
virtual machines that require zero configuration. This is a beautiful thing, help us keep it that way.

> NOTE: On systems with less memory (32GB or less), there might be issues when running `./build.sh`. If you notice
programs crashing or messages like `internal compiler error: Killed (program cc1plus)`, this could mean your system is
running out of memory. In that case, try to run `./build.sh -j <num_procs>`, where `<num_procs>` is the number of
processes created during `./build.sh`. A good number to use for `<num_procs>` is `10` but this may need to be smaller
if you are still seeing the same issues when building.

## Running Isaac Sim

- Go to debug or release folder under `_build/{platform}/{config}`
- Execute `./isaac-sim.sh` (Linux) / `isaac-sim.bat` (Windows)

## Debugging With Visual Studio Code

To run isaac sim with a debugger attached:
- Go to the `Run and Debug` panel (or press `Ctrl+Shift+D`)
- From the dropdown select `(Linux) isaac-sim [release]` or `(Linux) isaac-sim [debug]` depending on the build configuration you wish to run.
- Press the green play button to start debugging
- Breakpoints can be set directly in cpp files

To attach a debugger to a running application:

- See [Here](https://omniverse.gitlab-master-pages.nvidia.com/isaac/omni_isaac_sim/develop/installation/install_python.html)

To debug a native python (normally run from `python.sh`) application:

- Open the python script you wish to debug.
- Go to the `Run and Debug` panel (or press `Ctrl+Shift+D`)
- Select `Python: Current File`
- Press the green play button to start debugging
- Breakpoints can be set directly in the python file you are debugging

## Packaging

* `./tools/ci/build-and-packaging/launcher-package-linux-x86_64/step.sh` (Linux)
* `tools/ci/build-and-packaging/launcher-package-windows-x86_64/step.bat` (Windows)


## Running Tests

- all tests are in the `_build/{platform}/{config}/tests` folder and start with `tests-*` in the filename. There are several categories of tests, extension, native python scripts, internal tests, startup tests, jupyter notebook tests.

## Building Internal Docs

A full release build is required before building docs, as API documentation is generated from the build output.

**Prerequisites:**
1. Run `./build.sh -r` (Linux) or `build.bat -r` (Windows) to complete a release build.
2. Ensure `_repo/python/python3` and `_build/linux-x86_64/release/kit/python/python3` exist and are the same Python version. If there is a mismatch, remove `_repo/python` and `~/.cache/packman/chk/repo_docs_deps`, then re-run `./build.sh`.

**Linux:**
```bash
./tools/build_docs.sh
```

This runs the full pipeline: Doxygen generation, extension docs, extension TOC, user guide (Sphinx), API reference, and examples list. A build summary with per-step timings is printed at the end.

**Windows:**
```bat
tools\build_docs.bat
```

The Windows script builds extension TOC, extension docs, and the user guide.

**Output:** The built docs are placed in `_build/docs/isaac-sim/latest/`. Open `_build/docs/isaac-sim/latest/index.html` in a browser to preview locally.

> **Tip:** Pass extra arguments to the build scripts to forward them to the underlying `repo.sh docs` command (e.g. `./tools/build_docs.sh --project isaac-sim` to build only the user guide).

## Best Practices for Creating New Assets

See the [Asset Naming Best Practices](https://docs.google.com/document/d/1WmZo35smDxfjZPzuFBCLvsZu8bMQzy1bK_0J-13EUMM/edit?usp=sharing) guide for conventions on naming assets.

## Pre-Merge Validation Tools

The `tools/isaac/pre_merge/` directory contains scripts used to validate code quality before merging. These are the same checks that run in CI, but you can run them locally to catch issues early.

### Quick Start

Run all default validation checks (lint, format, changelog, TOML, structure, license headers) on extensions touched by your branch:

```bash
python tools/isaac/pre_merge/pre_merge_validate.py
```

Auto-fix what can be fixed automatically (ruff, formatting, extension.toml):

```bash
python tools/isaac/pre_merge/pre_merge_validate.py --fix
```

### Orchestrator (`pre_merge_validate.py`)

This is the main entry point that runs one or more validation checks and optionally extension tests. By default it detects the base branch and only validates extensions with modified files.

| Flag | Purpose |
|---|---|
| `--lint` | Run Python linting (ruff) |
| `--format` | Run code format verification |
| `--changelog` | Check changelog format and version bump |
| `--toml` | Validate extension.toml structure and ordering |
| `--structure` | Validate extension directory structure |
| `--license` | Check SPDX license headers |
| `--test` | Run validation checks plus extension tests |
| `--test-only` | Skip validation, run only extension tests |
| `--all` | Check every extension, not just modified ones |
| `--fix` | Auto-fix issues where possible |
| `--base-branch <ref>` | Explicit base branch instead of auto-detection |
| `--log <path>` | Save ANSI-stripped output to a log file |
| `--keep-going` / `-k` | Run all checks even if earlier ones fail |

Examples:

```bash
# Run only lint and format checks
python tools/isaac/pre_merge/pre_merge_validate.py --lint --format

# Run validation + extension tests
python tools/isaac/pre_merge/pre_merge_validate.py --test

# Re-run tests for specific extensions that failed previously
python tools/isaac/pre_merge/pre_merge_validate.py --retest isaacsim.robot.poser isaacsim.robot.schema
```

### Individual Tools

Each check can also be run standalone:

| Script | Description | Example |
|---|---|---|
| `run_python_linting.py` | Run mypy, darglint, interrogate, pydoclint, and ruff on extensions or arbitrary paths | `python tools/isaac/pre_merge/run_python_linting.py --path tools/isaac/pre_merge` |
| `validate_changelog.py` | Check changelog formatting, version entries, and version bump vs base branch | `python tools/isaac/pre_merge/validate_changelog.py source/extensions/isaacsim.robot.poser` |
| `validate_extension_toml.py` | Validate and auto-fix section order, field order, dependencies sort, and whitespace in extension.toml files | `python tools/isaac/pre_merge/validate_extension_toml.py --fix` |
| `validate_extension_structure.py` | Validate extension directory layout (config, data, docs, bindings, etc.) | `python tools/isaac/pre_merge/validate_extension_structure.py source/extensions/isaacsim.robot.poser` |
| `validate_license_headers.py` | Check or repair SPDX license headers in source files | `python tools/isaac/pre_merge/validate_license_headers.py --fix` |
| `run_extension_tests.py` | Discover and run test scripts for specified extensions | `python tools/isaac/pre_merge/run_extension_tests.py isaacsim.robot.poser` |

Some of these scripts are also accessible via `repo.sh` when the repo tool infrastructure is available (e.g. `./repo.sh run_python_linting`).

### Shared Modules

| Module | Purpose |
|---|---|
| `repo_helpers.py` | Repository layout constants (`REPO_ROOT`, `EXTENSION_ROOTS`), extension discovery, TOML loading, and git helpers |
| `term_helpers.py` | ANSI color codes (`Colors`), `colorize()`, and status-line helpers (`log_pass`, `log_fail`, etc.) |

# Troubleshooting

### Permission errors when on VPN on Windows
You may see this error when using VPN on Windows:
```bash
Permission denied (publickey,gssapi-keyex,gssapi-with-mic,password).: exit status 255
```
As a workaround, use ssh key without a passphrase.

Another possible ssh error:

```bash
x509: certificate signed by unknown authority
```
The current solution is to disable SSL verification:

```bash
git config http.sslVerify false
```

### Docker fails with ``permission denied`` errors when building
 * You need to log out and log back in for group changes to take effect.
   If you haven't logged out since installing Docker with ``setup.sh`` or
   adding yourself to the ``docker`` group, you need to log out and log back in.
 * After you have logged out and logged back in, check that your user is in the
   ``docker`` group with the ``groups`` command.
 * Add yourself to the docker group with ``usermod -aG docker ${USER}`` if you
   are not in the ``docker`` group.

### Docker fails with ``docker: Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?`` when building
 * Start the daemon with ``systemctl start docker``
 * Make the daemon always start on boot with ``systemctl enable docker``
 * You can check if the daemon is running with ``systemctl list-units --state=active | grep docker``

## Linux Build Environment

The linux-x86_64 build process uses a docker container to create a consistent
build environment across all systems. `setup.sh` is intended to take care of
installing Docker. We use docker-ce upstream from docker.com rather than the
version which comes with your host linux system.  Should you wish to set up
Docker manually, the process goes roughly as follows on Ubuntu systems:

- sudo apt update
- sudo apt install apt-transport-https ca-certificates curl software-properties-common
- curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
- sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
- sudo apt update
- sudo apt install docker-ce
- sudo usermod -aG docker ${USER} # Then log out and back in

> NOTE: Docker on Windows System for Linux (WSL) is unsupported and likely will not work.

## Building Isaac Sim container

- Execute `./build.sh -r` (Linux) (needs VPN)
- Execute `./tools/internal/container_build.sh` (Linux) (may need to disconnect VPN if you have errors)

To run the container and start Isaac Sim as a headless app:

```bash
docker run --name isaac-sim --entrypoint bash -it --gpus all -e "ACCEPT_EULA=Y" --rm --network=host \
  -e "PRIVACY_CONSENT=Y" -e "PRIVACY_USERID=<nv_email>" \
  -v ~/docker/isaac-sim/cache/kit:/isaac-sim/kit/cache:rw \
  -v ~/docker/isaac-sim/cache/ov:/root/.cache/ov:rw \
  -v ~/docker/isaac-sim/cache/pip:/root/.cache/pip:rw \
  -v ~/docker/isaac-sim/cache/glcache:/root/.cache/nvidia/GLCache:rw \
  -v ~/docker/isaac-sim/cache/computecache:/root/.nv/ComputeCache:rw \
  -v ~/docker/isaac-sim/logs:/root/.nvidia-omniverse/logs:rw \
  -v ~/docker/isaac-sim/data:/root/.local/share/ov/data:rw \
  -v ~/docker/isaac-sim/documents:/root/Documents:rw \
  isaac-sim:<version_tag> \
  ./isaac-sim.streaming.sh --/persistent/isaac/asset_root/default="omniverse://isaac-dev.ov.nvidia.com" --allow-root -v
```

To run the container and start Isaac Sim as a windowed app:

```bash
xhost +
docker run --name isaac-sim --entrypoint bash -it --gpus all -e "ACCEPT_EULA=Y" --rm --network=host \
  -e "PRIVACY_CONSENT=Y" -e "PRIVACY_USERID=<nv_email>" \
  -v $HOME/.Xauthority:/root/.Xauthority \
  -e DISPLAY \
  -v ~/docker/isaac-sim/cache/kit:/isaac-sim/kit/cache:rw \
  -v ~/docker/isaac-sim/cache/ov:/root/.cache/ov:rw \
  -v ~/docker/isaac-sim/cache/pip:/root/.cache/pip:rw \
  -v ~/docker/isaac-sim/cache/glcache:/root/.cache/nvidia/GLCache:rw \
  -v ~/docker/isaac-sim/cache/computecache:/root/.nv/ComputeCache:rw \
  -v ~/docker/isaac-sim/logs:/root/.nvidia-omniverse/logs:rw \
  -v ~/docker/isaac-sim/data:/root/.local/share/ov/data:rw \
  -v ~/docker/isaac-sim/documents:/root/Documents:rw \
  isaac-sim:<version_tag> \
  ./isaac-sim.sh --/persistent/isaac/asset_root/default="omniverse://isaac-dev.ov.nvidia.com" --allow-root
```

> Note that running Isaac Sim as a windowed app in a container is possible but not officially recommended. This works if you have a physical monitor attached but running in a headless or virtual environment may have issues.

