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

    async def test_imports_for_omni_isaac_tf_viewer_extension(self):
        # Testing all imports from original extension tests
        import os

        import carb
        import omni.graph.core as og
        import omni.kit.app
        from omni.isaac.core.utils.physics import simulate_async
        from omni.isaac.core.utils.stage import add_reference_to_stage, create_new_stage_async
        from omni.isaac.nucleus import get_assets_root_path_async
        from pxr import Sdf

        print("All imports successful for extension: omni.isaac.tf_viewer")
