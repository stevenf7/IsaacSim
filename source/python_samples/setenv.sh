#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

path=$SCRIPT_DIR
while [[ $path != / ]];
do
    
    if ! find "$path" -maxdepth 1 -mindepth 1 -iname "_build" -exec false {} +
    then
        break
    fi
    # Note: if you want to ignore symlinks, use "$(realpath -s "$path"/..)"
    path="$(readlink -f "$path"/..)"
    
done
build_path=$path/_build
export EXP_PATH=$SCRIPT_DIR/experiences
export ISAAC_PATH=$build_path/linux-x86_64/release
# TODO Not sure if this does anything
# export USDSHADE_OLD_MDL_SCHEMA_SUPPORT=1
# export USDIMAGING_ENABLE_NESTED_GPRIMS=1
# export USDIMAGING_DISABLE_CAMERA_ADAPTER=1
# export USDIMAGING_GPRIMADAPTER_PRIMVAR_INVALIDATION=1
# export USDIMAGING_ENABLE_SPARSE_LIGHT_UPDATES=1
# export USDIMAGING_ALLOW_UNREGISTERED_SHADER_IDS=1
. ${ISAAC_PATH}/setup_python_env.sh
