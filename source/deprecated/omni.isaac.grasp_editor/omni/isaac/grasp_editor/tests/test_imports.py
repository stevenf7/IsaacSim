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

    async def test_imports_for_omni_isaac_grasp_editor_extension(self):
        # Testing all imports from original extension tests
        import asyncio

        import numpy as np
        from omni.isaac.core.objects import GroundPlane
        from omni.isaac.core.prims import XFormPrim, XFormPrimView
        from omni.isaac.core.utils.viewports import set_camera_view
        from omni.isaac.grasp_editor import GraspSpec, import_grasps_from_file
        from omni.isaac.grasp_editor.util import move_rb_subframe_to_position
        from omni.isaac.nucleus import get_assets_root_path_async
        from pxr import Sdf, UsdLux, UsdPhysics

        print("All imports successful for extension: omni.isaac.grasp_editor")
