# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Tests for NuRec stage detection (is_nurec_stage)."""

import omni.kit.test
from isaacsim.replicator.experimental.mobility_gen.impl.nurec_overrides import is_nurec_stage
from pxr import Sdf, Usd, UsdGeom


class TestIsNurecStage(omni.kit.test.AsyncTestCase):
    """is_nurec_stage detects particle-field and volume NuRec scenes, nothing else.

    Markers verified against the galileo sample scenes: particle splats use a
    ``ParticleField*`` prim type; NuRec volumes use ``OmniNuRecFieldAsset`` field
    prims under a ``Volume`` flagged with ``omni:nurec:isNuRecVolume``.
    """

    async def test_none_is_not_nurec(self):
        self.assertFalse(is_nurec_stage(None))

    async def test_plain_mesh_is_not_nurec(self):
        stage = Usd.Stage.CreateInMemory()
        UsdGeom.Mesh.Define(stage, "/World/Mesh")
        self.assertFalse(is_nurec_stage(stage))

    async def test_particle_field_is_nurec(self):
        stage = Usd.Stage.CreateInMemory()
        stage.DefinePrim("/World/Splats", "ParticleFieldEmissive")
        self.assertTrue(is_nurec_stage(stage))

    async def test_volume_field_type_is_nurec(self):
        stage = Usd.Stage.CreateInMemory()
        stage.DefinePrim("/World/Volume/density_field", "OmniNuRecFieldAsset")
        self.assertTrue(is_nurec_stage(stage))

    async def test_volume_flag_attr_is_nurec(self):
        stage = Usd.Stage.CreateInMemory()
        prim = stage.DefinePrim("/World/Volume", "Volume")
        prim.CreateAttribute("omni:nurec:isNuRecVolume", Sdf.ValueTypeNames.Bool).Set(True)
        self.assertTrue(is_nurec_stage(stage))

    async def test_volume_flag_false_is_not_nurec(self):
        stage = Usd.Stage.CreateInMemory()
        prim = stage.DefinePrim("/World/Volume", "Volume")
        prim.CreateAttribute("omni:nurec:isNuRecVolume", Sdf.ValueTypeNames.Bool).Set(False)
        self.assertFalse(is_nurec_stage(stage))
