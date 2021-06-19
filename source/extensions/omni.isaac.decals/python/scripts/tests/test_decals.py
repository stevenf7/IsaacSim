# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.kit.test

import omni.kit.undo
import omni.kit.commands
import carb.tokens
import os
import asyncio

from pxr import Gf, Kind, Sdf, Usd, UsdGeom, UsdShade

from omni.isaac.decals import _decals


class TestDecals(omni.kit.test.AsyncTestCaseFailOnLogError):
    async def setUp(self):
        self._decals = _decals.acquire()

        # these must be in the extension "startup" or i can't seem to get decals to work properly
        self._decals.set_enabled(True)
        self._decals.set_picking_enabled(True)
        pass

    # After running each test
    async def tearDown(self):
        pass

    async def test_all(self):
        # first pass at a test.  should probabbly break this into many, smaller tests

        await omni.usd.get_context().new_stage_async()
        stage = omni.usd.get_context().get_stage()
        root_layer = stage.GetRootLayer()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())

        success = omni.kit.commands.execute("CreatePrimCommand", prim_type="Cube")
        # success = omni.kit.commands.execute("CreateMeshPrimCommand", prim_type="Cube")
        # BUG: meshPath from this command returns None type.  see https://jirasw.nvidia.com/browse/ISAACSIM-1076

        meshPath = default_prim_path + "/Cube"

        self._decals.set_pen_color(1.0, 0, 0)
        self._decals.set_pen_width(5.0)
        self._decals.set_pen_offset(0.1)
        self._decals.set_pen_threshold(10.0)
        self._decals.set_pen_surface(meshPath)
        self._decals.set_pen_position((0, 0, 0))

        self._decals.set_pen_down(True)
        self._decals.set_pen_position((1, 0, 0))
        self._decals.set_pen_position((0, 1, 0))
        self._decals.set_pen_position((0, 0, 1))
        self._decals.set_pen_position((1, 0, 0))
        self._decals.set_pen_down(False)

        self._decals.erase_surface(meshPath)
        self._decals.erase_all_surfaces()

        if omni.kit.undo.can_undo():
            omni.kit.undo.undo()
        pass
