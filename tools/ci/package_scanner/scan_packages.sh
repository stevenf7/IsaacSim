#!/bin/bash
#
# Scan Isaac Sim release packages for internal URLs.
#
# Usage:
#   # Use version from VERSION file, download + unzip + scan
#   ./tools/ci/package_scanner/scan_packages.sh
#
#   # Specify version explicitly
#   ./tools/ci/package_scanner/scan_packages.sh 6.0.0-rc.19
#
#   # Skip download (reuse existing zips)
#   ./tools/ci/package_scanner/scan_packages.sh --skip-download
#   ./tools/ci/package_scanner/scan_packages.sh 6.0.0-rc.19 --skip-download
#
#   # Skip both download and unzip
#   ./tools/ci/package_scanner/scan_packages.sh --skip-download --skip-unzip
#
#   # Use a different packages directory
#   PACKAGES_DIR=_packages ./tools/ci/package_scanner/scan_packages.sh --skip-download --skip-unzip
#
#   # Filter to only linux release
#   ./tools/ci/package_scanner/scan_packages.sh --filter linux --filter release
#
set -eu

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

PACKAGES_DIR="${PACKAGES_DIR:-$REPO_ROOT/_build/packages}"

if [ $# -gt 0 ] && [[ "$1" != --* ]]; then
    VERSION="$1"
    shift
else
    VERSION="$(head -1 "$REPO_ROOT/VERSION")"
fi

echo "Scanning packages for version: $VERSION"
echo "Packages directory: $PACKAGES_DIR"

python3 "$SCRIPT_DIR/scan_packages.py" \
    --version "$VERSION" \
    --packages-dir "$PACKAGES_DIR" \
    --exclude-dir kit \
    --exclude-dir extscache \
    --exclude-dir tests \
    --exclude-dir docs \
    --exclude-dir extsInternal \
    "$@"
