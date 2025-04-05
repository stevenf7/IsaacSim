# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import carb
import omni.ext
import omni.kit.app

from .. import _openxr

# expose pybind interface/API
_openxr_interface = None


def acquire_openxr_interface():
    return _openxr_interface


class OpenXR(omni.ext.IExt):
    """The Extension class"""

    def on_startup(self, ext_id):
        """Method called when the extension is loaded/enabled"""
        carb.log_info(f"on_startup {ext_id}")
        ext_path = omni.kit.app.get_app().get_extension_manager().get_extension_path(ext_id)

        # acquire the pybind interface
        global _openxr_interface
        _openxr_interface = _openxr.acquire_openxr_interface()

    def on_shutdown(self):
        """Method called when the extension is disabled"""
        carb.log_info(f"on_shutdown")
        # release the pybind interface
        global _openxr_interface
        _openxr.release_openxr_interface(_openxr_interface)
        _openxr_interface = None

    def locate_hand_joints(self, hand, time=None, stage_axis=True):
        return _openxr_interface.locate_hand_joints(hand, time, stage_axis)
