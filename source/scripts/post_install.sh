#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})

# Add symlink to Isaac Examples
echo Creating extension_examples symlink...
pushd ${SCRIPT_DIR}
if [ ! -L extension_examples ] && [ ! -e extension_examples ]; then
    ln -s exts/isaacsim.examples.interactive/isaacsim/examples/interactive extension_examples
    echo Symlink extension_examples created.
else
    echo Symlink or folder extension_examples exists.
fi
popd

# Install icon
echo Installing Icon...
${SCRIPT_DIR}/python.sh ${SCRIPT_DIR}/data/icon/install_icon.py

