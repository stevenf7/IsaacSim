#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"
ROOT_DIR="$SCRIPT_DIR/../../../.."

if [ -z "$TEAMCITY_VERSION" ]
then
# Verify formatting
echo "##teamcity[progressMessage 'Verify formatting...']"
"$ROOT_DIR/format_code.sh" --verify
fi

# Full rebuild
echo "##teamcity[progressMessage 'Full rebuild...']"
"$ROOT_DIR/build.sh" -x

# Docs
echo "##teamcity[progressMessage 'Docs...']"
"$ROOT_DIR/tools/build_docs.sh" -c release

# Gathering licenses
echo "##teamcity[progressMessage 'Gathering licenses...']"
"$ROOT_DIR/tools/licensing.sh" gather \
    -p $ROOT_DIR/deps/isaac-sim.packman.xml \
    $ROOT_DIR/deps/kit-sdk.packman.xml \
    $ROOT_DIR/deps/rtx-plugins.packman.xml \
    $ROOT_DIR/deps/omni-physics.packman.xml \
    -d $ROOT_DIR/_build

# Validating licenses
#echo "##teamcity[progressMessage 'Validating licenses...']"
#"$ROOT_DIR/tools/licensing.sh" validate \
#    -p $ROOT_DIR/deps/isaac-sim.packman.xml \
#    $ROOT_DIR/deps/kit-sdk.packman.xml \
#    $ROOT_DIR/deps/rtx-plugins.packman.xml \
#    $ROOT_DIR/deps/omni-physics.packman.xml \
#    -d $ROOT_DIR/_build \
#    -b linux-x86_64/release

# Run python tests
#echo "##teamcity[progressMessage 'Python tests...']"
#"$SCRIPT_DIR/../../../test_runner.sh" --suite pythontests --config release

# Package
echo "##teamcity[progressMessage 'Packaging...']"
"$ROOT_DIR/tools/package.sh" -m test_runner
"$ROOT_DIR/tools/package.sh" -m docs
"$ROOT_DIR/tools/package.sh" -m isaac-sim -c debug
"$ROOT_DIR/tools/package.sh" -m isaac-sim -c release
"$ROOT_DIR/tools/package.sh" -m omni_domain_randomization -c debug
"$ROOT_DIR/tools/package.sh" -m omni_domain_randomization -c release

# publish artifacts to teamcity
echo "##teamcity[publishArtifacts '_build/packages']"


