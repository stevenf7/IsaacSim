# Isaac Sim

This repository contains the source code and build tools required to compile and run Isaac Sim. 

## Documentation

For the latest Isaac Sim documentation, release notes, quick start, tutorials, and more, see [Isaac Sim Documentation](https://docs.isaacsim.omniverse.nvidia.com/latest/index.html)

## Prerequisites and Environment Setup

Ensure your system is set up with the following before building Isaac Sim:

- **Operating System**: Windows 10/11 or Linux (Ubuntu 22.04 or newer)

- **GPU**: For additional information on GPU features and requirements, see [NVIDIA GPU Requirements](https://docs.omniverse.nvidia.com/materials-and-rendering/latest/common/technical-requirements.html)

  #### Local Workstation

  | Min | Recommended | Best |
  |-----|-------------|------|
  | RTX 4080 | RTX 5080 | RTX PRO 6000 Blackwell Workstation |

  #### Datacenter

  | Min | Recommended | Best |
  |-----|-------------|------|
  | A40 | L40S | RTX PRO 6000 Blackwell Server |


- **Driver**: See [NVIDIA Driver Requirements](https://docs.omniverse.nvidia.com/materials-and-rendering/latest/common/technical-requirements.html)

- **Internet Access**: Required for downloading the Omniverse Kit SDK, extensions, and tools.



### Required Software Dependencies

- [**Git**](https://git-scm.com/downloads): For version control and repository management

- [**Git LFS**](https://git-lfs.com/): For managing large files within the repository

- **(Windows - C++ Only) Microsoft Visual Studio (2019 or 2022)**: You can install the latest version from [Visual Studio Downloads](https://visualstudio.microsoft.com/downloads/). Ensure that the **Desktop development with C++** workload is selected.  [Additional information on Windows development configuration](docs/readme/windows_developer_configuration.md)

- **(Windows - C++ Only) Windows SDK**: Install this alongside MSVC. You can find it as part of the Visual Studio Installer. [Additional information on Windows development configuration](readme-assets/additional-docs/windows_developer_configuration.md)

- **(Linux) build-essentials**: A package that includes `make` and other essential tools for building applications.  For Ubuntu, install with `sudo apt-get install build-essential`

### Recommended Software

- [**(Linux) Docker**](https://docs.docker.com/engine/install/ubuntu/): For containerized development and deployment. **Ensure non-root users have Docker permissions.**

- [**(Linux) NVIDIA Container Toolkit**](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html): For GPU-accelerated containerized development and deployment. **Installation and Configuring Docker steps are required.**

- [**VSCode**](https://code.visualstudio.com/download) (or your preferred IDE): For code editing and development

## Quick Start

This section guides you through building Isaac Sim from source code.

### 1. Clone the Repository

```bash
git clone <repository-url> isaacsim
cd isaacsim
```

### 2. Build

Run the following command to initiate the configuration wizard:

**Linux:**
```bash
./build.sh
```

**Windows:**
```powershell
build.bat
```

### 3. Run

Navigate to the corresponding binary directory for your platform and run the executable.

**Linux:**
```bash
cd _build/linux-x86_64/release
./isaac-sim.sh
```

**Windows:**
```powershell
cd _build/windows-x86_64/release
isaac-sim.bat
```

> **NOTE:** If this is your first time building Isaac Sim, you will be prompted to accept the Omniverse Licensing Terms.



## Advanced Build Options


Isaac Sim uses a custom build system with the following key options:


### Core Build Options
- `-c, --clean`: Clean the repository and exit
- `-x, --rebuild`: Clean the repository before building (full rebuild)
- `-h, --help`: Show all available build options


### Configuration Options
- `--config [debug|release]`: Specify build configuration (default: both)
- `-d, --debug`: Build only debug configuration
- `-r, --release`: Build only release configuration


### Advanced Options
- `-j NUM_CORES, --jobs NUM_CORES`: Limit the number of parallel compilation jobs
- `-v, --verbose`: Enable verbose build output
- `-q, --quiet`: Suppress build output


### Build Steps Control
- `--fetch-only`: Only fetch dependencies and stop
- `-g, --generate`: Generate projects, stage files and stop
- `-s, --stage`: Stage files, skip generation step
- `-b, --build-only`: Only perform building step, skip others
- `--post-build-only`: Only perform post-build step


## Feature Branch Information
**This repository is based on a Feature Branch of the Omniverse Kit SDK.** Feature Branches are regularly updated and best suited for testing and prototyping.

[Omniverse Release Information](https://docs.omniverse.nvidia.com/dev-overview/latest/omniverse-releases.html#)


## License
This repository is licensed under the [Apache-2.0 License](LICENSE).

Additional components like the Omniverse Kit SDK are governed by the [NVIDIA Software License Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-software-license-agreement/) and the [Product-Specific Terms for NVIDIA Omniverse](https://www.nvidia.com/en-us/agreements/enterprise-software/product-specific-terms-for-omniverse/).



## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for more information.