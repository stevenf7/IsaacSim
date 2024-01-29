# Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import argparse
import os
import platform

import packmanapi


def get_host_platform() -> str:
    """Get host platform string (platform-arch, E.g.: "windows-x86_64")"""
    arch = platform.machine()
    if arch == "AMD64":
        arch = "x86_64"
    platform_host = platform.system().lower() + "-" + arch
    return platform_host


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.prog = "autopull"
    parser.description = "Auto pull Kit SDK."
    parser.add_argument(
        "-c",
        "--config",
        dest="config",
        required=False,
        default="debug",
        help="Config to run test against (debug or release). (default: %(default)s)",
    )
    options = parser.parse_args()

    script_dir = os.path.dirname(os.path.realpath(__file__))
    packmanapi.pull(
        os.path.join(script_dir, "../../deps/kit-sdk.packman.xml"),
        platform=get_host_platform(),
        include_tags=[options.config],
        tokens={"config": options.config},
    )
