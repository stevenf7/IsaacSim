# Copyright (c) 2018-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import isaacsim.test.docstring


class TestAsyncDocTest(isaacsim.test.docstring.AsyncDocTestCase):
    # Before running each test
    async def setUp(self):
        pass

    # After running each test
    async def tearDown(self):
        pass

    async def test_async_doctest_case(self):
        from isaacsim.test.docstring import AsyncDocTestCase

        await self.assertDocTests(AsyncDocTestCase)
