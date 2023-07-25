#!/bin/bash

set -e
set -f

SCRIPT_DIR=$(dirname ${BASH_SOURCE})
cd "$SCRIPT_DIR"


../repo.sh update kit-sdk
../repo.sh update repo_
../repo.sh update omni_physics --include-pre-release
../repo.sh update_extscache
./packman/packman update -y