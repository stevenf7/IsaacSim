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

"""Tests for RTX GPU information retrieval."""

import omni.kit.test
from isaacsim.app.compatibility_check import _compatibility_check


class TestRtxGpuInfo(omni.kit.test.AsyncTestCase):
    """Test suite for RTX GPU information retrieval."""

    async def setUp(self):
        """Prepare the test fixture."""
        super().setUp()
        # ---------------
        # Do custom setUp
        # ---------------

    async def tearDown(self):
        """Clean up after the test method has been called."""
        # ------------------
        # Do custom tearDown
        # ------------------
        super().tearDown()

    # --------------------------------------------------------------------

    def test_rtx_gpu_info(self):
        """Verify RTX GPU info retrieval returns valid results."""
        _interface = _compatibility_check.acquire_compatibility_check_interface()
        ret, infos = _interface.get_rtx_gpu_info(False)  # don't create GPU Foundation
        self.assertTrue(ret, "Failed to get GPU info")
        self.assertTrue(len(infos) > 0, "No GPU info found")
        for info in infos:
            self.assertEqual(info.vendor_id, "10de")
