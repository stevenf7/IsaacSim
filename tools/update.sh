#!/bin/bash
#
# Script to update and build the project components
#

# Exit immediately if a command exits with a non-zero status
set -e
# Disable filename expansion (globbing)
set -f

# Function to run extension cache cleaning and building
run_extscache_operations() {
  echo "Running build and cleaning extscache..."
  pushd ../
  # update extensions to match kit and physics versions
  python3 tools/isaac/clean_extscache.py --update-locks --kit-file="source/apps/isaacsim.exp.extscache.kit" --update-physics

  # Build with update flag to update extension cache
  ./repo.sh build -ur

  # Cleanup extension cache
  python3 tools/isaac/clean_extscache.py --update-locks --kit-file="source/apps/isaacsim.exp.extscache.kit" --update-physics
  popd
}

# Help function
print_help() {
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  -h, --help         Show this help message and exit"
  echo "  --repo             Run repo update"
  echo "  --packman          Run packman update"
  echo "  --only-extscache   Only run extension cache cleaning and building"
  echo ""
  exit 0
}

# Default values for command line options
RUN_REPO_UPDATE=false
RUN_PACKMAN_UPDATE=false
ONLY_EXTSCACHE=false

# Parse command line arguments
for arg in "$@"; do
  case $arg in
    -h|--help)
      print_help
      ;;
    --repo)
      RUN_REPO_UPDATE=true
      shift
      ;;
    --packman)
      RUN_PACKMAN_UPDATE=true
      shift
      ;;
    --only-extscache)
      ONLY_EXTSCACHE=true
      shift
      ;;
  esac
done

# Get the directory where this script is located
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
cd "$SCRIPT_DIR"

# If only-extscache mode, skip all other updates and go straight to extscache operations
if [ "$ONLY_EXTSCACHE" = true ]; then
  run_extscache_operations
  exit 0
fi

# Update components
# ../repo.sh update kit-kernel --patch
../repo.sh update omni_physics --include-pre-release --patch
../repo.sh check_python_package_definitions --update-omniverse-kit
python3 isaac/update_isaac_sim_deps.py --mode version
pushd ../
# Generate documentation
python3 tools/isaac/generate_doxygen_input.py --root ./
popd

# Run build and clean extscache (now runs by default)
run_extscache_operations

# Run conditional updates based on command line arguments
if [ "$RUN_REPO_UPDATE" = true ]; then
  echo "Running repo update..."
  ../repo.sh update repo_
fi

if [ "$RUN_PACKMAN_UPDATE" = true ]; then
  echo "Running packman update..."
  ./packman/packman update -y
fi
