# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
import omni.ext
from isaacsim.asset.gen.conveyor.bindings._isaacsim_asset_gen_conveyor import acquire_interface as _acquire
from isaacsim.asset.gen.conveyor.bindings._isaacsim_asset_gen_conveyor import release_interface as _release


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self.__interface = _acquire()

    def on_shutdown(self):
        _release(self.__interface)
        self.__interface = None
