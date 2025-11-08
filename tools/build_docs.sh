#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# Remove repo log file if it exists
rm -f "$SCRIPT_DIR/../_repo/repo.log"

# Run each step with timing
run_timed_step "Generate Doxygen Input" "$SCRIPT_DIR/../repo.sh" -v generate_doxygen_input
run_timed_step "Extension Docs" "$SCRIPT_DIR/../repo.sh" -v extension_docs --error-as-warn "$@"
run_timed_step "Extension TOC" "$SCRIPT_DIR/../repo.sh" -v extension_toc --error-as-warn "$@"
run_timed_step "Build Docs (Doxygen + Sphinx)" "$SCRIPT_DIR/../repo.sh" -v docs -c release --warn-as-error=0 "$@"
run_timed_step "Examples List" "$SCRIPT_DIR/../repo.sh" -v examples_list "$@"

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
