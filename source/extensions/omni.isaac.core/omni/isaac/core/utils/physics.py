# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


import omni.kit
from typing import Callable


async def simulate_async(seconds: float, steps_per_sec: int = 60, callback: Callable = None) -> None:
    """Helper function to simulate async for seconds * steps_per_sec frames. 

    Args:
        seconds (float): time in seconds to simulate for
        steps_per_sec (int, optional): steps per second. Defaults to 60.
        callback (Callable, optional): optional function to run every step. Defaults to None.
    """
    for frame in range(int(steps_per_sec * seconds)):
        await omni.kit.app.get_app().next_update_async()
        if callback is not None:
            callback()
