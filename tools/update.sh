#!/bin/bash

set -e
set -f

SCRIPT_DIR=$(dirname ${BASH_SOURCE})
cd "$SCRIPT_DIR"


../repo.sh update omniverse-kit
../repo.sh update repo_
./packman/packman update -y