# Omniverse Isaac Sim
This is where the Robotics experience for Omniverse is developed

[Confluence](https://confluence.nvidia.com/display/OMNIVERSE/Omniverse+Isaac+Sim)

[Tagged Releases](https://gitlab-master.nvidia.com/Isaac/omni_isaac_sim/-/releases)

[Internal Documentation](https://isaac.gitlab-master-pages.nvidia.com/omni_isaac_sim/app_isaacsim/app_isaacsim/overview.html)

[Public Documentation](https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/overview.html)

Slack: [#ct-omni-isaac-support](https://nvidia.slack.com/archives/CBDM22E5P)


# Getting Started

[See here for general hardware and driver requirements](https://isaac.gitlab-master-pages.nvidia.com/omni_isaac_sim/app_isaacsim/app_isaacsim/requirements.html)

There are multiple ways to use isaac sim based on your workflow:

## Source (This repository)
See **Using Source Repository** section below for how to compile source and set up `git lfs`
#### Branches:
* [Release/2021.2](https://gitlab-master.nvidia.com/Isaac/omni_isaac_sim/-/tree/release/2021.2): Current Stable, should be used by most users
* [Develop](https://gitlab-master.nvidia.com/Isaac/omni_isaac_sim/-/tree/develop): Latest Codebase, updated daily

## Binary Builds (Omniverse Launcher) **[Recommended]**

* Download the internal [Integration](https://web.launcher.omniverse.nvidia.com/exchange/app) Omniverse Launcher App
* Use ``chmod +x`` to make it executable if needed

Once launched you will see the builds under the ``Exchange`` tab 

* [Isaac-Sim](http://ov-launcher/exchange/app/isaac_sim): Latest build from Release/2021.2 branch. This build works with localhost Nucleus by default.
* [Isaac-Sim Daily](http://ov-launcher/exchange/app/isaac_sim-daily): Latest daily build from Develop branch. This build works with our internal ov-isaac-dev.nvidia.com Nucleus by default.

For information on launching once you have downloaded a build [see here](https://isaac.gitlab-master-pages.nvidia.com/omni_isaac_sim/app_isaacsim/app_isaacsim/install_basic.html). 

> Note that our documentation shows the public Omniverse launcher where daily builds are not available, but the process of running Isaac-Sim is identical. 

## Binary Builds (Packman Manual Download)
* [Stable Builds from Release](http://packman.ov.nvidia.com/packages/isaac-sim-standalone?search=rc)
* [Daily Builds from Develop](http://packman.ov.nvidia.com/packages/isaac-sim-standalone?search=beta)

## Binary Builds (Teamcity Manual Download)

* [Linux-x86_64 Binary From Release](https://teamcity.nvidia.com/repository/download/Omniverse_IsaacSim_Release_BuildAndValidation/.lastSuccessful/artifacts/Linux/isaac-sim-standalone%40%7Bbuild.number%7D.linux-x86_64.release.7z)
* [Linux-x86_64 Binary From Develop](https://teamcity.nvidia.com/repository/download/Omniverse_IsaacSim_Develop_BuildAndValidation/.lastSuccessful/artifacts/Linux/isaac-sim-standalone%40%7Bbuild.number%7D.linux-x86_64.release.7z)

## Docker Containers (GitLab)

* Isaac-Sim: [gitlab-master.nvidia.com:5005/isaac/omni_isaac_sim/isaac-sim:latest-2021.2](https://gitlab-master.nvidia.com/Isaac/omni_isaac_sim/container_registry/6641)
* Isaac-Sim Daily: [gitlab-master.nvidia.com:5005/isaac/omni_isaac_sim/isaac-sim:latest-develop](https://gitlab-master.nvidia.com/Isaac/omni_isaac_sim/container_registry/6641)

## Docker Containers (NGC)

* Isaac-Sim Public: [nvcr.io/nvidia/isaac-sim:2021.2.0](https://catalog.ngc.nvidia.com/orgs/nvidia/containers/isaac-sim)
* Isaac-Sim: [nvcr.io/omniverse/isaac-internal/isaac-sim:latest-2021.2](https://ngc.nvidia.com/containers/omniverse:isaac-internal:isaac-sim)
* Isaac-Sim Daily: [nvcr.io/omniverse/isaac-cesspool/isaac-sim:latest-develop](https://ngc.nvidia.com/containers/omniverse:isaac-cesspool:isaac-sim)

## Native Python Sample Repository

For certain python only usecases we have a [separate repository](https://gitlab-master.nvidia.com/Isaac/omni_isaac_sim_python)

This repository will automatically pull a specific binary package from our packman repository and extract it for use in your branch/fork. 
It is ideal if you want to write native python scripts and need place to work where the version of isaac-sim is deterministic. See the repo for more information on usage.

# Running headless and connecting via a remote client

See [here](https://isaac.gitlab-master-pages.nvidia.com/omni_isaac_sim/app_isaacsim/app_isaacsim/install_advanced.html) for more information on how to use the remote clients.

# List of internal nucleus servers:
[Status of internal servers](http://stl-isaac/)
* ov-isaac-dev : http://ov-isaac-dev.nvidia.com/
    * For development work (most internal users use this)
* ov-isaac : http://ov-isaac.nvidia.com/
    * For releases or demos (content that doesn't change much)
* ov-isaac-qa : http://ov-isaac-qa.nvidia.com/
    * For QA testing or messing around
    * Content can be purged periodically
    * This server will be use for server version updates

Note: For first time login, click "Create Account". Enter you SSO username (without the @nvidia.com) and choose any password. Reuse this password to login.

# Using the Omniverse cache service

## Cache Status
To check the status of your nucleus cache go to [localhost:3080/cache](http://localhost:3080/cache). 

You can also clear your local cache from here and see used disk space

## Deleting previous installs

* Uninstall previous installs
    * Run ``sudo apt remove 'omniverse*'`` to remove all previously installed omniverse packages. 
    * You might need to manually delete `omniverse-cache-enabler`
        * use ``which omniverse-cache-enabler`` to determine the location. If it doesn't exist then you can go to the next step.
        * remove using ``sudo rm -rf /path/returned/from/above/omniverse-cache-enabler``

* Download and run the [launcher cleanup tool](https://isaac.gitlab-master-pages.nvidia.com/omni_isaac_sim/prod_launcher/prod_utilities/cleanup-tool.html)
    * Run ``./launcher-cleanup``
    * This tool will delete any installed omniverse applications and will ask if you want to delete your local nucleus data. 
    * Run with ``sudo`` if you have trouble installing cache from the launcher.

## Install Cache

* Download the internal [Integration](http://ov-launcher/exchange/app) Omniverse Launcher App
* Use ``chmod +x`` to make it executable if needed
* Once launched you will see Cache under the ``Exchange`` tab  and can install it from there. If there are failures you will see a red icon in the upper right. 

## Starting Cache

After a reboot you will need to:
- Start omniverse launcher
- go to [localhost:3080/cache](http://localhost:3080/cache). 
- Stop and Start the cache service
- Start isaac-sim and use like normal

> If the cache icon in the upper right of isaac sim says ``CACHE: ON`` but becomes ``CACHE: OFF`` after startup, stop and start the cache service from the web ui. Isaac sim also need to be restarted


# Filing Bugs and Requests
Use the links below to create a new bug/feature request in our [Isaac Sim JIRA Board](https://nvidia-omniverse.atlassian.net/secure/RapidBoard.jspa?rapidView=25049)

* [Create New Bug](https://nvidia-omniverse.atlassian.net/secure/CreateIssueDetails!init.jspa?pid=15222&issuetype=1&assignee=hmazhar&customfield_16630=17684&components=22384)
* [Create New Task/Request](https://nvidia-omniverse.atlassian.net/secure/CreateIssueDetails!init.jspa?pid=15222&issuetype=3&assignee=hmazhar&customfield_16630=17684&components=22384&priority=10)


# Using Source Repository

#### Linux/Windows
- Install Ubuntu 18.04/20.04 (linux-x86_64) / Windows 10 version 1903 (windows-x86_64 and DXR)
- Install NVIDIA driver 470.57 (Linux) / NVIDIA driver 471.41 (Windows)
    * [Linux] (http://eris-dl-b006.nvidia.com)
    * [NVIDIA OMNIVERSE - Driver Requirements](https://developer.nvidia.com/omniverse/driver)
- Install [VS Code](https://code.visualstudio.com/)
- Install "git".
- Install "git-lfs":
    * Required for fetching data folder used in unit tests only.
    * Reboot your machine after installation.
    * Execute `git lfs install` once to enable LFS features after installation.
        * If you cloned the repo before above steps, you have to fetch the data with `git lfs pull` in the repo.
- [Fork omniverse isaac sim repository](https://gitlab-master.nvidia.com/Isaac/omni_isaac_sim/-/forks/new)
- Go to your newly created fork in GitLab, select
    * go to "Settings->Repository->Mirroring repositories"
        * set "Git repository URL" to https://gitlab-master.nvidia.com/Isaac/omni_isaac_sim.git
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

## Running Isaac Sim

- Go to debug or release folder under `_build/{platform}/{config}`
- Execute `./isaac-sim.sh` (Linux) / `isaac-sim.bat` (Windows)

## Debugging With VScode

To run isaac sim with a debugger attached:
- Go to the `Run and Debug` panel (or press `Ctrl+Shift+D`)
- From the dropdown select `(Linux) isaac-sim [release]` or `(Linux) isaac-sim [debug]` depending on the build configuration you wish to run. 
- Press the green play button to start debugging
- Breakpoints can be set directly in cpp files

To attach a debugger to a running application:

- See [Here](https://isaac.gitlab-master-pages.nvidia.com/omni_isaac_sim/app_isaacsim/app_isaacsim/install_python.html)

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

- all tests are in the `_build/{platform}/{config}` folder and start with `tests-*` in the filename. There is one test per extension or python sample.

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


<!-- Linux Startup Tests  ``tools/ci/testing/test-linux-x86_64-release-startup-tests-ubuntu18/step.sh`` -->

<!-- Windows Builds ``tools\ci\build-and-packaging\windows-x86_64\step.bat``

Windows Tests ``tools\ci\testing\test-windows-x86_64\step.bat`` -->

