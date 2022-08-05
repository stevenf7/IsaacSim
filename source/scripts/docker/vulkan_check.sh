#!/usr/bin/env bash
set -e
set -u

# Check for libGLX_nvidia.so.0 (needed for vulkan)
ldconfig -p | grep libGLX_nvidia.so.0 || NOTFOUND=1
if [[ -v NOTFOUND ]]; then
    cat << EOF > /dev/stderr

Fatal Error: Can't find libGLX_nvidia.so.0...

Ensure running with NVIDIA runtime. (--gpus all) or (--runtime nvidia)

EOF
    exit 1
fi

# Detect NVIDIA vulkan api version, and create ICD
mkdir -p /etc/vulkan/icd.d
LD_LIBRARY_PATH=/isaac-sim/kit/plugins/carb_gfx \
    /opt/nvidia/omniverse/vkapiversion/bin/vkapiversion \
    /etc/vulkan/icd.d/nvidia_icd.json
