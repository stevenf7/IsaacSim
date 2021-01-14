set -e

SCRIPT_DIR=$(dirname ${BASH_SOURCE})
cd "$SCRIPT_DIR"
../build.sh
../_build/linux-x86_64/release/isaac-sim.sh --ext-folder exts --ext-folder apps --publish $@