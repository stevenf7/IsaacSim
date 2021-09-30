# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit.usd
import gc
import carb

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
import omni.kit.commands
from .common import get_selected_path, simulate
from omni.isaac.core.utils.nucleus_utils import find_nucleus_server

from pxr import Gf, UsdPhysics, PhysxSchema


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestGXFCommands(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        self._timeline = omni.timeline.get_timeline_interface()
        self._stage = omni.usd.get_context().get_stage()
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.robot_engine_bridge_gxf")
        self._reb_extension_path = ext_manager.get_extension_path(ext_id)

        scene = UsdPhysics.Scene.Define(self._stage, "/physics/scene")
        scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
        scene.CreateGravityMagnitudeAttr().Set(9.81)

        PhysxSchema.PhysxSceneAPI.Apply(self._stage.GetPrimAtPath("/physics/scene"))
        physxSceneAPI = PhysxSchema.PhysxSceneAPI.Get(self._stage, "/physics/scene")
        physxSceneAPI.CreateEnableCCDAttr(True)
        physxSceneAPI.CreateEnableStabilizationAttr(True)
        physxSceneAPI.CreateEnableGPUDynamicsAttr(False)
        physxSceneAPI.CreateBroadphaseTypeAttr("MBP")
        physxSceneAPI.CreateSolverTypeAttr("TGS")

        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return
        self._nucleus_path = nucleus_server + "/Isaac"

        pass

    # After running each test
    async def tearDown(self):
        self._stage = None
        self._timeline = None
        gc.collect()
        pass

    async def test_command_tick(self):
        result, status = omni.kit.commands.execute(
            "RobotEngineBridgeGxfCreateApplication",
            base_path=self._reb_extension_path + "/lib",
            manifest_file="manifest.yaml",
            graph_files=[
                f"{self._reb_extension_path}/data/test/vehicle_control_forward.yaml",
                self._reb_extension_path + "/data/config/isaac_sim_allocator.yaml",
            ],
        )
        self._timeline.play()
        await simulate(1)
        result, prim = omni.kit.commands.execute("RobotEngineBridgeCreateLidar", path="/REB_Lidar", enabled=False)
        await simulate(1)
        # first frame is skipped sowe tick twice
        self.assertTrue(omni.kit.commands.execute("RobotEngineBridgeGxfTickComponent", path="/REB_Lidar")[1])
        self.assertTrue(omni.kit.commands.execute("RobotEngineBridgeGxfTickComponent", path="/REB_Lidar")[1])
        self.assertFalse(omni.kit.commands.execute("RobotEngineBridgeGxfTickComponent", path="/REB_DOESNT_EXIST")[1])
        await simulate(0.25)
        self.assertTrue(omni.kit.commands.execute("RobotEngineBridgeGxfDestroyApplication")[1])
        self._timeline.stop()
