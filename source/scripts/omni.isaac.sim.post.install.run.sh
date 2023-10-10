#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})

echo "Isaac Sim Post-Installation Script"

# Warm up cache
# Run command below to skip warm up
#  echo "export ISAACSIM_SKIP_WARMUP=Y" >> ~/.profile
if [[ -z "${ISAACSIM_SKIP_WARMUP}" ]]; then
    echo Warming up cache for main app...
    echo Close this window to skip.
    ${SCRIPT_DIR}/omni.isaac.sim.warmup.sh &>> ${SCRIPT_DIR}/omni.isaac.sim.post.install.log
fi

echo Isaac Sim Post-Installation Script completed! |& tee -a ${SCRIPT_DIR}/omni.isaac.sim.post.install.log
