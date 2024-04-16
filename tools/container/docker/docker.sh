#!/bin/bash -e

# Copyright (c) 2019, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

# Simple wrapper around our preferred version of the docker client, in case you
# don't have that version installed

SCRIPT_DIR="$(dirname "$0")"
${SCRIPT_DIR}/common/packman/packman pull -p linux ${SCRIPT_DIR}/packman.xml

${SCRIPT_DIR}/package-links/docker/docker "$@"

