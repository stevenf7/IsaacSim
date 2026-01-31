# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
import asyncio

import isaacsim.core.experimental.utils.prim as prim_utils
import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
import omni.graph.core as og
import omni.kit.commands
import omni.kit.test
import omni.timeline
import usdrt.Sdf
from isaacsim.core.experimental.objects import Cube, GroundPlane
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim
from isaacsim.core.simulation_manager import SimulationManager
from pxr import PhysxSchema

from .common import step_simulation


class TestContactSensorOgn(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        await stage_utils.create_new_stage_async()
        physics_rate = 60
        SimulationManager.setup_simulation(dt=1.0 / physics_rate)
        self._timeline = omni.timeline.get_timeline_interface()
        await self.setup_environment()
        await self.setup_ogn()

    async def tearDown(self):
        if self._timeline.is_playing():
            self._timeline.stop()
        SimulationManager.invalidate_physics()
        await omni.kit.app.get_app().next_update_async()
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            # print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        await omni.kit.app.get_app().next_update_async()

    async def setup_environment(self):
        GroundPlane("/World/GroundPlane", positions=[0.0, 0.0, 0.0])
        Cube("/World/Cube", sizes=1.0, positions=[0.0, 0.0, 1.0])
        GeomPrim("/World/Cube", apply_collision_apis=True)
        RigidPrim("/World/Cube", masses=[1.0])
        contact_report_api = PhysxSchema.PhysxContactReportAPI.Apply(prim_utils.get_prim_at_path("/World/Cube"))
        contact_report_api.CreateThresholdAttr().Set(0)
        omni.kit.commands.execute(
            "IsaacSensorCreateContactSensor",
            path="/contact_sensor",
            parent="/World/Cube",
            max_threshold=10000000,
        )

    async def setup_ogn(self):
        self.graph_path = "/TestGraph"
        self.prim_path = "/World/Cube/contact_sensor"

        if prim_utils.get_prim_at_path(self.graph_path).IsValid():
            stage_utils.delete_prim(self.graph_path)

        keys = og.Controller.Keys
        try:
            og.Controller.edit(
                {"graph_path": self.graph_path, "evaluator_name": "execution"},
                {
                    keys.CREATE_NODES: [
                        ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                        ("ReadContactNode", "isaacsim.sensors.physics.IsaacReadContactSensor"),
                    ],
                    keys.CONNECT: [
                        ("OnPlaybackTick.outputs:tick", "ReadContactNode.inputs:execIn"),
                    ],
                    keys.SET_VALUES: [
                        (
                            "ReadContactNode.inputs:csPrim",
                            [usdrt.Sdf.Path("/World/Cube/contact_sensor")],
                        ),
                    ],
                },
            )
        except Exception as e:
            print(e)

    # verifying force value and sensor time are non-zero in valid case
    async def test_valid_contact_sensor_ogn(self):
        """Verify non-zero outputs for a valid contact sensor prim."""
        # must play, stop, and play simulation for force value to be properly recorded
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        await step_simulation(1.0)

        force_value = og.Controller.attribute(self.graph_path + "/ReadContactNode.outputs:value").get()
        self.assertNotEqual(force_value, 0.0)

        sensor_time = og.Controller.attribute(self.graph_path + "/ReadContactNode.outputs:sensorTime").get()
        self.assertNotEqual(sensor_time, 0.0)

    # verifying force value and sensor time equal zero for invalid case
    async def test_invalid_contact_sensor_ogn(self):
        """Verify outputs are zero for an invalid contact sensor prim."""
        og.Controller.set(
            og.Controller.attribute(self.graph_path + "/ReadContactNode.inputs:csPrim"), [usdrt.Sdf.Path("/World/Cube")]
        )
        self._timeline.play()
        await step_simulation(0.5)
        force_val = og.Controller.attribute(self.graph_path + "/ReadContactNode.outputs:value").get()
        self.assertEqual(force_val, 0.0)

        sensor_time = og.Controller.attribute(self.graph_path + "/ReadContactNode.outputs:sensorTime").get()
        self.assertEqual(sensor_time, 0.0)
