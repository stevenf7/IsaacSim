#!/bin/bash

set -e
set -f

SCRIPT_DIR=$(dirname ${BASH_SOURCE})
cd "$SCRIPT_DIR"


../repo.sh update kit-sdk --patch
../repo.sh update omni_physics_dev --include-pre-release --patch
../repo.sh update_extscache
# ../repo.sh update repo_
# ./packman/packman update -y