#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version compatibility and resolve which interpreter to reference.
# Sets DOCS_PYTHON to the validated interpreter path for downstream use.
check_python_version() {
    local REPO_PYTHON="$SCRIPT_DIR/../_repo/python/python3"
    local KIT_PYTHON="$SCRIPT_DIR/../_build/linux-x86_64/release/kit/python/python3"

    if [ ! -f "$KIT_PYTHON" ]; then
        echo -e "${RED}ERROR: Kit Python not found at $KIT_PYTHON${NC}"
        echo -e "${RED}Please run ./build.sh first to build Isaac Sim.${NC}"
        exit 1
    fi

    if [ ! -f "$REPO_PYTHON" ]; then
        echo -e "${YELLOW}WARNING: Repo Python not found at $REPO_PYTHON${NC}"
        echo -e "${YELLOW}Falling back to Kit Python at $KIT_PYTHON${NC}"
        local KIT_VERSION=$("$KIT_PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        echo -e "${GREEN}Using Kit Python: $KIT_VERSION${NC}"
        return
    fi

    # Both interpreters exist -- verify they agree on major.minor version
    local REPO_VERSION=$("$REPO_PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    local KIT_VERSION=$("$KIT_PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

    if [ "$REPO_VERSION" != "$KIT_VERSION" ]; then
        echo -e "${RED}========================================${NC}"
        echo -e "${RED}ERROR: Python version mismatch!${NC}"
        echo -e "${RED}========================================${NC}"
        echo -e "${RED}Repo tools Python: $REPO_VERSION (from _repo/python/)${NC}"
        echo -e "${RED}Isaac Sim Python:  $KIT_VERSION (from _build/.../kit/python/)${NC}"
        echo ""
        echo -e "${YELLOW}To fix this, update the repo Python by:${NC}"
        echo -e "${YELLOW}  1. Remove the old _repo/python directory:${NC}"
        echo -e "${YELLOW}     rm -rf _repo/python${NC}"
        echo -e "${YELLOW}  2. Clear cached docs dependencies:${NC}"
        echo -e "${YELLOW}     rm -rf ~/.cache/packman/chk/repo_docs_deps${NC}"
        echo -e "${YELLOW}  3. Re-run ./build.sh to download the correct Python${NC}"
        exit 1
    fi

    echo -e "${GREEN}Python version check passed: $REPO_VERSION${NC}"
}

# Function to format duration
format_duration() {
    local total_seconds=$1
    local minutes=$((total_seconds / 60))
    local seconds=$((total_seconds % 60))
    if [ $minutes -gt 0 ]; then
        echo "${minutes}m ${seconds}s"
    else
        echo "${seconds}s"
    fi
}

# Function to run a command and track its duration
run_timed_step() {
    local step_name="$1"
    shift
    
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Starting: ${step_name}${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    local start_time=$(date +%s)
    "$@"
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    STEP_NAMES+=("$step_name")
    STEP_DURATIONS+=($duration)
    
    echo -e "${GREEN}Completed: ${step_name} in $(format_duration $duration)${NC}"
    echo ""
}

# Initialize arrays to store step information
declare -a STEP_NAMES
declare -a STEP_DURATIONS

# Record overall start time
OVERALL_START=$(date +%s)

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Documentation Build Started${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Check Python version compatibility before building
check_python_version
echo ""

# Remove repo log file if it exists
rm -f "$SCRIPT_DIR/../_repo/repo.log"

REPO_ROOT="$SCRIPT_DIR/.."

# Run each step with timing
run_timed_step "Copy PYI Stubs" "$REPO_ROOT/repo.sh" copy_pyi_stubs -c release
run_timed_step "Generate Doxygen Input" "$REPO_ROOT/repo.sh" -v generate_doxygen_input
run_timed_step "Extension Docs" "$REPO_ROOT/repo.sh" -v extension_docs --error-as-warn "$@"
run_timed_step "Extension TOC" "$REPO_ROOT/repo.sh" -v extension_toc --error-as-warn "$@"

# Build user guide first (main docs), then API docs into its py/ subfolder
# Use --project to build specific projects, or omit to build all
run_timed_step "Build User Guide" "$REPO_ROOT/repo.sh" -v docs --project isaac-sim -c release --warn-as-error=0 "$@" || true
run_timed_step "Build API Docs" "$REPO_ROOT/repo.sh" -v docs --project api -c release --warn-as-error=0 "$@" || true

run_timed_step "Examples List" "$REPO_ROOT/repo.sh" -v examples_list "$@"

# Calculate total time
OVERALL_END=$(date +%s)
TOTAL_DURATION=$((OVERALL_END - OVERALL_START))

# Print summary
echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Documentation Build Summary${NC}"
echo -e "${YELLOW}========================================${NC}"
for i in "${!STEP_NAMES[@]}"; do
    duration_str=$(format_duration ${STEP_DURATIONS[$i]})
    percent=$((${STEP_DURATIONS[$i]} * 100 / TOTAL_DURATION))
    printf "%-35s %10s (%3d%%)\n" "${STEP_NAMES[$i]}" "$duration_str" "$percent"
done
echo "----------------------------------------"
printf "%-35s %10s\n" "Total Time" "$(format_duration $TOTAL_DURATION)"
echo -e "${YELLOW}========================================${NC}"
