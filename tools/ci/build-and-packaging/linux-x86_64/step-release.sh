#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"
pushd $SCRIPT_DIR/../../../..

if [ -z "$TEAMCITY_VERSION" ]
then
# Verify formatting
echo "##teamcity[blockOpened name='Verify formatting...']"
"./format_code.sh" --verify
echo "##teamcity[blockClosed name='Verify formatting...']"
fi

# Full rebuild
echo "##teamcity[blockOpened name='Full rebuild...']"
"./build.sh" -c
"./build.sh" -r
echo "##teamcity[blockClosed name='Full rebuild...']"

# Docs
if [ -z "$TEAMCITY_VERSION" ]
then
   echo "##teamcity[blockOpened name='Docs...']"
   "./tools/build_docs.sh" -c release
   echo "##teamcity[blockClosed name='Docs...']"
   echo "##teamcity[progressMessage 'Packaging docs...']"
   "./tools/package.sh" -m docs -c release
fi

# Gathering licenses
echo "##teamcity[blockOpened name='Gathering licenses...']"
"./tools/gather_licenses.sh" \
   || (echo "##teamcity[buildStatus text='Licensing gather failed.' status='FAILURE']" \
   && exit 1)
echo "##teamcity[blockClosed name='Gathering licenses...']"

# Validating licenses
echo "##teamcity[blockOpened name='Validating licenses...']"
"./tools/licensing.sh" validate \
   -p ./deps/isaac-sim.packman.xml \
   -d . \
   -b ./_build/linux-x86_64/release
echo "##teamcity[blockClosed name='Validating licenses...']"

# Package
echo "##teamcity[blockOpened name='Build packages...']"
echo "##teamcity[progressMessage 'Packaging test_runner...']"
"./tools/package.sh" -m test_runner -c release
echo "##teamcity[progressMessage 'Packaging isaac-sim...']"
"./tools/package.sh" -m isaac-sim -c release
echo "##teamcity[progressMessage 'Packaging omniverse-kit-robotics...']"
"./tools/package.sh" -m omniverse-kit-robotics -c release
echo "##teamcity[progressMessage 'Packaging omni_domain_randomization...']"
"./tools/package.sh" -m omni_domain_randomization -c release
echo "##teamcity[blockClosed name='Build packages...']"

# publish artifacts to teamcity
echo "##teamcity[publishArtifacts '_build/packages']"

