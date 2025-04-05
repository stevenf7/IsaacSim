# SPDX-FileCopyrightText: Copyright (c) 2018-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})

# enable the extension
import isaacsim.core.utils.extensions as extensions_utils

simulation_app.update()
extensions_utils.enable_extension("isaacsim.test.docstring")
simulation_app.update()

# run test
from isaacsim.test.docstring import StandaloneDocTestCase

tester = StandaloneDocTestCase()
tester.assertDocTests(StandaloneDocTestCase)

# quit
simulation_app.close()
