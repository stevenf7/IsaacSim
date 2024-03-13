#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})

if [[ ! -z "${ISAACSIM_SKIP_POSTINSTALL}" ]]; then
    echo ISAACSIM_SKIP_POSTINSTALL was set. Post-install skipped. |& tee -a ${SCRIPT_DIR}/omni.isaac.sim.post.install.log
else

    echo "Isaac Sim Post-Installation Script" |& tee ${SCRIPT_DIR}/omni.isaac.sim.post.install.log

    # Add symlink to Isaac Examples
    echo Creating extension_examples symlink...
    pushd ${SCRIPT_DIR}
    if [ ! -L extension_examples ] && [ ! -e extension_examples ]; then
        ln -s exts/omni.isaac.examples/omni/isaac/examples extension_examples &>>${SCRIPT_DIR}/omni.isaac.sim.post.install.log
        echo Symlink extension_examples created. &>>${SCRIPT_DIR}/omni.isaac.sim.post.install.log
    else
        echo Symlink or folder extension_examples exists. &>>${SCRIPT_DIR}/omni.isaac.sim.post.install.log
    fi
    popd

    # Install icon
    echo Installing Icon...
    ${SCRIPT_DIR}/python.sh ${SCRIPT_DIR}/data/icon/install_icon.py &>>${SCRIPT_DIR}/omni.isaac.sim.post.install.log

    # Warm up cache
    # Run command below to skip warm up
    #  echo "export ISAACSIM_SKIP_WARMUP=Y" >> ~/.profile
    if [[ -z "${ISAACSIM_SKIP_WARMUP}" ]]; then
        x-terminal-emulator -e "${SCRIPT_DIR}/omni.isaac.sim.post.install.run.sh"
    else
        echo ISAACSIM_SKIP_WARMUP was set. Warm up skipped. |& tee -a ${SCRIPT_DIR}/omni.isaac.sim.post.install.log
    fi

fi
