#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})

# Add symlink to Isaac Examples
pushd ${SCRIPT_DIR}
if [ ! -L extension_examples ] && [ ! -e extension_examples ]; then
    ln -s exts/omni.isaac.examples/omni/isaac/examples extension_examples
    echo "Symlink extension_examples created"
else
    echo "Symlink or folder extension_examples exists"
fi
popd

# Warm up shader cache
# Disabling warmup till crash is fixed - OM-45182
# echo "Warming up cache..."
# ${SCRIPT_DIR}/omni.isaac.sim.warmup.sh

# Install default Python packages 
echo "Installing Python packages..."
${SCRIPT_DIR}/python.sh -m pip install -r ${SCRIPT_DIR}/requirements.txt

echo "Isaac Sim post installation script completed!"
