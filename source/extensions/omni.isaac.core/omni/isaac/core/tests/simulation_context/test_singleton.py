# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.kit.test
from scipy.spatial.transform import Rotation
import numpy as np
from omni.isaac.core import World


class TestSingleton(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        pass

    # After running each test
    async def tearDown(self):
        pass

    async def test_singleton(self):
        my_world_1 = World()
        my_world_2 = World()
        self.assertTrue(my_world_1 == my_world_2)
        await omni.kit.app.get_app().next_update_async()

        # try to delete the previous one
        my_world_2.__del__()
        self.assertTrue(my_world_1.instance() is None)
        my_world_3 = World()
        self.assertTrue(my_world_1 != my_world_3)
        self.assertTrue(my_world_1.instance() == my_world_3.instance())
        return
