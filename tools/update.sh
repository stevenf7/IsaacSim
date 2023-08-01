#!/bin/bash

set -e
set -f

SCRIPT_DIR=$(dirname ${BASH_SOURCE})
cd "$SCRIPT_DIR"


../repo.sh update kit-sdk
../repo.sh update omni_physics --include-pre-release
../repo.sh update_extscache
# ../repo.sh update repo_
# ./packman/packman update -y