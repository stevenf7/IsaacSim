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

# Function to print help message
print_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help         Show this help message and exit"
    echo "  --kit              Update kit-kernel and related components"
    echo "  --physics          Update physics components"
    echo "  --exts             Update and clean extension cache"
    echo "  --all              Run all updates"
    echo "  --clean            Clean extensions from extscache that exist in build tree (exclusive mode)"
    echo "  --commit-hash      Specific commit hash for template URL (used with --exts)"
    echo ""
    echo "Examples:"
    echo "  $0 --kit           # Update only kit components"
    echo "  $0 --kit --physics # Update kit and physics components"
    echo "  $0 --all           # Run all updates"
    echo "  $0 --clean         # Clean extensions only (cannot be combined with other modes)"
    echo "  $0 --exts --commit-hash abc123def456  # Update extensions with specific commit hash"
    echo ""
    exit 0
}

# Function to update kit components
update_kit() {
    echo "Updating kit components..."
    pushd ../
    ./repo.sh update kit-kernel --patch
    ./repo.sh validate_python_packages --update-omniverse-kit
    # update GMO package and other dep versions
    python3 tools/isaac/update_isaac_sim_deps.py
    popd
}

# Function to update physics components
update_physics() {
    echo "Updating physics components..."
    pushd ../
    ./repo.sh update omni_physics --include-pre-release --patch
    popd
}

# Function to update extension cache
update_extensions() {
    local commit_hash="$1"
    echo "Updating extension cache..."
    pushd ../
    
    # Build the command with optional commit hash and platform-specific paths
    local cmd="python3 tools/isaac/clean_extscache.py --update-locks --update-physics --match-kat"
    cmd="$cmd --build-dir _build/$PLATFORM/release/exts"
    cmd="$cmd --deprecated-dir _build/$PLATFORM/release/extsDeprecated"
    cmd="$cmd --apps-dir _build/$PLATFORM/release/apps"
    if [ -n "$commit_hash" ]; then
        cmd="$cmd --commit-hash $commit_hash"
        echo "Using commit hash: $commit_hash"
    fi
    
    # Run the command
    eval $cmd
    ./repo.sh build -r
    eval $cmd
    popd
}

# Function to clean extensions from extscache
clean_extensions() {
    echo "Cleaning extensions from extscache..."
    pushd ../
    python3 tools/isaac/clean_extscache.py \
        --build-dir "_build/$PLATFORM/release/exts" \
        --deprecated-dir "_build/$PLATFORM/release/extsDeprecated" \
        --apps-dir "_build/$PLATFORM/release/apps"
    popd
}

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
COMMIT_HASH=""

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
        --all)
            UPDATE_KIT=true
            UPDATE_PHYSICS=true
            UPDATE_EXTS=true
            shift
            ;;
        --commit-hash)
            # The next argument should be the commit hash
            if [[ $# -gt 1 ]]; then
                COMMIT_HASH="$2"
                shift 2
            else
                echo "Error: --commit-hash requires a value"
                print_help
            fi
            ;;
        --commit-hash=*)
            # Handle --commit-hash=value format
            COMMIT_HASH="${1#*=}"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            print_help
            ;;
    esac
done

# Validate that --clean is not combined with other modes
if [ "$CLEAN_EXTS" = true ]; then
    if [ "$UPDATE_KIT" = true ] || [ "$UPDATE_PHYSICS" = true ] || [ "$UPDATE_EXTS" = true ]; then
        echo "Error: --clean cannot be combined with --kit, --physics, --exts, or --all"
        print_help
    fi
fi

# Run selected updates
if [ "$UPDATE_KIT" = true ]; then
    update_kit
fi

if [ "$UPDATE_PHYSICS" = true ]; then
    update_physics
fi

if [ "$UPDATE_EXTS" = true ]; then
    update_extensions "$COMMIT_HASH"
fi

if [ "$CLEAN_EXTS" = true ]; then
    clean_extensions
fi

echo "Update completed successfully!"
