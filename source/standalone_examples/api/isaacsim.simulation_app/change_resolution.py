# SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import random

from isaacsim import SimulationApp

# Simple example showing how to change resolution
kit = SimulationApp({"headless": True})
kit.update()
for i in range(100):
    width = random.randint(128, 1980)
    height = random.randint(128, 1980)
    kit.set_setting("/app/renderer/resolution/width", width)
    kit.set_setting("/app/renderer/resolution/height", height)
    kit.update()
    print(f"resolution set to: {width}, {height}")

# cleanup
kit.close()
