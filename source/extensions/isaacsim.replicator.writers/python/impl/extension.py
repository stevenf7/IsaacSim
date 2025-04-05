# SPDX-FileCopyrightText: Copyright (c) 2022-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import omni.ext


class Extension(omni.ext.IExt):
    """Object that tracks the lifetime of the Python part of the extension loading"""

    def on_startup(self):
        """Set up initial conditions for the Python part of the extension"""
        from isaacsim.replicator.writers.scripts.writers import register_writers

        register_writers()

    def on_shutdown(self):
        """Shutting down this part of the extension prepares it for hot reload"""
        pass
