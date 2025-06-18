#!/bin/bash
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
    echo ""
    echo "Examples:"
    echo "  $0 --kit           # Update only kit components"
    echo "  $0 --kit --physics # Update kit and physics components"
    echo "  $0 --all           # Run all updates"
    echo ""
    exit 0
}

# Function to update kit components
update_kit() {
    echo "Updating kit components..."
    pushd ../
    ./repo.sh update kit-kernel --patch
    ./repo.sh check_python_package_definitions --update-omniverse-kit
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
    echo "Updating extension cache..."
    pushd ../
    python3 tools/isaac/clean_extscache.py --update-locks --update-physics --match-kat
    ./repo.sh build -ur
    python3 tools/isaac/clean_extscache.py --update-locks --update-physics --match-kat
    popd
}

# Get the directory where this script is located
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
cd "$SCRIPT_DIR"

# Parse command line arguments
if [ $# -eq 0 ]; then
    print_help
fi

# Initialize flags
UPDATE_KIT=false
UPDATE_PHYSICS=false
UPDATE_EXTS=false

# Process arguments
for arg in "$@"; do
    case $arg in
        -h|--help)
            print_help
            ;;
        --kit)
            UPDATE_KIT=true
            ;;
        --physics)
            UPDATE_PHYSICS=true
            ;;
        --exts)
            UPDATE_EXTS=true
            ;;
        --all)
            UPDATE_KIT=true
            UPDATE_PHYSICS=true
            UPDATE_EXTS=true
            ;;
        *)
            echo "Unknown option: $arg"
            print_help
            ;;
    esac
done

# Run selected updates
if [ "$UPDATE_KIT" = true ]; then
    update_kit
fi

if [ "$UPDATE_PHYSICS" = true ]; then
    update_physics
fi

if [ "$UPDATE_EXTS" = true ]; then
    update_extensions
fi

echo "Update completed successfully!"
