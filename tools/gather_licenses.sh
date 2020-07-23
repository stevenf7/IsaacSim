#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})

pushd "$SCRIPT_DIR/.."

if [ -d PACKAGE-LICENSES ]
then
    rm PACKAGE-LICENSES/*.md || true
fi

cp $SCRIPT_DIR/internal-licenses/* $SCRIPT_DIR/../PACKAGE-LICENSES/

"tools/licensing.sh" gather -d "." -p "deps/isaac-sim.packman.xml" --platform "linux-x86_64" $LICENSING_OPTIONS $*

"tools/licensing.sh" gather -d "." -p "deps/kit-sdk.packman.xml" --platform "linux-x86_64" $LICENSING_OPTIONS $*

"tools/licensing.sh" gather -d "." -p "deps/rtx-plugins.packman.xml" --platform "linux-x86_64" $LICENSING_OPTIONS $*

"tools/licensing.sh" gather -d "." -p "deps/omni-physics.packman.xml" --platform "linux-x86_64" $LICENSING_OPTIONS $*

if [ ! -z "$TEAMCITY_VERSION" ]
then
    rm -f "PACKAGE-LICENSES/*readme*"
fi
