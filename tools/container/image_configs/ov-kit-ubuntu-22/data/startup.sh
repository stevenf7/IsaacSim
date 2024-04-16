#!/usr/bin/env bash
set -e
set -u

# Check for libGLX_nvidia.so.0 (needed for vulkan)
ldconfig -p | grep libGLX_nvidia.so.0 || NOTFOUND=1
if [[ -v NOTFOUND ]]; then
    cat << EOF > /dev/stderr

Fatal Error: Can't find libGLX_nvidia.so.0...

Ensure running with NVIDIA runtime. (--gpus all) or (--runtime nvidia)
If no GPU is required, please run startup_nogpu.sh as the entrypoint.

EOF
    exit 1
fi

echo 'Running: [...]kit in GPU mode, please run startup_nogpu.sh if no GPU is required' $@

exec "/opt/nvidia/omniverse/kit-sdk-launcher/kit" \
    "--/rtx/shaderDb/driverAppShaderCachePath=/opt/nvidia/omniverse/kit-sdk-launcher/_cache" \
    "--/renderer/shadercache/driverDiskCache/enabled=true" \
    "--no-window" \
    $@
