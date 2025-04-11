# Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import numpy as np
import omni.kit.test
import warp as wp
from isaacsim.core.experimental.prims.impl import _ops

from .utils import check_array, check_equal


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
                        check_equal(output.numpy(), broadcasted)
                        # - list
                        output = _ops.broadcast_to(x.tolist(), shape=shape, dtype=dtype, device=device)
                        check_array(output, shape=shape, dtype=dtype, device=device)
                        check_equal(output.numpy(), broadcasted)
                        # - Warp array
                        output = _ops.broadcast_to(wp.array(x), shape=shape, dtype=dtype, device=device)
                        check_array(output, shape=shape, dtype=dtype, device=device)
                        check_equal(output.numpy(), broadcasted)
