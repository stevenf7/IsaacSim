#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"
ROOT_DIR="$SCRIPT_DIR/../../../.."

if [ -z "$TEAMCITY_VERSION" ]
then
# Verify formatting
echo "##teamcity[progressStart 'Verify formatting...']"
"$ROOT_DIR/format_code.sh" --verify
echo "##teamcity[progressFinish 'Verify formatting...']"
fi

# Full rebuild
echo "##teamcity[progressStart 'Full rebuild...']"
"$ROOT_DIR/build.sh" -c
"$ROOT_DIR/build.sh" -r
echo "##teamcity[progressFinish 'Full rebuild...']"

# Docs
echo "##teamcity[progressStart 'Docs...']"
"$ROOT_DIR/tools/build_docs.sh" -c release
echo "##teamcity[progressFinish 'Docs...']"

# Gathering licenses
echo "##teamcity[progressStart 'Gathering licenses...']"
"$ROOT_DIR/tools/licensing.sh" gather \
    -p $ROOT_DIR/deps/isaac-sim.packman.xml \
    $ROOT_DIR/deps/kit-sdk.packman.xml \
    $ROOT_DIR/deps/rtx-plugins.packman.xml \
    $ROOT_DIR/deps/omni-physics.packman.xml \
    -d $ROOT_DIR/_build
echo "##teamcity[progressFinish 'Gathering licenses...']"

# Validating licenses
#echo "##teamcity[progressStart 'Validating licenses...']"
#"$ROOT_DIR/tools/licensing.sh" validate \
#    -p $ROOT_DIR/deps/isaac-sim.packman.xml \
#    $ROOT_DIR/deps/kit-sdk.packman.xml \
#    $ROOT_DIR/deps/rtx-plugins.packman.xml \
#    $ROOT_DIR/deps/omni-physics.packman.xml \
#    -d $ROOT_DIR/_build \
#    -b linux-x86_64/release
#echo "##teamcity[progressFinish 'Validating licenses...']"

# Package
echo "##teamcity[progressStart 'Packaging...']"
"$ROOT_DIR/tools/package.sh" -m test_runner -c release
"$ROOT_DIR/tools/package.sh" -m docs -c release
"$ROOT_DIR/tools/package.sh" -m isaac-sim -c release
"$ROOT_DIR/tools/package.sh" -m omniverse-kit-robotics -c release
"$ROOT_DIR/tools/package.sh" -m omni_domain_randomization -c release
echo "##teamcity[progressFinish 'Packaging...']"

# publish artifacts to teamcity
echo "##teamcity[publishArtifacts '_build/packages']"

