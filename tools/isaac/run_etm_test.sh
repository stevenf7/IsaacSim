#!/bin/bash

###############################################################################
# run_etm_test.sh
#
# Run ETM (Extension Test Mode) tests for a single Isaac Sim extension.
#
# What this does
# - Locates the built extension in `_build/linux-x86_64/release/exts/<extension_id>`
# - Chooses an appropriate `repo.sh` runner (prefers a Kit *source* checkout if
#   you point `KIT_DIR` at one)
# - Runs `repo.sh test -s etm -- ...` with the right `--ext-folder` and settings
#   so ETM can discover and load the extension under test.
#
# Common failure mode
# - This Isaac Sim repo typically does NOT define an `etm` test suite in its
#   repo_test configuration. The ETM suite usually comes from a Kit source repo.
#   If you see: "does not provide an 'etm' test suite", set `KIT_DIR` to a Kit
#   source checkout that defines the suite.
#
# Examples
#   ./tools/isaac/run_etm_test.sh isaacsim.ros2.bridge
#   KIT_DIR=~/repos/kit/kit ./tools/isaac/run_etm_test.sh isaacsim.ros2.bridge
#   EXTRA_EXT_FOLDERS="/some/path:/other/path" ./tools/isaac/run_etm_test.sh isaacsim.ros2.bridge
###############################################################################

set -euo pipefail  # Exit on any error; treat unset vars as errors; fail pipelines

usage() {
    cat <<'EOF'
Run ETM (Extension Test Mode) tests for a single built Isaac Sim extension.

Usage:
  run_etm_test.sh [--help] [--build-dir <dir>] [--config <cfg>] <extension_id>

Args:
  <extension_id>          Extension ID (e.g. isaacsim.ros2.bridge)

Options:
  -h, --help              Show this help and exit
  -b, --build-dir <dir>   Build dir relative to repo root
                          Default: _build/linux-x86_64/release
  -c, --config <cfg>      repo.sh build config passed to `repo.sh test -c`
                          Default: release

Environment:
  KIT_DIR                 Path to a Kit checkout/bundle used to find repo.sh.
                          If you point this to a Kit *source* repo, ETM suite is
                          typically available there.
  EXTRA_EXT_FOLDERS       Optional additional extension folders, ':'-separated.

Exit codes:
  1 invalid usage
  2 extension path missing (not built / wrong extension id)
  3 KIT_DIR not found
  4 no usable repo.sh found
  5 repo.sh has no 'etm' suite
EOF
}

log() { echo "[$(basename "$0")] $*"; }
die() { echo "[$(basename "$0")] Error: $*" >&2; exit "${2:-1}"; }

BUILD_DIR_DEFAULT="_build/linux-x86_64/release"
TEST_CONFIG_DEFAULT="release"

# Resolve paths relative to this script's location so it can be run from any CWD.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

BUILD_DIR="${BUILD_DIR_DEFAULT}"
TEST_CONFIG="${TEST_CONFIG_DEFAULT}"
EXTENSION_NAME=""

# Parse args (keep it simple and dependency-free; supports GNU-style long opts).
while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        -b|--build-dir)
            [ $# -ge 2 ] || die "Missing value for $1" 1
            BUILD_DIR="$2"
            shift 2
            ;;
        -c|--config)
            [ $# -ge 2 ] || die "Missing value for $1" 1
            TEST_CONFIG="$2"
            shift 2
            ;;
        --)
            shift
            break
            ;;
        -*)
            die "Unknown option: $1 (use --help)" 1
            ;;
        *)
            # First positional arg is the extension id.
            EXTENSION_NAME="$1"
            shift
            # Remaining args are unexpected (avoid silently ignoring typos).
            if [ $# -gt 0 ]; then
                die "Unexpected extra arguments: $* (use --help)" 1
            fi
            break
            ;;
    esac
done

if [ "${EXTENSION_NAME}" = "" ]; then
    usage >&2
    exit 1
fi

EXTENSION_PATH="${REPO_ROOT}/${BUILD_DIR}/exts/${EXTENSION_NAME}"

# Track whether the user explicitly provided KIT_DIR (so we can prioritize Kit's repo.sh).
USER_PROVIDED_KIT_DIR=0
if [ "${KIT_DIR+x}" = "x" ]; then
    USER_PROVIDED_KIT_DIR=1
fi

KIT_DIR="${KIT_DIR:-${REPO_ROOT}/${BUILD_DIR}/kit}"

log "Running ETM for extension: ${EXTENSION_NAME}"
log "Repo root: ${REPO_ROOT}"
log "Build dir: ${BUILD_DIR}"
log "Extension path: ${EXTENSION_PATH}"
log "KIT_DIR: ${KIT_DIR}"

if [ ! -d "$EXTENSION_PATH" ]; then
    die "Extension path not found: ${EXTENSION_PATH}
Did you build Isaac Sim (so ${BUILD_DIR}/exts exists) and pass the right extension id?" 2
fi

if [ ! -d "$KIT_DIR" ]; then
    die "KIT_DIR not found: ${KIT_DIR}
Set KIT_DIR to your Kit repo root, e.g.:
  KIT_DIR=/path/to/kit/kit $(basename "$0") ${EXTENSION_NAME}" 3
fi

REPO_SH=""
if [ "${USER_PROVIDED_KIT_DIR}" -eq 1 ] && [ -x "${KIT_DIR}/repo.sh" ]; then
    # If user explicitly points at a Kit source checkout, prefer it: that's where ETM suite is typically defined.
    REPO_SH="${KIT_DIR}/repo.sh"
elif [ -x "${REPO_ROOT}/repo.sh" ]; then
    # Isaac Sim repo runner (works from any CWD, but does not define an ETM suite by default).
    REPO_SH="${REPO_ROOT}/repo.sh"
elif [ -x "${KIT_DIR}/dev/repo.sh" ]; then
    # Built Kit bundle layout (often has an empty repo.toml and won't register repo_test suites).
    REPO_SH="${KIT_DIR}/dev/repo.sh"
elif [ -x "${KIT_DIR}/repo.sh" ]; then
    # Alternate layout.
    REPO_SH="${KIT_DIR}/repo.sh"
fi

if [ -z "${REPO_SH}" ]; then
    die "Could not find an executable repo.sh to run ETM tests.
Looked for:
  - ${REPO_ROOT}/repo.sh
  - ${KIT_DIR}/dev/repo.sh
  - ${KIT_DIR}/repo.sh" 4
fi

log "Using repo runner: ${REPO_SH}"

# Sanity check: ETM suite must exist in the *repo runner's* repo_test configuration.
# (E.g. Kit source repo defines it; this Isaac Sim repo does not.)
#
# We detect this by looking at the --suite choices emitted by `repo test -h`.
if ! "${REPO_SH}" test -h 2>/dev/null | grep -Eq -- "--suite \\{[^}]*\\betm\\b[^}]*\\}"; then
    die "The selected repo runner does not provide an 'etm' test suite.

Why this happens:
  - ETM is a repo_test *suite* defined by the Kit repo's repo.toml/config.
  - This Isaac Sim repo typically does not define an ETM suite, so
    'repo.sh test -s etm' is invalid with the Isaac runner.
  - The built Kit bundle at ${KIT_DIR} may have an empty kit/dev/repo.toml, so
    its repo.sh registers no tools/suites.

How to fix:
  - Point KIT_DIR at a Kit *source* checkout (or kit-kernel dev package) that
    supports ETM, e.g.:
      KIT_DIR=~/repos/kit/kit $(basename "$0") ${EXTENSION_NAME}" 5
fi

# Add extension folders so Kit can resolve cached extensions (mirrors how premake tests pass --ext-folder).
# We use absolute paths so the script works from any current directory.
EXT_FOLDERS=(
  "${REPO_ROOT}/${BUILD_DIR}/exts"
  "${REPO_ROOT}/${BUILD_DIR}/extscache"
  "${REPO_ROOT}/${BUILD_DIR}/extsDeprecated"
)

# Optional additional extension folders, separated by ':' (absolute or relative).
# Example:
#   EXTRA_EXT_FOLDERS="/some/path:/other/path" ./tools/isaac/run_etm_test.sh isaacsim.ros2.bridge
if [ "${EXTRA_EXT_FOLDERS:-}" != "" ]; then
    IFS=':' read -r -a EXTRA_EXT_FOLDERS_ARR <<< "${EXTRA_EXT_FOLDERS}"
    for p in "${EXTRA_EXT_FOLDERS_ARR[@]}"; do
        EXT_FOLDERS+=("$p")
    done
fi

EXT_FOLDER_ARGS=()
for p in "${EXT_FOLDERS[@]}"; do
    # Resolve relative paths against repo root to keep behavior predictable.
    if [[ "$p" != /* ]]; then
        p="${REPO_ROOT}/$p"
    fi
    if [ -d "$p" ]; then
        EXT_FOLDER_ARGS+=(--ext-folder "$p")
    fi
done

# Pass settings arrays with explicit quoting so paths/names are always valid.
log "Starting ETM (this may take a while)..."
"${REPO_SH}" test -c "${TEST_CONFIG}" -s etm -- \
  "${EXT_FOLDER_ARGS[@]}" \
  --/app/exts/devPaths="[\"${EXTENSION_PATH}\"]" \
  --/exts/omni.kit.etm.runner/include="[\"${EXTENSION_NAME}\"]"

log "ETM test completed successfully."