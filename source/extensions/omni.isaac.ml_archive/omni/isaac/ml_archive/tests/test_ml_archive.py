# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.kit.test
import omni.kit.pipapi


class TestPipArchive(omni.kit.test.AsyncTestCase):
    async def test_ml_archive(self):
        # Take one of packages from deps/pip.toml, it should be prebundled and available without need for going into online index
        omni.kit.pipapi.install("gym", version="0.21.0", use_online_index=False)
        import gym

        self.assertIsNotNone(gym)

    # import all packages to make sure dependencies were not missed
    async def test_import_all(self):
        import gym
        import torch
        import torchvision

        self.assertIsNotNone(torch)
        self.assertIsNotNone(torchvision)
        self.assertIsNotNone(gym)
