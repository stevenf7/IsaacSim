# omniverse-image-scripts

> Wrapper scripts that can be used for building Omniverse Docker images.


- [omniverse-image-scripts](#omniverse-image-scripts)
  - [Requirements](#requirements)
  - [Cache Generation](#cache-generation)
    - [Example](#example)
  - [Docker](#docker)
    - [Details](#details)
    - [Example](#example-1)


## Requirements

This project should be included as a [git submodule](https://git-scm.com/book/en/v2/Git-Tools-Submodules) in the image project.

Example `.gitmodules` (from **[omniverse / farm / containers](https://gitlab-master.nvidia.com/omniverse/farm/containers)** project location):

```bash
[submodule "omniverse-image-scripts"]
  path = bin
  url = ../../devops/scripts/omniverse-image-scripts
  branch = main
```

## Cache Generation

The `cache-generation` directory contains the generic pipeline requirements to generate shader cache for Omniverse applications.

Since each application import path is different, the `.kit` file must be modified to replace `${APP_IMPORT_PATH}` with the actual import path for the application.

### Example

To replace the import path for an application (eg. **Create**), with an import path `omni.create`, the following command can be used (eg. using `sed`):

```
#!/bin/bash

APP_IMPORT_PATH="omni.create"
sed "s|\${APP_IMPORT_PATH}|$APP_IMPORT_PATH|g" ./cache-generation/generate_shader_cache.kit > /path/to/destination/
```

## Docker

### Details

Building locally:

```bash
export BUILD=<image_config_build>
./bin/docker/build.sh
```

### Example

See **[Omniverse / Containers / Apps](https://gitlab-master.nvidia.com/omniverse/containers/apps)** for example projects.
