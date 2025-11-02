#!/bin/bash
# Script to analyze Python package usage and update pip*.toml files with extension usage information
#
# This script:
# 1. Analyzes which extensions use which Python packages
# 2. Identifies transitive dependencies using pipdeptree
# 3. Updates all pip*.toml files with "# Used by:" comments
# 4. Maintains consistent formatting with aligned columns

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory and navigate to repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Python Package Usage Analyzer${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Working directory: $REPO_ROOT"
echo ""

# Check if pipdeptree is installed
echo -e "${YELLOW}Checking for pipdeptree...${NC}"
if ! _build/linux-x86_64/release/python.sh -m pipdeptree --version > /dev/null 2>&1; then
    echo -e "${YELLOW}pipdeptree not found. Installing...${NC}"
    _build/linux-x86_64/release/python.sh -m pip install pipdeptree
    echo -e "${GREEN}✓ pipdeptree installed${NC}"
else
    echo -e "${GREEN}✓ pipdeptree already installed${NC}"
fi
echo ""

# Step 1: Analyze package usage
echo -e "${BLUE}Step 1: Analyzing package usage across extensions...${NC}"
echo -e "${YELLOW}This will scan all Python files to identify which extensions use which packages${NC}"
python tools/isaac/validate_pip_dependencies.py \
    --package-extensions \
    --include-transitive-deps \
    --package-extensions-json package_extensions_with_deps.json

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to analyze package usage${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Analysis complete${NC}"
echo ""

# Step 2: Update pip*.toml files
echo -e "${BLUE}Step 2: Updating pip*.toml files with usage information...${NC}"
if [ ! -f "package_extensions_with_deps.json" ]; then
    echo -e "${RED}✗ Error: package_extensions_with_deps.json not found${NC}"
    exit 1
fi

python tools/isaac/update_pip_toml_with_deps.py

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to update pip*.toml files${NC}"
    exit 1
fi
echo -e "${GREEN}✓ All pip*.toml files updated${NC}"
echo ""

# Step 3: Show summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Updated files:"
for file in deps/pip*.toml; do
    echo -e "  ${GREEN}✓${NC} $(basename "$file")"
done
echo ""

# Count statistics from JSON
if command -v jq &> /dev/null; then
    DIRECTLY_USED=$(jq '.summary.directly_used' package_extensions_with_deps.json)
    TRANSITIVE=$(jq '.summary.transitive_dependencies' package_extensions_with_deps.json)
    UNUSED=$(jq '.summary.potentially_unused' package_extensions_with_deps.json)
    
    echo "Package statistics:"
    echo -e "  Directly used by extensions:  ${GREEN}$DIRECTLY_USED${NC}"
    echo -e "  Transitive dependencies:       ${YELLOW}$TRANSITIVE${NC}"
    echo -e "  Potentially unused:            ${RED}$UNUSED${NC}"
    echo ""
fi

# Optional: Clean up temporary files
if [ -t 0 ]; then
    # Interactive mode - ask user
    read -p "Remove temporary JSON file (package_extensions_with_deps.json)? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f package_extensions_with_deps.json
        echo -e "${GREEN}✓ Temporary file removed${NC}"
    else
        echo -e "${YELLOW}Keeping temporary file for reference${NC}"
    fi
else
    # Non-interactive mode - keep the file
    echo -e "${YELLOW}Non-interactive mode: Keeping package_extensions_with_deps.json for reference${NC}"
fi
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Done!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "All pip*.toml files have been updated with:"
echo "  • Normalized SWIPAT format"
echo "  • Extension usage information"
echo "  • Transitive dependency annotations"
echo "  • Aligned column formatting"
echo ""
echo "You can review the changes with: git diff deps/"

