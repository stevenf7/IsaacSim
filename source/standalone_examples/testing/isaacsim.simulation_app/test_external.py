# SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
import sys

import numpy as np
from isaacsim import SimulationApp

simulation_app = SimulationApp()

import omni
from isaacsim.core.utils.extensions import disable_extension, enable_extension

simulation_app.update()

enable_extension("semantics.schema.editor")
simulation_app.update()
disable_extension("semantics.schema.editor")
simulation_app.update()
enable_extension("omni.cuopt.examples")
simulation_app.update()
disable_extension("omni.cuopt.examples")
simulation_app.update()
enable_extension("omni.anim.people")
simulation_app.update()
disable_extension("omni.anim.people")
simulation_app.update()
# Cleanup application
simulation_app.close()
