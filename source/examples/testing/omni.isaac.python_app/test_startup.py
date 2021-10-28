# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from omni.isaac.python_app import OmniKitHelper
import os

# The most basic usage for creating a simulation app
kit = OmniKitHelper({"experience": f'{os.environ["EXP_PATH"]}/omni.isaac.sim.python.kit'})

for i in range(100):
    kit.update()

kit.get_context()
kit.get_stage()
kit.get_status()
kit.is_exiting()
kit.is_loading()
kit.play()
kit.pause()
kit.stop()
kit.setup_renderer()
kit.shutdown()  # Cleanup application
