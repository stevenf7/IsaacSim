# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import omni.kit.test


class TestImports(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    async def test_imports_for_omni_isaac_ui_extension(self):
        # Testing all imports from original extension tests
        import asyncio
        import os

        import carb
        import numpy as np
        import omni.timeline
        import omni.ui as ui
        import pyperclip
        from omni.isaac.core.articulations import Articulation
        from omni.isaac.core.objects.cuboid import FixedCuboid, VisualCuboid
        from omni.isaac.core.utils.prims import delete_prim
        from omni.isaac.core.utils.stage import add_reference_to_stage, create_new_stage, update_stage_async
        from omni.isaac.core.world import World
        from omni.isaac.nucleus import get_assets_root_path
        from omni.isaac.ui import ScreenPrinter
        from omni.isaac.ui.element_wrappers.core_connectors import LoadButton, ResetButton

        print("All imports successful for extension: omni.isaac.ui")
