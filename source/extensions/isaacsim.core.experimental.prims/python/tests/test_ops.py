# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import numpy as np
import omni.kit.test
import warp as wp
from isaacsim.core.experimental.prims.impl import _ops

from .common import check_array, check_equal


class TestOps(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        """Method called to prepare the test fixture"""
        super().setUp()
        # ---------------
        # Do custom setUp
        # ---------------
        self.parametrize_device = ["cpu", "cuda:0", None]
        self.parametrize_dtype = [wp.int8, wp.int16, wp.int32, wp.int64, wp.float16, wp.float32, wp.float64, None]
        self.parametrize_dim = [1, 2, 3, 4]

    async def tearDown(self):
        """Method called immediately after the test method has been called"""
        # ------------------
        # Do custom tearDown
        # ------------------
        super().tearDown()

    # --------------------------------------------------------------------

    async def test_place(self):
        for device in self.parametrize_device:
            for dtype in self.parametrize_dtype:
                for dim in self.parametrize_dim:
                    shape = (*([1] * (dim - 1)),) + (5,)
                    # list
                    x = list(range(5))
                    for _ in range(dim - 1):
                        x = [x]
                    output = _ops.place(x, dtype=dtype, device=device)
                    check_array(output, shape=shape, dtype=dtype, device=device)
                    # NumPy array
                    x = np.arange(5).reshape(*([1] * (dim - 1)), -1)
                    output = _ops.place(x, dtype=dtype, device=device)
                    check_array(output, shape=shape, dtype=dtype, device=device)
                    # Warp array
                    x = wp.array(x)
                    output = _ops.place(x, dtype=dtype, device=device)
                    check_array(output, shape=shape, dtype=dtype, device=device)

    async def test_resolve_indices(self):
        for device in self.parametrize_device:
            for dtype in self.parametrize_dtype:
                for dim in self.parametrize_dim:
                    shape = (5,)
                    # list
                    x = list(range(5))
                    for _ in range(dim - 1):
                        x = [x]
                    output = _ops.resolve_indices(x, count=5, dtype=dtype, device=device)
                    check_array(output, shape=shape, dtype=dtype, device=device)
                    # NumPy array
                    x = np.arange(5).reshape(*([1] * (dim - 1)), -1)
                    output = _ops.resolve_indices(x, count=5, dtype=dtype, device=device)
                    check_array(output, shape=shape, dtype=dtype, device=device)
                    # Warp array
                    x = wp.array(x)
                    output = _ops.resolve_indices(x, count=5, dtype=dtype, device=device)
                    check_array(output, shape=shape, dtype=dtype, device=device)

    async def test_broadcast_to(self):
        for device in self.parametrize_device:
            for dtype in self.parametrize_dtype:
                for shape in [(5,), (11, 5), (22, 11, 5), (33, 22, 11, 5)]:
                    for n in (1, 5):
                        x = np.arange(n).reshape(-1)
                        broadcasted = np.broadcast_to(x, shape=shape)
                        # - NumPy array
                        output = _ops.broadcast_to(x, shape=shape, dtype=dtype, device=device)
                        check_array(output, shape=shape, dtype=dtype, device=device)
                        check_equal(broadcasted, output)
                        # - list
                        output = _ops.broadcast_to(x.tolist(), shape=shape, dtype=dtype, device=device)
                        check_array(output, shape=shape, dtype=dtype, device=device)
                        check_equal(broadcasted, output)
                        # - Warp array
                        output = _ops.broadcast_to(wp.array(x), shape=shape, dtype=dtype, device=device)
                        check_array(output, shape=shape, dtype=dtype, device=device)
                        check_equal(broadcasted, output)
