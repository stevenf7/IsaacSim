#!/bin/bash
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# Wrapper script for stubgen that preloads TBB (required by cached physx extensions).
# The physx Python bindings expect TBB symbols to be globally available at import time,
# but stubgen's --disable-ext-startup prevents native plugins from loading TBB first.

set -e

ROOT="$1"
CONFIG="$2"

if [ -z "$ROOT" ] || [ -z "$CONFIG" ]; then
    echo "Usage: $0 <root> <config>"
    exit 1
fi

# Find the TBB shared library in the USD target-deps (debug: libtbb_debug.so.12, release: libtbb.so.12)
TBB_LIB=$(ls "$ROOT/_build/target-deps/usd/$CONFIG/lib"/libtbb*.so.12 2>/dev/null | grep -v malloc | grep -v bind | head -1)
if [ -n "$TBB_LIB" ]; then
    export LD_PRELOAD="$TBB_LIB"
fi

export LD_LIBRARY_PATH="$ROOT/_build/target-deps/cuda/lib64/stubs:$ROOT/_build/target-deps/usd/$CONFIG/lib"

exec "$ROOT/repo.sh" stubgen -c "$CONFIG"
