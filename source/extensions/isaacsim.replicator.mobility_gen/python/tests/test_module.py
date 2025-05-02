# SPDX-FileCopyrightText: Copyright (c) 2018-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import carb.tokens
import numpy as np

# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.usd
from isaacsim.replicator.mobility_gen.impl.common import Buffer, Module


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestPathPlanner(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        pass

    # After running each test
    async def tearDown(self):
        pass

    # test to make sure this runs
    async def test_module_named_buffers(self):

        class ModuleA(Module):
            def __init__(self):
                super().__init__()
                self.buffer_a = Buffer(value=0)

        class ModuleB(Module):
            def __init__(self):
                super().__init__()
                self.module_a = ModuleA()
                self.buffer_b = Buffer(value=1)

        module = ModuleB()

        self.assert_("buffer_b" in module.named_buffers())
        self.assert_("module_a.buffer_a" in module.named_buffers())

    async def test_module_state_dict(self):

        class ModuleA(Module):
            def __init__(self):
                super().__init__()
                self.buffer_a = Buffer(value=0)

        class ModuleB(Module):
            def __init__(self):
                super().__init__()
                self.module_a = ModuleA()
                self.buffer_b = Buffer(value=1)

        module = ModuleB()

        state_dict = module.state_dict()

        self.assert_("buffer_b" in state_dict)
        self.assertEqual(state_dict["buffer_b"], 1)
        self.assert_("module_a.buffer_a" in state_dict)
        self.assertEqual(state_dict["module_a.buffer_a"], 0)

    async def test_module_named_buffer_with_tags(self):

        class ModuleA(Module):
            def __init__(self):
                super().__init__()
                self.buffer_a = Buffer(value=0, tags=["foo", "bar"])

        class ModuleB(Module):
            def __init__(self):
                super().__init__()
                self.module_a = ModuleA()
                self.buffer_b = Buffer(value=1, tags=["foo"])

        module = ModuleB()

        state_dict = module.state_dict()

        foo_buffers = module.named_buffers(include_tags=["foo"])
        bar_buffers = module.named_buffers(include_tags=["bar"])
        nonbar_buffers = module.named_buffers(exclude_tags=["bar"])

        self.assert_("buffer_b" in foo_buffers)
        self.assert_("buffer_b" not in bar_buffers)
        self.assert_("buffer_b" in nonbar_buffers)

        self.assert_("module_a.buffer_a" in foo_buffers)
        self.assert_("module_a.buffer_a" in bar_buffers)
        self.assert_("module_a.buffer_a" not in nonbar_buffers)
