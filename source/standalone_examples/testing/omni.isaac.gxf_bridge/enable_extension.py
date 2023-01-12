# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import time
import carb
from omni.isaac.kit import SimulationApp


kit = SimulationApp()
import omni
from omni.isaac.core.utils.extensions import enable_extension

# enable GXF bridge extension
enable_extension("omni.isaac.gxf")
kit.update()
kit.close()
