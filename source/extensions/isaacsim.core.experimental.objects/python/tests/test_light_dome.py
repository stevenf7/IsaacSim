# Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from typing import Literal

import isaacsim.core.utils.stage as stage_utils
import omni.kit.test
import omni.usd
import warp as wp
from isaacsim.core.experimental.objects import DomeLight as TargetLight
from isaacsim.core.experimental.prims.tests.utils import (
    check_allclose,
    check_array,
    check_lists,
    draw_choice,
    draw_indices,
    draw_sample,
)

from .utils import parametrize


async def populate_stage(max_num_prims: int, operation: Literal["wrap", "create"]) -> None:
    # create new stage
    await stage_utils.create_new_stage_async()
    # define prims
    if operation == "wrap":
        for i in range(max_num_prims):
            omni.kit.commands.execute(
                "CreatePrimWithDefaultXform",
                prim_type="DomeLight",
                prim_path=f"/World/A_{i}",
                attributes={"inputs:intensity": 30000},
                select_new_prim=False,
            )


class TestDomeLight(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        """Method called to prepare the test fixture"""
        super().setUp()

    async def tearDown(self):
        """Method called immediately after the test method has been called"""
        super().tearDown()

    # --------------------------------------------------------------------

    @parametrize(backends=["usd"], prim_classes=[TargetLight], populate_stage_func=populate_stage)
    async def test_len(self, prim, num_prims, device, backend):
        self.assertEqual(len(prim), num_prims, f"Invalid len ({num_prims} prims)")

    @parametrize(backends=["usd"], prim_classes=[TargetLight], populate_stage_func=populate_stage)
    async def test_are_of_type(self, prim, num_prims, device, backend):
        stage = omni.usd.get_context().get_stage()
        self.assertFalse(TargetLight.are_of_type("/World").numpy().item())
        self.assertTrue(TargetLight.are_of_type("/World/A_0").numpy().item())
        self.assertTrue(TargetLight.are_of_type(["/World/A_0"]).numpy().item())
        self.assertTrue(TargetLight.are_of_type(stage.GetPrimAtPath("/World/A_0")).numpy().item())
        self.assertTrue(TargetLight.are_of_type([stage.GetPrimAtPath("/World/A_0")]).numpy().item())

    @parametrize(backends=["usd"], prim_classes=[TargetLight], populate_stage_func=populate_stage)
    async def test_guide_radii(self, prim, num_prims, device, backend):
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for v0, expected_v0 in draw_sample(shape=(expected_count, 1), dtype=wp.float32):
                prim.set_guide_radii(v0, indices=indices)
                output = prim.get_guide_radii(indices=indices)
                check_array(output, shape=(expected_count, 1), dtype=wp.float32, device=device)
                check_allclose(expected_v0, output, given=(v0,))

    @parametrize(backends=["usd"], prim_classes=[TargetLight], populate_stage_func=populate_stage)
    async def test_texture_files(self, prim, num_prims, device, backend):
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for v0, expected_v0 in draw_choice(shape=(expected_count,), choices=["a", "bc", "def"]):
                prim.set_texture_files(v0, indices=indices)
                output = prim.get_texture_files(indices=indices)
                check_lists(expected_v0, output)

    @parametrize(backends=["usd"], prim_classes=[TargetLight], populate_stage_func=populate_stage)
    async def test_texture_formats(self, prim, num_prims, device, backend):
        choices = ["automatic", "latlong", "mirroredBall", "angular", "cubeMapVerticalCross"]
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for v0, expected_v0 in draw_choice(shape=(expected_count,), choices=choices):
                prim.set_texture_formats(v0, indices=indices)
                output = prim.get_texture_formats(indices=indices)
                check_lists(expected_v0, output)
