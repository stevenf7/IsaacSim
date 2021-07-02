set -e

SCRIPT_DIR=$(dirname ${BASH_SOURCE})
cd "$SCRIPT_DIR"
../repo.sh publish_exts -c release $@

# keeping manual command below for reference
# ../build.sh
# ../_build/linux-x86_64/release/isaac-sim.sh --ext-folder exts --ext-folder apps --publish