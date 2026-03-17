# SPDX-FileCopyrightText: Copyright (c) 2018-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Test module for validating docstrings in the isaacsim.sensors.experimental.camera extension."""


import isaacsim.core.experimental.utils.stage as stage_utils
import isaacsim.test.docstring
from isaacsim.sensors.experimental.camera import (
    CameraSensor,
    SingleViewDepthCameraSensor,
    TiledCameraSensor,
    draw_annotator_data_to_image,
)
from pxr import UsdGeom


class TestExtensionDocstrings(isaacsim.test.docstring.AsyncDocTestCase):
    """Test case class for validating docstrings in the isaacsim.sensors.experimental.camera extension.

    This class extends isaacsim.test.docstring.AsyncDocTestCase to provide automated testing of docstring
    examples for camera sensor classes and functions. It sets up a USD stage environment with appropriate
    prims and validates that all docstring code examples execute correctly.

    The test class covers:
    - CameraSensor docstring validation
    - SingleViewDepthCameraSensor docstring validation
    - TiledCameraSensor docstring validation with multiple camera prims
    - draw_annotator_data_to_image function docstring validation

    Each test method creates the necessary USD prims and stage setup required for the respective sensor
    classes to function properly during docstring testing.
    """

    async def setUp(self) -> None:
        """Method called to prepare the test fixture."""
        super().setUp()
        # create new stage
        await stage_utils.create_new_stage_async()
        stage_utils.define_prim(f"/World", "Xform")

    async def tearDown(self) -> None:
        """Method called immediately after the test method has been called."""
        super().tearDown()

    # --------------------------------------------------------------------

    async def test_camera_sensor_docstrings(self) -> None:
        """Tests docstrings for the CameraSensor class by creating a camera prim and running docstring tests."""
        # define prim
        stage_utils.define_prim(f"/World/prim_0", "Camera")
        # test case
        await self.assertDocTests(CameraSensor)

    async def test_single_view_depth_camera_sensor_docstrings(self) -> None:
        """Tests docstrings for the SingleViewDepthCameraSensor class by creating a camera prim and running docstring tests."""
        # define prim
        stage_utils.define_prim(f"/World/prim_0", "Camera")
        # test case
        await self.assertDocTests(SingleViewDepthCameraSensor)

    async def test_tiled_camera_sensor_docstrings(self) -> None:
        """Tests docstrings for the TiledCameraSensor class by creating multiple camera prims with different transforms and running docstring tests."""
        # define prims
        for i in range(3):
            prim = stage_utils.define_prim(f"/World/prim_{i}", "Camera")
            UsdGeom.Xformable(prim).AddTranslateOp().Set((i * 1.0, 0.0, 0.0))
            UsdGeom.Xformable(prim).AddRotateXYZOp().Set((0.0, 0.0, 0.0))
        # test case
        await self.assertDocTests(TiledCameraSensor)

    async def test_draw_annotator_data_to_image_docstrings(self) -> None:
        """Tests docstrings for the draw_annotator_data_to_image function by running docstring tests."""
        self.assertDocTest(draw_annotator_data_to_image)
