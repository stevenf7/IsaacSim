# Docker Build Tools

This directory contains scripts for building Docker images of Isaac Sim. The build process involves two main steps: preparing the build environment and building the Docker image.

## Contents

- [Prerequisites](#prerequisites)
- [Build Process](#build-process)
- [Example Usage](#example-usage)
- [Environment Variables for `docker run`](#environment-variables-for-docker-run)
- [Ports for streaming](#ports-for-streaming)
- [Docker Compose (Isaac Sim + Web Viewer)](#docker-compose-isaac-sim--web-viewer)
  - [Quick start](#quick-start)
  - [Using a prebuilt Isaac Sim image](#using-a-prebuilt-isaac-sim-image)
  - [Checking status and endpoints](#checking-status-and-endpoints)
  - [Rebuilding the web viewer](#rebuilding-the-web-viewer)
  - [Multiple instances with dedicated GPUs](#multiple-instances-with-dedicated-gpus)
- [Important Notes](#important-notes)
- [Keyboard Shortcuts (Web Viewer)](#keyboard-shortcuts-web-viewer)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before running these scripts, ensure you have the following installed on your host machine:

- **rsync** - Required for file synchronization during the preparation phase
- **python3** - Required for running the preparation scripts and installing dependencies
- **Docker** - Required for building the final image
- **NVIDIA Container Toolkit** - Required for GPU access inside the container when running the image

See also: [Container Setup](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/install_container.html#container-setup) in the Isaac Sim documentation.

### Installing Prerequisites

On Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y rsync python3 docker.io
```

**NVIDIA Container Toolkit** (required for running the built image with GPU support):

```bash
# Configure the repository
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list \
  && sudo apt-get update

# Install and configure
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Verify (optional)
docker run --rm --runtime=nvidia --gpus all ubuntu nvidia-smi
```

On other systems, install these packages using your system's package manager. For full details and alternatives, see [Container Setup](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/install_container.html#container-setup).

## Build Process

### Step 1: Prepare the Build Environment

Use `prep_docker_build.sh` to prepare the Docker build context:

```bash
./tools/docker/prep_docker_build.sh [OPTIONS]
```

#### Options:

- `--build` - Run the full Isaac Sim build sequence before preparing Docker files:
  - Executes `build.sh -r`
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


| Variable                 | Required? | Description                                                                                                                 |
| ------------------------ | --------- | --------------------------------------------------------------------------------------------------------------------------- |
| **ACCEPT_EULA**          | **Yes**   | Accept the license agreement (required to run; set e.g. to `Y`).                                                            |
| **OMNI_SERVER**          | No        | Override the default asset root (passed as `--/persistent/isaac/asset_root/default`).                                       |
| **ISAACSIM_HOST**        | No        | Public or private IP of the host running Isaac Sim (for livestream; passed as livestream `publicIp`). Default: `127.0.0.1`. |
| **ISAACSIM_SIGNAL_PORT** | No        | Signal port for WebRTC streaming. Default: `49100`.                                                                         |
| **ISAACSIM_STREAM_PORT** | No        | Streaming port for WebRTC. Default: `47998`.                                                                                |


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
mkdir -p ~/docker/isaac-sim/{cache/main,cache/computecache,config,data,logs,pkg}
sudo chown -R 1234:1234 ~/docker

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

Replace `<host-ip>` with the host's LAN/public IP (e.g. `192.168.1.100`), `<signal-port>` with the desired signaling port (default `49100`), and `<stream-port>` with the desired streaming port (default `47998`). With `--network=host`, no `-p` flags are needed -- the container shares the host's network directly.

Open the ports listed below (e.g. UFW) if the host firewall is active.

### Why not Docker bridge networking (`-p`)?

The NVIDIA streaming SDK binds its UDP media socket to the IP specified by `ISAACSIM_HOST`. With Docker bridge networking, this IP does not exist inside the container (the container only has a `172.17.x.x` address), so the UDP bind fails and no media stream is established. Signaling (TCP 49100) may connect, but the actual video stream will not. **Use `--network=host` for livestreaming.**

## Ports for streaming

When using `--network=host`, the container shares the host's network. If the host firewall is active (e.g. UFW), allow these ports:


| Port      | Protocol | Purpose                          |
| --------- | -------- | -------------------------------- |
| **8210**  | TCP      | Web viewer (Docker Compose only) |
| **49100** | TCP      | WebRTC signal (signaling)        |
| **47998** | UDP      | WebRTC stream (media)            |


Minimal UFW rules:

```bash
sudo ufw allow 8210/tcp  comment 'Web viewer'
sudo ufw allow 49100/tcp comment 'Isaac Sim WebRTC signal'
sudo ufw allow 47998/udp comment 'Isaac Sim WebRTC stream'
sudo ufw reload
```

If you override ports via `ISAACSIM_SIGNAL_PORT`, `ISAACSIM_STREAM_PORT` or `WEB_VIEWER_PORT`, open those instead.

## Docker Compose (Isaac Sim + Web Viewer)

A `docker-compose.yml` is provided that launches both Isaac Sim (headless streaming) and a WebRTC web-viewer container side by side. The web viewer is built from `@nvidia/create-ov-web-rtc-app` in local streaming mode and connects the browser directly to the Isaac Sim WebRTC endpoints.

> **Security notice:** Isaac Sim and the web viewer are designed for use on private/trusted networks. They do not include authentication or encryption. If you need to expose them over the Internet, add a reverse proxy with HTTPS/TLS and authentication (e.g. nginx with SSL certificates and basic auth). Users are responsible for securing any public-facing deployments.

### Quick start

```bash
# Create cache/log mounts (use uid 1234 to match container user)
mkdir -p ~/docker/isaac-sim/{cache/main,cache/computecache,config,data,logs,pkg}
sudo chown -R 1234:1234 ~/docker

# 1. Build the Isaac Sim image (existing workflow)
./tools/docker/prep_docker_build.sh --build --x86_64
./tools/docker/build_docker.sh --x86_64

# 2. Launch both services (logs stream to the terminal; Ctrl+C stops everything)
docker compose -p isim -f tools/docker/docker-compose.yml up

# Or, launch in detached mode (runs in the background)
docker compose -p isim -f tools/docker/docker-compose.yml up -d
```

> **Note:** On DGX Spark, use `--aarch64` instead of `--x86_64` in the build commands above.

Running without `-d` (foreground) streams combined logs from both containers to your terminal, which is useful for debugging. Press `Ctrl+C` to stop all services. Running with `-d` (detached) starts everything in the background.

On first run, Docker Compose will build the `web-viewer` image automatically. The web viewer waits for the Isaac Sim healthcheck (`AppReady` in logs) before starting.

### Using a prebuilt Isaac Sim image

By default the compose file uses the locally built `isaac-sim-docker:latest` image. To use a prebuilt NGC image instead, set `ISAAC_SIM_IMAGE`:

```bash
ISAAC_SIM_IMAGE=nvcr.io/nvidia/isaac-sim:6.0.0 docker compose -p isim -f tools/docker/docker-compose.yml up -d
```

This skips the local build steps (`prep_docker_build.sh` and `build_docker.sh`).

### Checking status and endpoints

```bash
docker compose -p isim logs              # combined logs from both containers
docker compose -p isim logs web-viewer   # web viewer only (shows the URL)
docker compose -p isim logs isaac-sim    # Isaac Sim only (look for "app ready")
docker compose -p isim logs -f           # follow live logs (Ctrl+C to stop)
```

### Environment variables

Override any variable via the shell or a `.env` file next to `docker-compose.yml`:


| Variable                 | Default     | Description                                          |
| ------------------------ | ----------- | ---------------------------------------------------- |
| **ISAACSIM_HOST**        | `127.0.0.1` | Host IP for WebRTC streaming (used by both services) |
| **ISAACSIM_SIGNAL_PORT** | `49100`     | WebRTC signaling port                                |
| **ISAACSIM_STREAM_PORT** | `47998`     | WebRTC media port                                    |


### Rebuilding the web viewer

The web viewer bakes `ISAACSIM_HOST`, `ISAACSIM_SIGNAL_PORT`, and `ISAACSIM_STREAM_PORT` into the JavaScript bundle at build time. If you change any of these values, add `--build` to rebuild the image:

```bash
docker compose -p isim -f tools/docker/docker-compose.yml up --build -d
```

### Stopping

```bash
docker compose -p isim -f tools/docker/docker-compose.yml down
```

### Multiple instances with dedicated GPUs

You can run multiple Isaac Sim instances on the same host by using Docker Compose project names (`-p`) to namespace each deployment. Each instance needs unique ports and its own data directory. Use `GPU_DEVICE` to pin each instance to a dedicated GPU.

```bash
# Prepare separate data directories (one per instance, owned by uid 1234)
mkdir -p ~/docker/isaac-sim-1/{cache/main,cache/computecache,config,data,logs,pkg}
mkdir -p ~/docker/isaac-sim-2/{cache/main,cache/computecache,config,data,logs,pkg}
sudo chown -R 1234:1234 ~/docker/isaac-sim-1 ~/docker/isaac-sim-2

# Instance 1 — GPU 0, default ports, web viewer on 8210
GPU_DEVICE=0 \
ISAACSIM_SIGNAL_PORT=49100 \
ISAACSIM_STREAM_PORT=47998 \
WEB_VIEWER_PORT=8210 \
ISAAC_SIM_DATA=~/docker/isaac-sim-1 \
  docker compose -p isim1 -f tools/docker/docker-compose.yml up --build -d

# Instance 2 — GPU 1, custom ports, web viewer on 8211
GPU_DEVICE=1 \
ISAACSIM_SIGNAL_PORT=49200 \
ISAACSIM_STREAM_PORT=48100 \
WEB_VIEWER_PORT=8211 \
ISAAC_SIM_DATA=~/docker/isaac-sim-2 \
  docker compose -p isim2 -f tools/docker/docker-compose.yml up --build -d
```

Check status and endpoints for each instance:

```bash
docker compose -p isim1 logs
docker compose -p isim2 logs
```

Each instance sees only its assigned GPU. Verify with:

```bash
docker exec isim1-isaac-sim-1 nvidia-smi -L   # GPU 0 only
docker exec isim2-isaac-sim-1 nvidia-smi -L   # GPU 1 only
```

To stop a specific instance:

```bash
docker compose -p isim1 -f tools/docker/docker-compose.yml down
docker compose -p isim2 -f tools/docker/docker-compose.yml down
```


| Variable            | Description                                                   |
| ------------------- | ------------------------------------------------------------- |
| **GPU_DEVICE**      | GPU index to pin the Isaac Sim container to (default: `all`)  |
| **WEB_VIEWER_PORT** | Host port for the web viewer (default: `8210`)                |
| **ISAAC_SIM_DATA**  | Host path for persistent data (default: `~/docker/isaac-sim`) |


## Important Notes

- **Build Requirements**: The `_build/$CONTAINER_PLATFORM/release` directory must exist before running the Docker preparation. Use `--build` option if you haven't built Isaac Sim yet.
- **Deduplication**: The deduplication process can significantly reduce Docker image size by replacing duplicate files with symlinks, but it takes time. Use `--skip-dedupe` for faster rebuilds during development.
- **File Paths**: The deduplication process skips files with spaces in their paths for reliability.
- **Build Context**: The final Docker build uses `_container_temp` as the build context and `tools/docker/Dockerfile` as the Dockerfile.
- **Platform**: Add the `--aarch64` flag to build for arm64 platform. It is recommended to use this flag when on an arm64 host.

## Keyboard Shortcuts (Web Viewer)


| Action                         | Windows / Linux         | Mac                              |
| ------------------------------ | ----------------------- | -------------------------------- |
| Copy / paste                   | **Ctrl+C** / **Ctrl+V** | **Ctrl+C** / **Ctrl+V (in app)** |
| Refresh the browser page       | **F5** or **Ctrl+R**    | **Fn+F5** or **Cmd+R**           |
| Maximize viewport in Isaac Sim | **F7**                  | **Fn+F7**                        |
| Toggle browser fullscreen      | **F11**                 | **Shift+Fn+F11**                 |
| Open DevTools                  | **F12**                 | **Fn+F12** or **Cmd+Option+I**   |


## Troubleshooting

- **Cannot connect to livestream**: (1) Ensure you are using `--network=host` (required for WebRTC streaming). (2) Set `ISAACSIM_HOST` to the IP address the client uses to reach the host (e.g. LAN IP). (3) Allow ports 8210/tcp, 49100/tcp, and 47998/udp in the host firewall (e.g. UFW).
- **Clipboard (Ctrl+C/V) not working in the web viewer**: The browser Clipboard API requires a secure context. When accessing the web viewer over HTTP from a non-localhost address, clipboard forwarding to Isaac Sim is blocked. To enable it, open `chrome://flags/#unsafely-treat-insecure-origin-as-secure` in Chrome, add your web viewer URL (e.g. `http://192.168.1.100:8210`), and relaunch the browser.
- **Error: "_build/$CONTAINER_PLATFORM/release does not exist"**: Run the script with `--build` option to build Isaac Sim first.
- **rsync not found**: Install rsync using your system's package manager.
- **Python requirements installation fails**: Ensure python3 and pip are properly installed.
- **Docker build fails**: Check that Docker daemon is running and you have sufficient disk space.

