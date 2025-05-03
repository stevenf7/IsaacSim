# Copyright (c) 2018-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import gc

import omni

from .. import _surface_gripper

EXTENSION_NAME = "Surface Gripper"


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._sg = _surface_gripper.acquire_surface_gripper_interface()

    def on_shutdown(self):
        _surface_gripper.release_surface_gripper_interface(self._sg)

        gc.collect()
