#!/bin/bash
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#
# Script to update and build specific components of the project
#

# Exit immediately if a command exits with a non-zero status
set -e
# Disable filename expansion (globbing)
set -f

########################################################################################################################
# Version helpers
########################################################################################################################

# Extract MAJOR.MINOR.PATCH from a packman XML for a given package name.
get_package_version() {
    local xml_file="$1"
    local package_name="$2"
    python3 -c "
import re, sys
with open(sys.argv[1]) as f:
    content = f.read()
m = re.search(r'name=\"' + re.escape(sys.argv[2]) + r'\"[^>]*version=\"(\d+\.\d+\.\d+)', content)
if m:
    print(m.group(1))
else:
    print(f'ERROR: Could not extract version for {sys.argv[2]} from {sys.argv[1]}', file=sys.stderr)
    sys.exit(1)
" "$xml_file" "$package_name"
}

# Replace the MAJOR.MINOR.PATCH prefix in every version= attribute for a given
# package inside a packman XML.  The build-metadata suffix is preserved.
set_package_version() {
    local xml_file="$1"
    local package_name="$2"
    local new_version="$3"
    python3 -c "
import re, sys
xml_file, pkg, ver = sys.argv[1], sys.argv[2], sys.argv[3]
with open(xml_file) as f:
    content = f.read()
pattern = r'(name=\"' + re.escape(pkg) + r'\"[^>]*version=\")\d+\.\d+\.\d+'
new_content, n = re.subn(pattern, r'\g<1>' + ver, content)
if n == 0:
    print(f'ERROR: Could not find {pkg} in {xml_file}', file=sys.stderr)
    sys.exit(1)
with open(xml_file, 'w') as f:
    f.write(new_content)
print(f'Set {pkg} version prefix to {ver} in {xml_file}')
" "$xml_file" "$package_name" "$new_version"
}

# Exit 0 when $1 > $2  (i.e. "would be a downgrade"),  exit 1 otherwise.
is_downgrade() {
    python3 -c "
import sys
v1 = tuple(int(x) for x in sys.argv[1].split('.'))
v2 = tuple(int(x) for x in sys.argv[2].split('.'))
sys.exit(0 if v1 > v2 else 1)
" "$1" "$2"
}

########################################################################################################################
# Help
########################################################################################################################

print_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Modes:"
    echo "  -h, --help           Show this help message and exit"
    echo "  --kit                Update kit-kernel and related components"
    echo "  --physics            Update physics components"
    echo "  --exts               Update and clean extension cache"
    echo "  --all                Run all updates (kit + physics + exts)"
    echo "  --clean              Clean extensions from extscache that exist in build tree (exclusive mode)"
    echo "  --repo-exts-only     Run ./build.sh -ur and keep only repo extension changes in extscache"
    echo ""
    echo "Version pinning:"
    echo "  --kit-version VER        Pin kit-kernel to MAJOR.MINOR.PATCH (default: latest patch)"
    echo "  --physics-version VER    Pin omni_physics to MAJOR.MINOR.PATCH (default: latest patch)"
    echo "  --force-physics          Allow physics downgrade (default: only upgrade)"
    echo "  --kit-sdk-repo PATH      Path to kit-sdk-public checkout (used with --exts)"
    echo ""
    echo "Examples:"
    echo "  $0 --all                                       # Full update, latest patches"
    echo "  $0 --all --kit-version 110.2.0                 # Full update, kit pinned to 110.2.0"
    echo "  $0 --kit --kit-version 110.2.0                 # Update only kit to 110.2.0"
    echo "  $0 --physics --physics-version 110.0.8         # Update physics to 110.0.8"
    echo "  $0 --physics --physics-version 110.0.6 --force-physics  # Force physics downgrade"
    echo "  $0 --exts                                      # Update extensions using local kit-sdk-public locks"
    echo "  $0 --exts --kit-sdk-repo /path/to/kit-sdk-public  # Use a specific kit-sdk-public checkout"
    echo "  $0 --clean                                     # Clean extensions only"
    echo "  $0 --repo-exts-only                            # Keep only repo extension cache changes after build"
    echo ""
    exit 0
}

########################################################################################################################
# Update functions
########################################################################################################################

# Step 1: Update kit-kernel and Isaac Sim deps (GMO, sensor-checker)
update_kit() {
    echo "=========================================="
    echo "Updating kit components..."
    echo "=========================================="
    pushd ../

    if [ -n "$KIT_VERSION" ]; then
        local old_version
        old_version=$(get_package_version deps/kit-sdk.packman.xml kit-kernel)
        echo "Current kit-kernel version: $old_version"
        echo "Pinning kit-kernel to: $KIT_VERSION"
        set_package_version deps/kit-sdk.packman.xml kit-kernel "$KIT_VERSION"
    fi

    ./repo.sh update kit-kernel --patch
    ./repo.sh validate_python_packages --update-omniverse-kit
    # Update GMO package and other dep versions to match kit
    python3 tools/isaac/update_isaac_sim_deps.py

    local new_version
    new_version=$(get_package_version deps/kit-sdk.packman.xml kit-kernel)
    echo "Kit-kernel version after update: $new_version"

    popd
}

# Step 2: Update physics components
update_physics() {
    echo "=========================================="
    echo "Updating physics components..."
    echo "=========================================="
    pushd ../

    local old_version
    old_version=$(get_package_version deps/omni-physics.packman.xml omni_physics)
    echo "Current omni_physics version: $old_version"

    if [ -n "$PHYSICS_VERSION" ]; then
        # Explicit version requested — check for downgrade
        if [ "$FORCE_PHYSICS" != true ]; then
            if is_downgrade "$old_version" "$PHYSICS_VERSION"; then
                echo "WARNING: Requested physics version $PHYSICS_VERSION is older than current $old_version."
                echo "  Use --force-physics to allow downgrade. Skipping physics update."
                popd
                return 0
            fi
        fi
        echo "Pinning omni_physics to: $PHYSICS_VERSION"
        set_package_version deps/omni-physics.packman.xml omni_physics "$PHYSICS_VERSION"
    fi

    ./repo.sh update omni_physics --include-pre-release --patch

    local new_version
    new_version=$(get_package_version deps/omni-physics.packman.xml omni_physics)
    echo "omni_physics version after update: $new_version"

    # Guard against accidental downgrade from repo.sh update
    if [ "$FORCE_PHYSICS" != true ]; then
        if is_downgrade "$old_version" "$new_version"; then
            echo "WARNING: repo.sh update returned a lower physics version ($new_version < $old_version)."
            echo "  Reverting to $old_version. Use --force-physics to allow downgrade."
            set_package_version deps/omni-physics.packman.xml omni_physics "$old_version"
            ./repo.sh update omni_physics --include-pre-release --patch
        fi
    fi

    popd
}

# Step 3: Update extension cache (Kit SDK lock sync + physics correction + build + clean)
update_extensions() {
    local kit_sdk_repo="$1"
    echo "=========================================="
    echo "Updating extension cache..."
    echo "=========================================="
    pushd ../

    echo "Using kit-sdk-public repo: $kit_sdk_repo"
    local cmd=(
        python3 tools/isaac/clean_extscache.py
        --update-locks
        --update-physics
        --match-kit-sdk
        --kit-sdk-repo "$kit_sdk_repo"
        --build-dir "_build/$PLATFORM/release/exts"
        --deprecated-dir "_build/$PLATFORM/release/extsDeprecated"
        --apps-dir "_build/$PLATFORM/release/apps"
        --internal-dir "_build/$PLATFORM/release/extsInternal"
    )

    "${cmd[@]}"
    ./repo.sh build -r
    "${cmd[@]}"
    popd
}

# Clean extensions from extscache that exist in build tree
clean_extensions() {
    echo "Cleaning extensions from extscache..."
    pushd ../
    python3 tools/isaac/clean_extscache.py \
        --build-dir "_build/$PLATFORM/release/exts" \
        --deprecated-dir "_build/$PLATFORM/release/extsDeprecated" \
        --apps-dir "_build/$PLATFORM/release/apps" \
        --internal-dir "_build/$PLATFORM/release/extsInternal"
    popd
}

# Run update/release build and restore extscache changes that do not come from repo extensions
update_repo_extensions_only() {
    echo "Updating repo extensions in extscache only..."
    pushd ../

    local kit_file="source/apps/isaacsim.exp.extscache.kit"
    local baseline_kit
    baseline_kit=$(mktemp)
    cp "$kit_file" "$baseline_kit"

    ./build.sh -ur

    python3 tools/isaac/clean_extscache.py \
        --restore-non-local-from "$baseline_kit" \
        --kit-file "$kit_file" \
        --build-dir "_build/$PLATFORM/release/exts" \
        --deprecated-dir "_build/$PLATFORM/release/extsDeprecated" \
        --apps-dir "_build/$PLATFORM/release/apps" \
        --internal-dir "_build/$PLATFORM/release/extsInternal"

    rm -f "$baseline_kit"
    popd
}

########################################################################################################################
# Main
########################################################################################################################

# Get the directory where this script is located
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
cd "$SCRIPT_DIR"

# Detect architecture
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ]; then
    PLATFORM="linux-aarch64"
else
    PLATFORM="linux-x86_64"
fi
echo "Detected platform: $PLATFORM"

# Parse command line arguments
if [ $# -eq 0 ]; then
    print_help
fi

# Initialize flags
UPDATE_KIT=false
UPDATE_PHYSICS=false
UPDATE_EXTS=false
CLEAN_EXTS=false
REPO_EXTS_ONLY=false
KIT_VERSION=""
PHYSICS_VERSION=""
FORCE_PHYSICS=false
KIT_SDK_REPO="${KIT_SDK_REPO:-/home/hmazhar/repos/kit-sdk-public}"
KIT_SDK_REPO_ARG=false

# Process arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            print_help
            ;;
        --kit)
            UPDATE_KIT=true
            shift
            ;;
        --physics)
            UPDATE_PHYSICS=true
            shift
            ;;
        --exts)
            UPDATE_EXTS=true
            shift
            ;;
        --clean)
            CLEAN_EXTS=true
            shift
            ;;
        --repo-exts-only)
            REPO_EXTS_ONLY=true
            shift
            ;;
        --all)
            UPDATE_KIT=true
            UPDATE_PHYSICS=true
            UPDATE_EXTS=true
            shift
            ;;
        --kit-version)
            if [[ $# -gt 1 ]]; then
                KIT_VERSION="$2"
                shift 2
            else
                echo "Error: --kit-version requires a MAJOR.MINOR.PATCH value"
                exit 1
            fi
            ;;
        --kit-version=*)
            KIT_VERSION="${1#*=}"
            shift
            ;;
        --physics-version)
            if [[ $# -gt 1 ]]; then
                PHYSICS_VERSION="$2"
                shift 2
            else
                echo "Error: --physics-version requires a MAJOR.MINOR.PATCH value"
                exit 1
            fi
            ;;
        --physics-version=*)
            PHYSICS_VERSION="${1#*=}"
            shift
            ;;
        --force-physics)
            FORCE_PHYSICS=true
            shift
            ;;
        --kit-sdk-repo)
            if [[ $# -gt 1 ]]; then
                KIT_SDK_REPO="$2"
                KIT_SDK_REPO_ARG=true
                shift 2
            else
                echo "Error: --kit-sdk-repo requires a path"
                exit 1
            fi
            ;;
        --kit-sdk-repo=*)
            KIT_SDK_REPO="${1#*=}"
            KIT_SDK_REPO_ARG=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            print_help
            ;;
    esac
done

# Validate flag combinations
if [ "$CLEAN_EXTS" = true ]; then
    if [ "$UPDATE_KIT" = true ] || [ "$UPDATE_PHYSICS" = true ] || [ "$UPDATE_EXTS" = true ] || [ "$REPO_EXTS_ONLY" = true ]; then
        echo "Error: --clean cannot be combined with --kit, --physics, --exts, --repo-exts-only, or --all"
        print_help
    fi
fi

if [ "$REPO_EXTS_ONLY" = true ]; then
    if [ "$UPDATE_KIT" = true ] || [ "$UPDATE_PHYSICS" = true ] || [ "$UPDATE_EXTS" = true ] || [ "$CLEAN_EXTS" = true ]; then
        echo "Error: --repo-exts-only cannot be combined with --kit, --physics, --exts, --clean, or --all"
        print_help
    fi
fi

if [ -n "$KIT_VERSION" ] && [ "$UPDATE_KIT" != true ]; then
    echo "Error: --kit-version requires --kit or --all"
    exit 1
fi

if [ -n "$PHYSICS_VERSION" ] && [ "$UPDATE_PHYSICS" != true ]; then
    echo "Error: --physics-version requires --physics or --all"
    exit 1
fi

if [ "$FORCE_PHYSICS" = true ] && [ "$UPDATE_PHYSICS" != true ]; then
    echo "Error: --force-physics requires --physics or --all"
    exit 1
fi

if [ "$KIT_SDK_REPO_ARG" = true ] && [ "$UPDATE_EXTS" != true ]; then
    echo "Error: --kit-sdk-repo requires --exts or --all"
    exit 1
fi

# Run selected updates
if [ "$UPDATE_KIT" = true ]; then
    update_kit
fi

if [ "$UPDATE_PHYSICS" = true ]; then
    update_physics
fi

if [ "$UPDATE_EXTS" = true ]; then
    update_extensions "$KIT_SDK_REPO"
fi

if [ "$CLEAN_EXTS" = true ]; then
    clean_extensions
fi

if [ "$REPO_EXTS_ONLY" = true ]; then
    update_repo_extensions_only
fi

echo ""
echo "Update completed successfully!"
