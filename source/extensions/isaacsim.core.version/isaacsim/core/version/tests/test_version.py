# SPDX-FileCopyrightText: Copyright (c) 2022-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import omni.kit.test
from isaacsim.core.version import get_version, parse_version


class TestIsaacVersion(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    async def test_version(self):
        parsed_version = parse_version("2000.0.0-beta.0+branch.0.hash.local")
        self.assertTrue(parsed_version.core == "2000.0.0")
        self.assertTrue(parsed_version.pretag == "beta")
        self.assertTrue(parsed_version.prebuild == "0")
        self.assertTrue(parsed_version.buildtag == "branch.0.hash.local")

        version = get_version()
        self.assertTrue(len(version) == 8)
