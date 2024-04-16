#!/bin/bash -e

# Copyright (c) 2019, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

SCRIPT_DIR="$(dirname "$0")"
${SCRIPT_DIR}/common/packman/packman pull -p linux ${SCRIPT_DIR}/packman.xml

DOCKER_CLIENT=${SCRIPT_DIR}/package-links/docker/docker

PYTHONPATH=${SCRIPT_DIR}/package-links/docker-py ${SCRIPT_DIR}/common/py3.sh ${SCRIPT_DIR}/misc/smart_cleanup.py \
    --docker=${DOCKER_CLIENT} "$@"

