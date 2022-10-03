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
echo "Warming up cache for main app..."
${SCRIPT_DIR}/omni.isaac.sim.warmup.sh

# Warm up python shader cache
echo "Warming up cache for python app..."
set +e # Workaround post-install script failure
${SCRIPT_DIR}/python.sh ${SCRIPT_DIR}/standalone_examples/api/omni.isaac.kit/hello_world.py
set -e

# Install default Python packages 
echo "Installing Python packages..."
${SCRIPT_DIR}/python.sh -m pip install -r ${SCRIPT_DIR}/requirements.txt

echo "Isaac Sim post installation script completed!"
