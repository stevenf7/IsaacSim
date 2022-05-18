# Copyright (c) 2021-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.kit.test
from omni.isaac.core.utils.prims import get_all_matching_child_prims
import omni.kit.commands
import numpy as np
import torch


class TestPrims(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()
        pass

    # After running each test
    async def tearDown(self):
        pass

    async def test_get_all_matching_child_prims(self):
        from omni.isaac.core.utils.prims import create_prim
        from omni.isaac.core.utils.stage import clear_stage

        clear_stage()
        create_prim("/World/Floor")
        create_prim("/World/Floor/thefloor", "Cube", position=np.array([75, 75, -150.1]), attributes={"size": 300})
        create_prim("/World/Room", "Sphere", attributes={"radius": 1e3})

        result = get_all_matching_child_prims("/World")
        self.assertListEqual(result, ["/World", "/World/Floor", "/World/Room", "/World/Floor/thefloor"])

    async def test_create_prim(self):
        from omni.isaac.core.utils.prims import create_prim
        from omni.isaac.core.utils.stage import clear_stage

        clear_stage()
        create_prim("/World")
        create_prim(
            "/World/thebox", "Cube", position=[175, 75, 0.0], orientation=[0.0, 0.0, 0.0, 1.0], attributes={"size": 150}
        )
        create_prim(
            "/World/thechair1",
            "Cube",
            position=(-75, 75, 0.0),
            orientation=(0.0, 0.0, 0.0, 1.0),
            attributes={"size": 150},
        )
        create_prim("/World/thechair2", "Cube", position=np.array([75, 75, 0.0]), attributes={"size": 150})
        create_prim("/World/thetable", "Cube", position=torch.Tensor([-175, 75, 0.0]), attributes={"size": 150})

        result = get_all_matching_child_prims("/World")
        self.assertListEqual(
            result, ["/World", "/World/thebox", "/World/thechair1", "/World/thechair2", "/World/thetable"]
        )
