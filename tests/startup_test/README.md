# OVAT `run_test` Tool

`run_test` is a  command line tool to help you run OVAT tests locally and in a CI environment.

When used locally it takes care of installing all the pre-requisites (as described in the
 [OVAT Development Environment](https://ovat.gitlab-master-pages.nvidia.com/documentation/userguide/environment_setup/)
 documentation) and executing your Test via GCN. It first reads your `ovat_test.toml`
 file to apply any overrides to Inputs that may be required for your local environment.

When used in CI it takes care of create a Job which runs your Test in the [OVAT Cluster](https://ovat.gitlab-master-pages.nvidia.com/documentation/architecture/ovat_cluster/),
as defined in your `task_architect.yml`. It will communicate your Test Outputs to your CI
system automatically. You can specify special Input overrides from CI parameters in your
`ovat_test.toml` file.

## Getting Started

1. Go to the [releases](https://gitlab-master.nvidia.com/ovat/run-test/-/releases) page and
 download the latest release zip file (ie. `run-test.1.2.0.zip`)
2. Extract the archive into your Test folder (so that the `run_test.[bat/sh]` is
sibling to the `src` folder, `gcn.yml` and `ovat_test.toml` as described in the OVAT
Test Structure page). (TODO: update docs and link page)
3. If you don't have an OVAT Test, please follow the [OVAT User Guide](https://ovat.gitlab-master-pages.nvidia.com/documentation/userguide/)
to learn how to write an OVAT Test.
4. You can now run your test locally using `run_test.[bat/sh]`

Read below how to integrate your Test to CI system.

### `tools` Folder

A `tools` folder is provided in the release ZIP which contains:

* a copy of [packman](https://gitlab-master.nvidia.com/hfannar/packman) in the `packman` folder
* OVAT tooling in the `ovat` folder

If your repo already contains a version of packman, you many use that instead of
the bundled packman.

You may move the `ovat` folder to a different location in your repo as well.

If you change the default structure of `tools/packman` and `tools/ovat`, make sure you modify
`run_test.[bat/sh]` to reflect the correct paths for your repository.

## CI Integration

### Teamcity

There is a `teamcity.ps1` Powershell script provided in `tools/ovat` which can be used in a
Teamcity Build Step to execute your OVAT Test.

It is recommended to have your OVAT Test run in a completely separate Build Configuration
from your artifact-generating Build Configurations to aid in organization, but it is not required.

#### Instructions

1. Create a Build Step with the `PowerShell` **Runner Type**. Make sure that **Script file**
points to wherever your `teamcity.ps1` file is located in your repo.
2. **You must configure the Working Directory** in the Build Step **Advanced Options**
to be the path which contains your Test's `ovat_test.toml` and `task_architect.yml` files,
**not** the path to `teamcity.ps1`. The Working Directory is how your specific test is
selected, in case you have a repo with many tests.
