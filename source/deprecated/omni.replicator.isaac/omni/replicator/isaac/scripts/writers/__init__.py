# Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb

old_extension_name = "omni.replicator.isaac"
new_extension_name = "isaacsim.replicator.common"
module_name = "writers"

carb.log_warn(
    f"{old_extension_name}.{module_name} has been deprecated in favor of {new_extension_name}.{module_name}. Please update your code accordingly."
)

from isaacsim.replicator.common.scripts.writers.data_visualization_writer import *
from isaacsim.replicator.common.scripts.writers.dope_writer import *
from isaacsim.replicator.common.scripts.writers.pose_writer import *
from isaacsim.replicator.common.scripts.writers.pytorch_listener import *
from isaacsim.replicator.common.scripts.writers.pytorch_writer import *
from isaacsim.replicator.common.scripts.writers.ycb_video_writer import *
