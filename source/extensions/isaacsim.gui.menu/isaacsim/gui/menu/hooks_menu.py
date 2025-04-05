# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
import omni.kit.menu.utils


class HookMenuHandler:
    def __init__(self):
        omni.kit.menu.utils.add_hook(self.__hook_func)

    def __del__(self):
        omni.kit.menu.utils.remove_hook(self.__hook_func)

    def __hook_func(self, merged_menu):
        for name in merged_menu:
            for i in merged_menu[name].copy():
                # remove all glyphs in all menus expect create
                if name != "Create":
                    i.glyph = None

                # HACK to show all menu items
                # i.show_fn = None
