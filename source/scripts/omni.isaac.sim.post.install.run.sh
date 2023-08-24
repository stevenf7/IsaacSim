#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})

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

# Install default Python packages
# Run command below to skip pip install step
#  echo "export ISAACSIM_SKIP_PIPINSTALL=Y" >> ~/.profile
if [[ -z "${ISAACSIM_SKIP_PIPINSTALL}" ]]; then
    echo Installing Python packages... Please wait...
    ${SCRIPT_DIR}/python.sh -m pip install -r ${SCRIPT_DIR}/requirements.txt &>>${SCRIPT_DIR}/omni.isaac.sim.post.install.log
    echo Python packages installed. &>>${SCRIPT_DIR}/omni.isaac.sim.post.install.log
fi

# Warm up cache
# Run command below to skip warm up
#  echo "export ISAACSIM_SKIP_WARMUP=Y" >> ~/.profile
if [[ -z "${ISAACSIM_SKIP_WARMUP}" ]]; then
    echo Warming up cache for main app...
    echo Close this window to skip.
    ${SCRIPT_DIR}/omni.isaac.sim.warmup.sh &>> ${SCRIPT_DIR}/omni.isaac.sim.post.install.log
fi

echo Isaac Sim Post-Installation Script completed! |& tee -a ${SCRIPT_DIR}/omni.isaac.sim.post.install.log
