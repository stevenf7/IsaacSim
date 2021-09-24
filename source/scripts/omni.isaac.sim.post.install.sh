#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
${SCRIPT_DIR}/omni.isaac.sim.warmup.sh
# install default python packages 
${SCRIPT_DIR}/python.sh -m pip install -r ${SCRIPT_DIR}/requirements.txt