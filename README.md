# Omniverse Isaac Sim
This is where the Omniverse Isaac Sim application is developed.

* [Internal Documentation](https://isaac.gitlab-master-pages.nvidia.com/omni_isaac_sim/isaacsim/latest/index.html)
* [Public Documentation](https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/overview.html)
* Slack: [#omni-isaac-support](https://nvidia.slack.com/archives/CBDM22E5P)
* [Confluence](https://confluence.nvidia.com/display/OMNIVERSE/Omniverse+Isaac+Sim)

# Getting Started

See [here](https://isaac.gitlab-master-pages.nvidia.com/omni_isaac_sim/isaacsim/latest/requirements.html) for general hardware and driver requirements

There are multiple ways to use isaac sim based on your workflow:

## Source (This repository)
See [Using The Source Repository](#using-the-source-repository) section below for how to compile source and set up `git lfs`
#### Branches:
* [Release/2023.1](https://gitlab-master.nvidia.com/omniverse/isaac/omni_isaac_sim/-/tree/release/2023.1): Current Release Candidates and Public Release (rc.x)
* [Develop](https://gitlab-master.nvidia.com/omniverse/isaac/omni_isaac_sim/-/tree/develop): Latest internal codebase, updated daily (alpha.x, beta.x)
* [Tagged Releases](https://gitlab-master.nvidia.com/omniverse/isaac/omni_isaac_sim/-/tags): Older release commits are tagged here

See [Isaac Sim Release Flow](https://docs.google.com/presentation/d/161QpSIxvXvAmZO1QeniJ-sMWdUhbX8iWUHpmg2sCHAA/edit?usp=sharing)

## Binary Builds (Omniverse Launcher) **[Recommended]**

* Download the internal [Integration](https://web.launcher.omniverse.nvidia.com/exchange/app) Omniverse Launcher App
* Use ``chmod +x`` to make it executable if needed

Once launched you will see the builds under the ``Exchange`` tab

* [Isaac Sim](https://web.launcher.omniverse.nvidia.com/exchange/app/isaac_sim): Latest build from Release branch. This build works staging or production assets. (Use the Release channel only)
* [Isaac Sim Daily](https://web.launcher.omniverse.nvidia.com/exchange/app/isaac_sim-daily): Latest daily build from Develop branch. This build works with our internal isaac-dev.ov.nvidia.com Nucleus by default. (Use the Beta channel only)
* [Isaac Sim Public Release](https://web.launcher.omniverse.nvidia.com/exchange/app/prod-isaac_sim): Latest public release. This build works with localhost Nucleus by default.
* [Isaac Sim Assets Pack 1](https://web.launcher.omniverse.nvidia.com/exchange/content-pack/isaac_sim-assets-1?text=&kind=content-pack): Latest asset pack download for use in an air-gapped environment. Pack 1 of 3.
* [Isaac Sim Assets Pack 2](https://web.launcher.omniverse.nvidia.com/exchange/content-pack/isaac_sim-assets-2?text=&kind=content-pack): Latest asset pack download for use in an air-gapped environment. Pack 2 of 3.
* [Isaac Sim Assets Pack 3](https://web.launcher.omniverse.nvidia.com/exchange/content-pack/isaac_sim-assets-3?text=&kind=content-pack): Latest asset pack download for use in an air-gapped environment. Pack 3 of 3.

For information on launching once you have downloaded a build [see here](https://isaac.gitlab-master-pages.nvidia.com/omni_isaac_sim/isaacsim/latest/install_workstation.html).

> Note that our documentation shows the public Omniverse launcher where daily builds are not available, but the process of running Isaac Sim is identical.

## Binary Builds (Packman Manual Download)
* [Stable RC Builds from Release branch](http://packman.ov.nvidia.com/packages/isaac-sim-standalone?search=rc)
* [Daily Alpha Builds from Develop branch](http://packman.ov.nvidia.com/packages/isaac-sim-standalone?search=alpha)
* [Daily Beta Builds from Develop branch](http://packman.ov.nvidia.com/packages/isaac-sim-standalone?search=beta)
* [Internal-only Builds from Develop branch (for internal tests/benchmarking)](http://packman.ov.nvidia.com/packages/isaac-sim-internal)

## Binary Builds (Teamcity Manual Download)

* [Linux-x86_64 Binary From Release branch](https://teamcity.nvidia.com/repository/download/Omniverse_IsaacSim_Release_BuildAndValidation/.lastSuccessful/artifacts/Linux/isaac-sim-standalone%40%7Bbuild.number%7D.linux-x86_64.release.7z)
* [Linux-x86_64 Binary From Develop branch](https://teamcity.nvidia.com/repository/download/Omniverse_IsaacSim_Develop_BuildAndValidation/.lastSuccessful/artifacts/Linux/isaac-sim-standalone%40%7Bbuild.number%7D.linux-x86_64.release.7z)

## Docker Containers (GitLab)

* Isaac Sim: [gitlab-master.nvidia.com:5005/isaac/omni_isaac_sim/isaac-sim:latest-20xx.x](https://gitlab-master.nvidia.com/omniverse/isaac/omni_isaac_sim/container_registry/6641) (Release branch, rc)
* Isaac Sim Daily: [gitlab-master.nvidia.com:5005/isaac/omni_isaac_sim/isaac-sim:latest-develop](https://gitlab-master.nvidia.com/omniverse/isaac/omni_isaac_sim/container_registry/6641) (Develop branch, alpha/beta)

## Docker Containers (NGC)

* Isaac Sim Public: [nvcr.io/nvidia/isaac-sim:20xx.x.x](https://catalog.ngc.nvidia.com/orgs/nvidia/containers/isaac-sim) Similar to Prod-Isaac Sim from the Integ Launcher.
* Isaac Sim: [nvcr.io/nvidian/isaac-sim:latest-20xx.x](https://registry.ngc.nvidia.com/orgs/nvidian/containers/isaac-sim/tags) Similar to RC Builds from the Integ Launcher. Built from the Release branch. For anyone in the ``nvidian`` org in NGC.
> To get access to the containers below, fill up and submit this [form](https://goo.gl/forms/IjKBiZRt4RYZcF3h1). Select the ``omniverse [For Omniverse Team (Susan Fong)]`` team. Post on [#swngc-help](https://nvidia.slack.com/archives/C7VGNG1V3) if you have issues getting access to the ``nvidian/omniverse`` NGC team.
* Isaac Sim: [nvcr.io/nvidian/omniverse/isaac-sim:latest-20xx.x](https://registry.ngc.nvidia.com/orgs/nvidian/teams/omniverse/containers/isaac-sim/tags) Similar to RC Builds from the Integ Launcher. Built from the Release branch.
* Isaac Sim Daily: [nvcr.io/nvidian/omniverse/isaac-sim:latest-develop](https://registry.ngc.nvidia.com/orgs/nvidian/teams/omniverse/containers/isaac-sim/tags) Similar to Alpha and Beta Builds from the Integ Launcher. Built from the Develop branch.
* Isaac Sim Internal-only: [nvcr.io/nvidian/omniverse/isaac-sim:latest-develop-internal](https://registry.ngc.nvidia.com/orgs/nvidian/teams/omniverse/containers/isaac-sim/tags) Similar to Internal-only builds from the Develop branch.

Notes:
  - See [Branches](#branches)
  - See [Binary Builds (Omniverse Launcher)](#binary-builds-omniverse-launcher-recommended)

## Native Python Sample Repository

For certain python only usecases we have a [separate repository](https://gitlab-master.nvidia.com/Isaac/omni_isaac_sim_python)

This repository will automatically pull a specific binary package from our packman repository and extract it for use in your branch/fork.
It is ideal if you want to write native python scripts and need place to work where the version of Isaac Sim is deterministic. See the repo for more information on usage.

# Developer Resources

See the [wiki section](https://gitlab-master.nvidia.com/omniverse/isaac/omni_isaac_sim/-/wikis/home) of this repo for developer resources and docs.

* [Filing Bugs And Requests](https://gitlab-master.nvidia.com/omniverse/isaac/omni_isaac_sim/-/wikis/Developer-Resources/Jira-Board#creating-a-new-issue)
* [Submitting a merge request](https://gitlab-master.nvidia.com/omniverse/isaac/omni_isaac_sim/-/wikis/Developer-Resources/Merge-Request)

# Running headless and connecting via a remote client

See [here](https://isaac.gitlab-master-pages.nvidia.com/omni_isaac_sim/isaacsim/latest/install_container.html) for more information on how to use the container.

# List of internal nucleus servers:
* isaac-dev.ov.nvidia.com : http://isaac-dev.ov.nvidia.com/
    - For development work (most internal users use this)
    - Note: ov-isaac-dev.nvidia.com will redirect to the server above.

# Using the Omniverse cache service

## Cache Status
To check the status of your nucleus cache go to [localhost:3080/cache](http://localhost:3080/cache).

You can also clear your local cache from here and see used disk space

## Deleting previous installs

* Download and run the [launcher cleanup tool](https://isaac.gitlab-master-pages.nvidia.com/omni_isaac_sim/prod_launcher/prod_utilities/cleanup-tool.html)
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
- Install Ubuntu 20.04 (linux-x86_64) / Windows 10 version 1903 (windows-x86_64 and DXR)
- Install NVIDIA driver 525.60 (Linux) / NVIDIA driver 527.37 (Windows)
    * [Linux] (http://eris-dl-b006.nvidia.com)
    * [NVIDIA OMNIVERSE - Driver Requirements](https://developer.nvidia.com/omniverse/driver)
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
- Clone your fork to a local hard drive, make sure to use a NTFS drive on Windows (Carbonite uses symbolic links)
- Execute `./setup.sh` (Linux) which will install Docker. Logging out and back
  in is required to update your account's group membership to include "docker".

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

- See [Here](https://isaac.gitlab-master-pages.nvidia.com/omni_isaac_sim/isaacsim/latest/install_python.html)

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

## Running TeamCity builds and tests locally

Linux Builds ``./tools/ci/build-and-packaging/linux-x86_64/step.sh``

Linux Tests  ``./tools/ci/testing/linux-x86_64-python-tests/step.sh``

## TeamCity Pipelines
Release: [![pipeline status](http://teamcity.nvidia.com/app/rest/builds/buildType(id:Omniverse_IsaacSim_Release_BuildAndValidation)/statusIcon)](https://teamcity.nvidia.com/viewType.html?buildTypeId=Omniverse_IsaacSim_Release_BuildAndValidation&tab=buildTypeHistoryList&Omniverse_IsaacSim_Release_BuildAndValidation=%3Cdefault%3E&branch_Omniverse_IsaacSim_Release=%3Cdefault%3E)

Develop: [![pipeline status](http://teamcity.nvidia.com/app/rest/builds/buildType(id:Omniverse_IsaacSim_Develop_BuildAndValidation)/statusIcon)](https://teamcity.nvidia.com/viewType.html?buildTypeId=Omniverse_IsaacSim_Develop_BuildAndValidation&tab=buildTypeHistoryList&Omniverse_IsaacSim_Develop_BuildAndValidation=%3Cdefault%3E&branch_Omniverse_IsaacSim_Develop=%3Cdefault%3E)

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
- Execute `./container_build.sh` (Linux) (may need to disconnect VPN if you have errors)

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
  ./isaac-sim.headless.native.sh --/persistent/isaac/asset_root/default="omniverse://isaac-dev.ov.nvidia.com" --allow-root -v
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
