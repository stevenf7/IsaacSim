# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
import argparse
import os
import sys
from typing import Callable, Dict

import omni.repo.ci


def main(args: argparse.Namespace):
    build_config_arg = ["-c", args.build_config, "--from-package"]
    test_cmd = ["${root}/repo${shell_ext}", "test"] + build_config_arg + args.extra_args
    print(test_cmd)
    # Run test
    omni.repo.ci.launch(test_cmd)
