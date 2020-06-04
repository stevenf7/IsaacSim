#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"
ROOT_DIR="$SCRIPT_DIR/../../../.."

if [ -z "$TEAMCITY_VERSION" ]
then
# Verify formatting
echo "##teamcity[blockOpened name='Verify formatting...']"
"$ROOT_DIR/format_code.sh" --verify
echo "##teamcity[blockClosed name='Verify formatting...']"
fi

# Full rebuild
echo "##teamcity[blockOpened name='Full rebuild...']"
"$ROOT_DIR/build.sh" -c
"$ROOT_DIR/build.sh" -d
echo "##teamcity[blockClosed name='Full rebuild...']"

# Docs
echo "##teamcity[blockOpened name='Docs...']"
"$ROOT_DIR/tools/build_docs.sh" -c debug
echo "##teamcity[blockClosed name='Docs...']"

# Gathering licenses
# echo "##teamcity[blockOpened name='Gathering licenses...']"
# "$ROOT_DIR/tools/licensing.sh" gather \
#     -p $ROOT_DIR/deps/isaac-sim.packman.xml \
#     $ROOT_DIR/deps/kit-sdk.packman.xml \
#     $ROOT_DIR/deps/rtx-plugins.packman.xml \
#     $ROOT_DIR/deps/omni-physics.packman.xml \
#     -d $ROOT_DIR/_build
# echo "##teamcity[blockClosed name='Gathering licenses...']"

# Validating licenses
#echo "##teamcity[blockOpened name='Validating licenses...']"
#"$ROOT_DIR/tools/licensing.sh" validate \
#    -p $ROOT_DIR/deps/isaac-sim.packman.xml \
#    $ROOT_DIR/deps/kit-sdk.packman.xml \
#    $ROOT_DIR/deps/rtx-plugins.packman.xml \
#    $ROOT_DIR/deps/omni-physics.packman.xml \
#    -d $ROOT_DIR/_build \
#    -b linux-x86_64/release
#echo "##teamcity[blockClosed name='Validating licenses...']"

# Package
echo "##teamcity[blockOpened name='Build packages...']"
echo "##teamcity[progressMessage 'Packaging test_runner...']"
"$ROOT_DIR/tools/package.sh" -m test_runner -c debug
echo "##teamcity[progressMessage 'Packaging docs...']"
"$ROOT_DIR/tools/package.sh" -m docs -c debug
echo "##teamcity[progressMessage 'Packaging isaac-sim...']"
"$ROOT_DIR/tools/package.sh" -m isaac-sim -c debug
echo "##teamcity[progressMessage 'Packaging omniverse-kit-robotics...']"
"$ROOT_DIR/tools/package.sh" -m omniverse-kit-robotics -c debug
echo "##teamcity[progressMessage 'Packaging omni_domain_randomization...']"
"$ROOT_DIR/tools/package.sh" -m omni_domain_randomization -c debug
echo "##teamcity[blockClosed name='Build packages...']"

# publish artifacts to teamcity
echo "##teamcity[publishArtifacts '_build/packages']"

