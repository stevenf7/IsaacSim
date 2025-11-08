#!/bin/bash

set -e          # exit on error
set -u          # exit on using unset variable
set -o pipefail # exit on command fail in pipe

# Default configuration
config="release"
platform="linux-x86_64"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--config)
            config="$2"
            shift 2
            ;;
        -p|--platform)
            platform="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [-c|--config release|debug] [-p|--platform windows-x86_64|linux-x86_64|linux-aarch64]"
            exit 1
            ;;
    esac
done

# Validate configuration
if [[ "$config" != "release" && "$config" != "debug" ]]; then
    echo "Error: Configuration must be 'release' or 'debug'"
    exit 1
fi

# Validate platform
if [[ "$platform" != "windows-x86_64" && "$platform" != "linux-x86_64" && "$platform" != "linux-aarch64" ]]; then
    echo "Error: Platform must be 'windows-x86_64', 'linux-x86_64', or 'linux-aarch64'"
    exit 1
fi

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
repo_root=$(realpath "${script_dir}"/..)

# Find the omni.kit.pip_archive directory in extscache (handle symlinks)
pip_archive_path=$(find "${repo_root}/_build/${platform}/${config}/extscache" -maxdepth 1 -name "omni.kit.pip_archive-*" 2>/dev/null | head -n 1)

# Build PYTHONPATH
pythonpath="${repo_root}/_build/target-deps/usd/${config}/lib/python:${repo_root}/_build/target-deps/pip_cloud_prebundle:${repo_root}/_build/${platform}/${config}/kit/exts/omni.kit.pip_archive/pip_prebundle"
if [[ -n "$pip_archive_path" ]]; then
    pythonpath="${pythonpath}:${pip_archive_path}/pip_prebundle"
fi

export PYTHONPATH="${pythonpath}"
exec "${repo_root}"/_build/target-deps/python/python "${repo_root}"/_build/target-deps/usd/${config}/bin/usdGenSchema "${repo_root}/source/extensions/isaacsim.robot.schema/robot_schema/RobotSchema.usda" "${repo_root}/source/extensions/isaacsim.robot.schema/robot_schema"
