#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"

# Verify formatting
echo "##teamcity[progressMessage 'Verify formatting...']"
"$SCRIPT_DIR/../../../../format_code.sh" --verify

# Full rebuild
echo "##teamcity[progressMessage 'Full rebuild...']"
"$SCRIPT_DIR/../../../../build.sh" -x

# Docs
echo "##teamcity[progressMessage 'Docs...']"
"$SCRIPT_DIR/../../../build_docs.sh" -c release

# Run python tests
#echo "##teamcity[progressMessage 'Python tests...']"
#"$SCRIPT_DIR/../../../test_runner.sh" --suite pythontests --config release

# Package
echo "##teamcity[progressMessage 'Packaging...']"
"$SCRIPT_DIR/../../../package.sh" -m test_runner
"$SCRIPT_DIR/../../../package.sh" -m docs
"$SCRIPT_DIR/../../../package.sh" -m omniverse-kit -c release
"$SCRIPT_DIR/../../../package.sh" -m omni_isaac_sim -c release

# publish artifacts to teamcity
echo "##teamcity[publishArtifacts '_build/packages']"


