#!/usr/bin/env bash
#
# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

set -eu

# Keep track of important locations
export BIN_DIR="$( cd "$(dirname "$0")" ; pwd -P )"
export PROJECT_ROOT_DIR="$( cd "$(dirname $(dirname $(dirname "$0")))" ; pwd -P )"

# Debug
echo "---- Debug ---------------------------------"
echo "BIN_DIR=$BIN_DIR"
echo "PROJECT_ROOT_DIR=$PROJECT_ROOT_DIR"

# Setup Python environment
echo "---- Setup Python environment --------------"
. "${BIN_DIR}/common.sh"
setup_python

# Publish the image
echo "---- Republishing image --------------------"
$PYTHON -B ${PROJECT_ROOT_DIR}/docker/republish.py $@
