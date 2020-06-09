# Omniverse Isaac Sim
This is where the Robotics experiece for Omniverse is developed

[Confluence](https://confluence.nvidia.com/display/OMNIVERSE/Omniverse+Isaac+Simulator)

[Tagged Releases](https://gitlab-master.nvidia.com/Isaac/omni_isaac_sim/-/releases)

### Latest Docs and Master Packages

[Documentation](http://isaac.gitlab-master-pages.nvidia.com/omni_isaac_sim)

[Linux-x86_64 Binary From Master](https://teamcity.nvidia.com/repository/download/Carbon_Isaac_OmniIsaacSim_Master_BuildAndPackaging_BuildLinuxX8664/.lastSuccessful/isaac-sim%40%7Bbuild.number%7D-linux-x86_64-release.7z)

### Filing Bugs
[Omniverse JIRA](https://nvidia-omniverse.atlassian.net/secure/RapidBoard.jspa?rapidView=25049)

### Branches
Master: Stable, should be used by most users
Develop: Latest Codebase

### List of internal servers:
* ov-isaac : http://ov-isaac.nvidia.com/

    For releases or demos (content that doesn't change much)

* ov-isaac-dev : http://ov-isaac-dev.nvidia.com/

    For development work

* ov-isaac-qa : http://ov-isaac-qa.nvidia.com/

    For QA testing or messing around
    Content can be purged periodically
    This server will be use for server version updates

[Status of internal servers](http://stl-isaac/)


### TeamCity Pipelines
Master: [![pipeline status](http://teamcity.nvidia.com/app/rest/builds/buildType(id:Carbon_Isaac_OmniIsaacSim_Master_BuildAndPackagingValidation)/statusIcon)](https://teamcity.nvidia.com/viewType.html?buildTypeId=Carbon_Isaac_OmniIsaacSim_Master_BuildAndPackagingValidation&tab=buildTypeHistoryList&Carbon_Isaac_OmniIsaacSim_Master_BuildAndPackagingValidation=%3Cdefault%3E&branch_Carbon_Isaac_OmniIsaacSim_Master=%3Cdefault%3E)

Develop: [![pipeline status](http://teamcity.nvidia.com/app/rest/builds/buildType(id:Carbon_Isaac_OmniIsaacSim_Develop_BuildAndPackagingValidation)/statusIcon)](https://teamcity.nvidia.com/viewType.html?buildTypeId=Carbon_Isaac_OmniIsaacSim_Develop_BuildAndPackagingValidation&tab=buildTypeHistoryList&Carbon_Isaac_OmniIsaacSim_Develop_BuildAndPackagingValidation=%3Cdefault%3E&branch_Carbon_Isaac_OmniIsaacSim_Develop=%3Cdefault%3E)

## Prerequisites
#### Hardware
- GPU supporting DirectX Raytracing or Vulkan Raytracing (This includes Pascal cards with 6 GB of RAM or more, Volta or Turing GPUs)

#### Linux/Windows
- Install Ubuntu 18.04+ (linux-x86_64) / Windows 10 version 1809+ (windows-x86_64 and DXR)
- Install NVIDIA driver 440.59+ (Linux) / NVIDIA driver 442.19+ (Windows)
- Install VS Code (recommended) or VS2017 with [SDK 10.17763+](https://go.microsoft.com/fwlink/?LinkID=2023014)
- (Optional) Install Vulkan SDK 1.1.106.0:
    * Required for debug builds and validation layers only.
    * [Windows] (https://sdk.lunarg.com/sdk/download/1.1.106.0/windows/VulkanSDK-1.1.106.0-Installer.exe)
    * [Linux] (https://sdk.lunarg.com/sdk/download/1.1.106.0/linux/vulkansdk-linux-x86_64-1.1.106.0.tar.gz)
- Install "git".
- Install "git-lfs":
    * Required for fetching data folder used in unit tests only.
    * Reboot your machine after installation.
    * Execute `git lfs install` once to enable LFS features after installation.
        * If you cloned the repo before above steps, you have to fetch the data with `git lfs pull` in the repo.
- [Fork omniverse isaac sim repository](https://gitlab-master.nvidia.com/Isaac/omni_isaac_sim/forks/new)
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


## Building omniverse-kit

- Execute `./build.sh` (Linux) / `build.bat` (Windows)
- Use `--help` to get more information. You can run only parts of build process, e.g:
    * `build.bat -s` to only copy/link files
    * `build.bat -d` to build only debug configuration
    * `build.bat -r` to build only release configuration
    * `build.bat -x` to do a clean and rebuild

The build output will be found in the generated
`_build` folder and the make/solution files will be found in the generated `_compiler` directory. Occasionally, when
drastic project level changes are made, you may have to regenerate these files using `--rebuild` option with the build
script.

The default setting is to target x86_64 CPU architecture when building on
x86_64 hosts. If you want to target arm64 (aarch64) then run
```bash
./build.sh -p linux-aarch64.
```

> NOTE: To build the project minimal configuration is needed. Any version of Windows 10 or Linux with Docker will do. Then
run the setup and build scripts as described here above. That's it. The specific version of Windows, NVIDIA driver,
and Vulkan are all runtime dependencies, not compile/link time dependencies. This allows omniverse-kit to build on stock
virtual machines that require zero configuration. This is a beautiful thing, help us keep it that way.

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

## Running omniverse-kit

- Go to debug or release folder under _build/xxx-x86_64 (x86_64 platforms only)
- Execute `./isaac-sim.sh` (Linux) / `isaac-sim.bat` (Windows)

---

## Packaging

- Use `./tools/package.sh` (Linux) / `tools/package.bat` (Windows):
    * `tools/package.bat -c debug -m omniverse-kit` create a package in `_builtpackages`

---

## Running Tests

- Use `./tools/test_runner.sh` (Linux) / `tools/test_runner.bat` (Windows) to run different tests suites.
- `--help` can give all the info on the arguments, for instance to run python tests on debug:
    * `tools/test_runner.bat -c debug --suite pythontests`

- Pass extra arguments to test with `-e`/`--extra-arg` command:
    * `tools/test_runner.bat -c debug --suite unittests -e [graphics]`

- Use `--from-pacakge`/`-p` to run tests against the package from `_builtpackages` folder. That is useful for mimicking TC setup:
    * `tools/test_runner.bat ---suite unittests -p` -- unzips package in folder nearby (once) and runs tests in it.

---

## Troubleshooting

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

---

## FAQ

### Adding new default resolutions to Kit
edit the following file:
``source/apps/configs/omniverse-kit.json``
And in this section:

```json
"renderer": {
    "resolution": {
        "list": [2048, 1080, 1920, 1080, 1280, 720, 1024, 1024, 512, 512],
        "multiplierList": [2.0, 1.0, 0.666666666666, 0.5, 0.333333333333, 0.25]
    }
},
```
Modify ``list`` and add your resolutions pair.
Ex: Adding a new resolution of 1024x768:

```json
"renderer": {
    "resolution": {
        "list": [2048, 1080, 1920, 1080, 1280, 720, 1024, 1024, 512, 512, 1024, 768],
        "multiplierList": [2.0, 1.0, 0.666666666666, 0.5, 0.333333333333, 0.25]
    }
},
```
Run ``./build.sh`` to update the application config so that it gets executed the next time you run ./isaac-sim.sh

---
### Running headless and connecting via a remote client

On the client machine, download the Client Application from the following page for your platform:
https://developer.nvidia.com/isaac-sim/download

Run the client:
``./omniverse-kit-remote.app -s server_ip``

On the server machine Launch kit via:
``./_build/linux-x86_64/release/isaac-sim-headless.sh``

---
### Running TeamCity builds and tests locally
 
Linux Builds ``./tools/ci/build-and-packaging/linux-x86_64/step.sh``

Linux Tests  ``./tools/ci/testing/test-linux-x86_64-release/step.sh``

Linux Startup Tests  ``tools/ci/testing/test-linux-x86_64-release-startup-tests-ubuntu18/step.sh``

Windows Builds ``tools\ci\build-and-packaging\windows-x86_64\step.bat``

Windows Tests ``tools\ci\testing\test-windows-x86_64\step.bat``

---
### Debugging in vscode on linux

press Ctrl-Shift-D and then select the configuration you would like to run:

- (linux) isaac-sim \[release\]
- (linux) isaac-sim \[debug\]