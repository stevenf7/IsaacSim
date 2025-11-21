# SPDX-FileCopyrightText: Copyright (c) 2018-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import omni.ext

from .. import _debug_draw


class Extension(omni.ext.IExt):
    def on_startup(self):
        """Initialize the debug draw extension and acquire the debug draw interface."""
        self._draw = _debug_draw.acquire_debug_draw_interface()

    def on_shutdown(self):
        """Shutdown the debug draw extension and release the debug draw interface."""
        _debug_draw.release_debug_draw_interface(self._draw)
