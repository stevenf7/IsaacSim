# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.kit.test
from omni.isaac.core.utils.viewports import get_intrinsics_matrix, set_intrinsics_matrix
import carb
from pxr import Sdf
import numpy as np


class TestViewports(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        pass

    # After running each test
    async def tearDown(self):
        pass

    async def test_get_intrinsics(self):
        viewport = omni.kit.viewport_legacy.get_default_viewport_window()
        viewport.set_texture_resolution(800, 600)
        await omni.kit.app.get_app().next_update_async()
        matrix = get_intrinsics_matrix(viewport)
        omni.kit.commands.execute(
            "ChangeProperty", prop_path=Sdf.Path("/OmniverseKit_Persp.verticalAperture"), value=6, prev=0
        )

        omni.kit.commands.execute(
            "ChangeProperty", prop_path=Sdf.Path("/OmniverseKit_Persp.horizontalAperture"), value=6, prev=0
        )

        await omni.kit.app.get_app().next_update_async()
        matrix = get_intrinsics_matrix(viewport)

        self.assertAlmostEqual(matrix[0, 0], 2419, delta=1)
        self.assertAlmostEqual(matrix[0, 2], 400, delta=1)
        self.assertAlmostEqual(matrix[1, 1], 1814, delta=1)
        self.assertAlmostEqual(matrix[1, 2], 300, delta=1)
        pass

    async def test_set_intrinsics(self):
        viewport = omni.kit.viewport_legacy.get_default_viewport_window()
        viewport.set_texture_resolution(800, 600)
        matrix = get_intrinsics_matrix(viewport)
        matrix = np.array([[3871, 0.0, 400.0], [0.0, 2177, 300.0], [0.0, 0.0, 1.0]])
        set_intrinsics_matrix(viewport, matrix)
        await omni.kit.app.get_app().next_update_async()
        matrix = get_intrinsics_matrix(viewport)
        self.assertAlmostEqual(matrix[0, 0], 3871, delta=1)
        self.assertAlmostEqual(matrix[0, 2], 400, delta=1)
        self.assertAlmostEqual(matrix[1, 1], 2177, delta=1)
        self.assertAlmostEqual(matrix[1, 2], 300, delta=1)
        pass
