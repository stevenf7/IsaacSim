# SPDX-FileCopyrightText: Copyright (c) 2018-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import gc

import omni.ext
import omni.kit.commands

from .. import _dynamic_control

EXTENSION_NAME = "Dynamic Control"


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._dc = _dynamic_control.acquire_dynamic_control_interface()

    def on_shutdown(self):
        _dynamic_control.release_dynamic_control_interface(self._dc)
        gc.collect()
