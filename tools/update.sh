#!/bin/bash

set -e
set -f

SCRIPT_DIR=$(dirname ${BASH_SOURCE})
cd "$SCRIPT_DIR"


../repo.sh update kit-kernel --patch
../repo.sh update omni_physics_dev --include-pre-release --patch
../repo.sh check_python_package_definitions --update-omniverse-kit
python3 isaac/generate_doxygen_input.py --root ../
# ../repo.sh update repo_
# ./packman/packman update -y