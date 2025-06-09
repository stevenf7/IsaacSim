#!/bin/bash

# Get script directory
SCRIPT_DIR="$( cd "$(dirname "$0")" ; pwd -P )"

# Check if EULA has already been accepted (either in current dir or script dir)
if [ -f ".eula_accepted" ] || [ -f "${SCRIPT_DIR}/.eula_accepted" ]; then
    exit 0
fi

# EULA text placeholder - replace this with your actual EULA text
echo "=== END USER LICENSE AGREEMENT ==="
echo "Building or using the software requires additional components licenced under other terms. These additional components include dependencies such as the Omniverse Kit SDK, as well as 3D models and textures. "
echo ""
echo "License terms for these additional NVIDIA owned and licensed components  can be found here:"
echo ""
echo "https://www.nvidia.com/en-us/agreements/enterprise-software/isaac-sim-additional-software-and-materials-license/"
echo ""
echo "================================"
echo ""
echo "Do you accept the governing terms? (YES/NO):"

# Read user input
read response

# Check response
if [ "$response" = "YES" ]; then
    # Create the acceptance file in the script directory to persist it
    touch "${SCRIPT_DIR}/.eula_accepted"
    exit 0
else
    exit 1
fi