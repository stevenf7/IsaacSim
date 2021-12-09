#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})

# Add symlink to Isaac Examples
pushd ${SCRIPT_DIR}
ln -s exts/omni.isaac.examples/omni/isaac/examples extension_examples
popd
# Warm up shader cache
${SCRIPT_DIR}/omni.isaac.sim.warmup.sh
# Install default Python packages 
${SCRIPT_DIR}/python.sh -m pip install -r ${SCRIPT_DIR}/requirements.txt