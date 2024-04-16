#!/usr/bin/env bash
#
# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

setup_python() {
  if [[ ! -e "${PROJECT_ROOT_DIR}/_python" ]]; then
    "${PROJECT_ROOT_DIR}/docker/common/env-bootstrap/packman/packman" install python  3.10.11+nv1-linux-$(arch) -l "${PROJECT_ROOT_DIR}/_python"
  fi

  if [[ ! -d _env ]]; then
    ${PROJECT_ROOT_DIR}/_python/bin/python3 -m venv _env
  fi

  PYTHON=${PROJECT_ROOT_DIR}/_env/bin/python
  if [[ ! -d _env/lib/python3.6/site-packages/docker ]]; then
    $PYTHON -m pip install docker
  fi

  if [[ ! -d _env/lib/python3.6/site-packages/pyyaml ]]; then
    $PYTHON -m pip install pyyaml
  fi
}
