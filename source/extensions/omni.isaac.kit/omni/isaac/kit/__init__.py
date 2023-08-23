# Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import builtins
import os

from .app_framework import AppFramework
from .simulation_app import SimulationApp

builtins.ISAAC_LAUNCHED_FROM_JUPYTER = (
    os.getenv("ISAAC_JUPYTER_KERNEL") is not None
)  # We set this in the kernel.json file

if builtins.ISAAC_LAUNCHED_FROM_JUPYTER:
    import nest_asyncio

    nest_asyncio.apply()
else:
    import carb

    # Do a sanity check to see if we are running in an ipython env
    try:
        get_ipython()
        carb.log_warn(
            "Interactive python shell detected but ISAAC_JUPYTER_KERNEL was not set. Problems with asyncio may occur"
        )
    except Exception:
        # We are probably not in an interactive shell
        pass
