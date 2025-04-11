# Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


import isaacsim.core.utils.stage as stage_utils
import omni.kit.test
import omni.usd
from isaacsim.core.experimental.prims import Prim


class TestPrim(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        """Method called to prepare the test fixture"""
        super().setUp()

    async def tearDown(self):
        """Method called immediately after the test method has been called"""
        super().tearDown()

    # --------------------------------------------------------------------

    async def test_resolve_paths(self):
        # create new stage
        await stage_utils.create_new_stage_async()
        # define prims
        stage = omni.usd.get_context().get_stage()
        for i in range(3):
            stage.DefinePrim(f"/World/A_{i}", "Xform")
            stage.DefinePrim(f"/World/A_{i}/B", "Cube")
        # test cases (valid results)
        # - single path
        existing_paths, nonexistent_paths = Prim.resolve_paths("/World/A_0")
        assert len(existing_paths) == 1 and len(nonexistent_paths) == 0
        # - single path (non-existing)
        existing_paths, nonexistent_paths = Prim.resolve_paths("/World/C")
        assert len(existing_paths) == 0 and len(nonexistent_paths) == 1
        # - regex
        existing_paths, nonexistent_paths = Prim.resolve_paths("/World/A_.*/B")
        assert len(existing_paths) == 3 and len(nonexistent_paths) == 0
        # test cases
        # - mixed paths
        with self.assertRaises(ValueError):
            Prim.resolve_paths(["/World/A_.*", "/World/C"])
        # no existing or non-existing paths exist
        with self.assertRaises(ValueError):
            Prim.resolve_paths("/World/A_.*/C")
        # incomplete existing paths
        with self.assertRaises(ValueError):
            Prim.resolve_paths(["/World/A_.*/B", "/World/A_.*/C"])
        # incomplete non-existing paths
        with self.assertRaises(ValueError):
            Prim.resolve_paths(["/World/C", "/World/A_.*/C"])
