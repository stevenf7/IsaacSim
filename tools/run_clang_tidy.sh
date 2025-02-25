#!/bin/bash
set -euo pipefail

# Usage: ./scripts/run_clang_tidy.sh <source-dir> [clang-tidy-args...]

if [ $# -lt 1 ]; then
    echo "Usage: $0 <source-dir> [clang-tidy-args...]"
    exit 1
fi

SOURCE_DIR="$1"
shift  # Remove first argument, leaving remaining args for clang-tidy

CONFIG_FILE="$(pwd)/.clang-tidy"
COMPILE_COMMANDS="$(pwd)/_build/linux-x86_64/release/compile_commands.json"

# Verify required files exist
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: .clang-tidy config file not found in project root"
    exit 1
fi

if [ ! -f "$COMPILE_COMMANDS" ]; then
    echo "Error: compile_commands.json not found in build directory"
    echo "       Make sure to generate it first with:"
    echo "       cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON .."
    exit 1
fi

# Run clang-tidy on all C++ files in source directory, excluding specified paths
find "$SOURCE_DIR" -type f \( -iname '*.cpp' -o -iname '*.h' \) \
    -not -path "*/isaac_ros2_messages/*" \
    -not -path "*/isaacsim.robot.schema/*" \
    -print0 \
    | xargs -0 -n1 -P$(nproc) clang-tidy \
    -p "$COMPILE_COMMANDS" \
    --extra-arg="-std=c++17" \
    --extra-arg="-Wno-error" \
    --quiet \
    --warnings-as-errors=-* \
    "$@"  # Add any additional arguments passed to the script

echo "Clang-tidy analysis completed successfully" 