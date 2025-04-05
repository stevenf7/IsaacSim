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

    async def test_imports_for_omni_isaac_conveyor_extension(self):
        # Testing all imports from original extension tests
        import asyncio
        import time

        import carb.tokens
        import numpy as np
        import omni.kit.commands
        from omni.isaac.conveyor.commands import CreateConveyorBelt
        from pxr import Gf, PhysxSchema, UsdGeom, UsdPhysics
        from usdrt import Sdf, Usd

        print("All imports successful for extension: omni.isaac.conveyor")
