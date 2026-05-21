#!/bin/bash
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
DOCS_DIR="$REPO_ROOT/_build/docs/isaac-sim/latest"
PORT="${1:-8000}"

if [ ! -d "$DOCS_DIR" ]; then
    echo "ERROR: Docs build output not found at $DOCS_DIR"
    echo "Run the docs build first:  ./tools/build_docs.sh"
    exit 1
fi

echo "Serving docs from: $DOCS_DIR"
echo "  User Guide: http://localhost:$PORT"
echo "  API Docs:   http://localhost:$PORT/py/"
echo ""
echo "Press Ctrl+C to stop."

cd "$DOCS_DIR"
python3 -m http.server "$PORT"
