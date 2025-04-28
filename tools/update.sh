#!/bin/bash
#
# Script to update and build the project components
#

# Exit immediately if a command exits with a non-zero status
set -e
# Disable filename expansion (globbing)
set -f

# Help function
print_help() {
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  -h, --help     Show this help message and exit"
  echo "  --repo         Run repo update"
  echo "  --packman      Run packman update"
  echo "  --extscache    Run build and clean extscache"
  echo ""
  exit 0
}

# Default values for command line options
RUN_REPO_UPDATE=false
RUN_PACKMAN_UPDATE=false
RUN_EXTSCACHE=false

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
    --extscache)
      RUN_EXTSCACHE=true
      shift
      ;;
  esac
done

# Get the directory where this script is located
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
cd "$SCRIPT_DIR"

# Update components
../repo.sh update kit-kernel --patch
../repo.sh update omni_physics_dev --include-pre-release --patch
../repo.sh check_python_package_definitions --update-omniverse-kit
python3 isaac/update_isaac_sim_deps.py --mode version

# Generate documentation
python3 isaac/generate_doxygen_input.py --root ../

# Run conditional updates based on command line arguments
if [ "$RUN_EXTSCACHE" = true ]; then
  echo "Running build and cleaning extscache..."
  # Build with update flag
  ../repo.sh build -u

  # Cleanup
  python3 isaac/clean_extscache.py --update-locks --kit-file="../source/apps/isaacsim.exp.extscache.kit"
fi

if [ "$RUN_REPO_UPDATE" = true ]; then
  echo "Running repo update..."
  ../repo.sh update repo_
fi

if [ "$RUN_PACKMAN_UPDATE" = true ]; then
  echo "Running packman update..."
  ./packman/packman update -y
fi
