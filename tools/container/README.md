# ov-kit

> Docker image that provides the Omniverse Kit SDK.

Contents:

- [ov-kit](#ov-kit)
  - [Details](#details)
  - [Gitlab](#gitlab)
    - [Main branch](#main-branch)
    - [Release branches](#release-branches)
    - [Required CI/CD Variables](#required-cicd-variables)
  - [Local Development](#local-development)
    - [Submodules](#submodules)
    - [Building](#building)

## Details

This project leverages the Omniverse end-to-end Docker release workflow, created and maintained by the Omniverse Microservices team.

See **[this confluence page](https://confluence.nvidia.com/display/OMNIVERSE/Omniverse+Docker+End-to-End+%28v3%29+Workflow)** for more details.

## Gitlab

It is important to understand the differences between the various branches used on this project.

### Main branch

The main branch is used to define the "skeleton" of the project. This includes everything **except** the generated `Dockerfiles` which are required to actually build images.

This allows maintainers to update and version the project structure/template files freely without creating images.

As a result, the **build pipeline** is disabled on this branch (and all tags associated to this branch):

```
variables:
  BUILD_PIPELINE_ENABLED: "false"
```

### Release branches

The release branches are used to generate images, either automatically via the **release pipeline** project or manually via development branches.

As a result, these branches must contain generated `Dockerfiles`, and the **build pipeline** must be enabled:

```
variables:
  BUILD_PIPELINE_ENABLED: "true"
```

### Required CI/CD Variables

| Variable name          | Type     | Masked  | Description                                                     |
| ---------------------- | -------- | ------- | --------------------------------------------------------------- |
| `NSPECT_ID`            | Variable |         | The NSPECT security scanner ID for the application.             |
| `VAULT_ADDR`           | Variable |         | The vault address to use (eg. `https://prod.vault.nvidia.com`). |
| `VAULT_JWT_MOUNT_PATH` | Variable | **yes** | The vault JWT auth backend/mount path to use.                   |
| `VAULT_JWT_ROLE`       | Variable | **yes** | The vault JWT auth role to use.                                 |
| `VAULT_NAMESPACE`      | Variable |         | The vault namespace to use.                                     |

## Local Development

### Submodules

When first cloning the project, be sure to initialize all the git submodules:

```bash
# initialize root submodules
git submodule init
git submodule update --recursive

# initialize docker submodules
cd docker
git submodule init
git submodule update --recursive
cd ..
```

### Building

```bash
./repo.sh ci build -c release
./tools/packman/packman install "7za" "16.02.4" -l "7za"
rm -rf tools/container/_inputs/*/
7za/linux-x86/64/7za x _build/packages/isaac-sim-standalone*.7z -otools/container/_inputs/isaac-sim
env BUILD=isaac-sim-dev ./tools/container/bin/docker/build.sh
```

See **[omniverse image scripts](https://gitlab-master.nvidia.com/omniverse/farm/devops/scripts/omniverse-image-scripts)** for build details.

