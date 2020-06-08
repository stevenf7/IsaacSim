#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export ISAAC_PATH=$SCRIPT_DIR/../../../../../../../
export KIT_PATH=$SCRIPT_DIR/../../../../../../../../../target-deps/kit_sdk_release/_build/linux-x86_64/release/
export CARB_APP_PATH=$KIT_PATH
. ${ISAAC_PATH}/setup_python_env.sh
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$KIT_PATH/libs/mdl/