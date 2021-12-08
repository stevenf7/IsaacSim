#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})

# Add symlink to Isaac Examples
ln -s exts/omni.isaac.examples/omni/isaac/examples extension_examples
# Warm up shader cache
${SCRIPT_DIR}/omni.isaac.sim.warmup.sh
# Install default Python packages 
${SCRIPT_DIR}/python.sh -m pip install -r ${SCRIPT_DIR}/requirements.txt