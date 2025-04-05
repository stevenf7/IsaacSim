# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import omni.kit.test


class TestPipArchive(omni.kit.test.AsyncTestCase):
    # import all packages to make sure dependencies were not missed
    async def test_import_all(self):
        import filelock
        import fsspec
        import gymnasium
        import mpmath
        import networkx
        import sympy
        import torch
        import torchaudio
        import torchvision

        self.assertIsNotNone(torch)
        self.assertIsNotNone(torchvision)
        self.assertIsNotNone(torchaudio)
        self.assertIsNotNone(filelock)
        self.assertIsNotNone(fsspec)
        self.assertIsNotNone(mpmath)
        self.assertIsNotNone(networkx)
        self.assertIsNotNone(sympy)
        self.assertIsNotNone(gymnasium)
