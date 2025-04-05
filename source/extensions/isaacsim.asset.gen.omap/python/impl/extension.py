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
import omni.kit.commands

from ..bindings import _omap


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._interface = _omap.acquire_omap_interface()

    def on_shutdown(self):
        _omap.release_omap_interface(self._interface)
