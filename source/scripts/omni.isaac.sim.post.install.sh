#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})

gnome-terminal -- "${SCRIPT_DIR}/omni.isaac.sim.post.install.run.sh"
