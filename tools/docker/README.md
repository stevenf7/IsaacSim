# Docker Build Tools

This directory contains scripts for building Docker images of Isaac Sim. The build process involves two main steps: preparing the build environment and building the Docker image.

## Prerequisites

Before running these scripts, ensure you have the following installed on your host machine:

- **rsync** - Required for file synchronization during the preparation phase
- **python3** - Required for running the preparation scripts and installing dependencies
- **Docker** - Required for building the final image

### Installing Prerequisites

On Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y rsync python3 docker.io
```

On other systems, install these packages using your system's package manager.

## Build Process

### Step 1: Prepare the Build Environment

Use `prep_docker_build.sh` to prepare the Docker build context:

```bash
./tools/docker/prep_docker_build.sh [OPTIONS]
```

#### Options:
- `--build` - Run the full Isaac Sim build sequence before preparing Docker files:
  - Executes `build.sh -r`
<!-- AUTOREMOVE: BEGIN -->
  - Executes `repo.sh examples_list`
  - Executes `tools/build_docs.sh`
<!-- AUTOREMOVE: END -->
- `--x86_64` - Build x86_64 container (default)
- `--aarch64` - Build aarch64 container
- `--skip-dedupe` - Skip the file deduplication process (faster but larger image)
- `--help, -h` - Show help message

#### What this script does:
1. **Build Verification**: Checks that `_build/$CONTAINER_PLATFORM/release` exists (required for Docker build)
2. **Dependency Installation**: Installs Python requirements from `tools/docker/requirements.txt`
3. **File Preparation**: Generates and runs an rsync script to copy necessary files to `_container_temp`
4. **Data Copying**: Copies additional data from `tools/docker/data` and `tools/docker/oss`
5. **Deduplication**: Finds duplicate files and replaces them with symlinks to reduce image size
6. **Symlink Cleanup**: Fixes any chained symlinks that may have been created

### Step 2: Build the Docker Image

Use `build_docker.sh` to build the actual Docker image:

```bash
./tools/docker/build_docker.sh [OPTIONS]
```

#### Options:
- `--tag TAG` - Specify the Docker image tag (default: `isaac-sim-docker:latest`)
- `--x86_64` - Specify the Platform tag (default: x86_64)
- `--aarch64` - Specify the Platform tag (default: x86_64)
- `--push` - Push docker image tag
- `-h, --help` - Show help message

## Example Usage

### Basic build:
```bash
# Prepare build environment (includes full build)
./tools/docker/prep_docker_build.sh --build

# Build Docker image with default tag
./tools/docker/build_docker.sh
```

### Custom tag:
```bash
# Prepare build environment
./tools/docker/prep_docker_build.sh --build

# Build with custom tag
./tools/docker/build_docker.sh --tag my-isaac-sim:v1.0
```

### Quick rebuild (skip deduplication):
```bash
# If you've already built once and want to rebuild quickly
./tools/docker/prep_docker_build.sh --skip-dedupe

# Build the image
./tools/docker/build_docker.sh
```

## Environment Variables for `docker run`

You can pass these environment variables when running the container (e.g. `docker run --rm -e VAR=value ...`) to control the entrypoint behavior. **ACCEPT_EULA** is required to run the container; the rest are optional. Optional flags are only added when the corresponding variable is set.

| Variable | Required? | Description |
|----------|-----------|-------------|
| **ACCEPT_EULA** | **Yes** | Accept the license agreement (required to run; set e.g. to `Y`). |
| **OMNI_SERVER** | No | Override the default asset root (passed as `--/persistent/isaac/asset_root/default`). |
| **ISAACSIM_HOST** | No | Public or private IP of the host running Isaac Sim (for livestream; passed as livestream `publicIp`). Default: `127.0.0.1`. |
| **ISAACSIM_SIGNAL_PORT** | No | Signal port for WebRTC streaming. Default: `49100`. |
| **ISAACSIM_STREAM_PORT** | No | Streaming port for WebRTC. Default: `47998`. |

### Minimal run:

```bash
docker run --rm -it --gpus all --network=host \
  -e ACCEPT_EULA=Y \
  isaac-sim-docker:latest
```

Alternatively, use the provided helper script which drops into a bash shell inside the container:

```bash
./tools/docker/run_docker.sh
```

### Run with volume mounts:

```bash
# Create cache/log mounts (optional; use uid 1234 to match container user)
mkdir -p ~/docker/isaac-sim/cache/main/ov ~/docker/isaac-sim/cache/main/warp
mkdir -p ~/docker/isaac-sim/cache/computecache
mkdir -p ~/docker/isaac-sim/config ~/docker/isaac-sim/data/documents ~/docker/isaac-sim/data/Kit
mkdir -p ~/docker/isaac-sim/logs ~/docker/isaac-sim/pkg
sudo chown -R 1234:1234 ~/docker/isaac-sim

docker run --name isaac-sim --rm -it --gpus all --network=host \
  -e ACCEPT_EULA=Y \
  -e ISAACSIM_HOST=<host-ip> \
  -e ISAACSIM_SIGNAL_PORT=<signal-port> \
  -e ISAACSIM_STREAM_PORT=<stream-port> \
  -v ~/docker/isaac-sim/cache/main:/isaac-sim/.cache:rw \
  -v ~/docker/isaac-sim/cache/computecache:/isaac-sim/.nv/ComputeCache:rw \
  -v ~/docker/isaac-sim/logs:/isaac-sim/.nvidia-omniverse/logs:rw \
  -v ~/docker/isaac-sim/config:/isaac-sim/.nvidia-omniverse/config:rw \
  -v ~/docker/isaac-sim/data:/isaac-sim/.local/share/ov/data:rw \
  -v ~/docker/isaac-sim/pkg:/isaac-sim/.local/share/ov/pkg:rw \
  -u 1234:1234 \
  isaac-sim-docker:latest
```
**`--network=host` is required for WebRTC livestreaming.** The NVIDIA streaming SDK binds its UDP media socket to the `ISAACSIM_HOST` address, which must be a real network interface inside the container. Docker bridge networking (`-p` port publishing) does not satisfy this requirement because the host IP is not available inside the container's network namespace.

Replace `<host-ip>` with the host's LAN/public IP (e.g. `192.168.1.100`), `<signal-port>` with the desired signaling port (default `49100`), and `<stream-port>` with the desired streaming port (default `47998`). With `--network=host`, no `-p` flags are needed -- the container shares the host's network directly. Connect via `http://<host-ip>:8211` in your browser.

Open the ports listed below (e.g. UFW) if the host firewall is active.

### Why not Docker bridge networking (`-p`)?

The NVIDIA streaming SDK binds its UDP media socket to the IP specified by `ISAACSIM_HOST`. With Docker bridge networking, this IP does not exist inside the container (the container only has a `172.17.x.x` address), so the UDP bind fails and no media stream is established. Signaling (TCP 49100) and the web page (TCP 8211) may load, but the actual video stream will not connect. **Use `--network=host` for livestreaming.**

## Ports for streaming

When using `--network=host`, the container shares the host's network. If the host firewall is active (e.g. UFW), allow these ports:

| Port      | Protocol | Purpose |
|-----------|----------|---------|
| **8211**  | TCP      | HTTP transport server (streaming web app) |
| **49100** | TCP      | WebRTC signal (signaling) |
| **47998** | UDP      | WebRTC stream (media) |

Minimal UFW rules:

```bash
sudo ufw allow 8211/tcp  comment 'Isaac Sim HTTP transport'
sudo ufw allow 49100/tcp comment 'Isaac Sim WebRTC signal'
sudo ufw allow 47998/udp comment 'Isaac Sim WebRTC stream'
sudo ufw reload
```

If you override ports via `ISAACSIM_SIGNAL_PORT` or `ISAACSIM_STREAM_PORT`, open those instead.

## Important Notes

- **Build Requirements**: The `_build/$CONTAINER_PLATFORM/release` directory must exist before running the Docker preparation. Use `--build` option if you haven't built Isaac Sim yet.
- **Deduplication**: The deduplication process can significantly reduce Docker image size by replacing duplicate files with symlinks, but it takes time. Use `--skip-dedupe` for faster rebuilds during development.
- **File Paths**: The deduplication process skips files with spaces in their paths for reliability.
- **Build Context**: The final Docker build uses `_container_temp` as the build context and `tools/docker/Dockerfile` as the Dockerfile.
- **Platform**: Add the `--aarch64` flag to build for arm64 platform. It is recommended to use this flag when on an arm64 host.

## Troubleshooting

- **Cannot connect to livestream**: (1) Ensure you are using `--network=host` (required for WebRTC streaming). (2) Set `ISAACSIM_HOST` to the IP address the client uses to reach the host (e.g. LAN IP). (3) Allow ports 8211/tcp, 49100/tcp, and 47998/udp in the host firewall (e.g. UFW).
- **Error: "_build/$CONTAINER_PLATFORM/release does not exist"**: Run the script with `--build` option to build Isaac Sim first.
- **rsync not found**: Install rsync using your system's package manager.
- **Python requirements installation fails**: Ensure python3 and pip are properly installed.
- **Docker build fails**: Check that Docker daemon is running and you have sufficient disk space.
