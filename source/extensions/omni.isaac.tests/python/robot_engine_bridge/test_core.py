# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit.asyncapi
import omni.kit.usd
import carb.tokens
import os
import asyncio

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
import omni.isaac.RobotEngineBridgeSchema as REBSchema
from omni.isaac.robot_engine_bridge import _robot_engine_bridge
from omni.isaac.utils.scripts.test_utils import load_test_file
from .common import setup_base_prim

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestREB(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await omni.kit.asyncapi.new_stage()
        self._timeline = omni.timeline.get_timeline_interface()
        self._usd_context = omni.usd.get_context()
        self._stage = self._usd_context.get_stage()
        self._re_bridge = _robot_engine_bridge.acquire_robot_engine_bridge_interface()
        pass

    # After running each test
    async def tearDown(self):
        pass

    def create_application(self):
        json_path = os.path.abspath(
            carb.tokens.get_tokens_interface().resolve(
                "${app}/../exts/omni.isaac.robot_engine_bridge/resources/isaac_engine/json/isaacsim.app.json"
            )
        )
        asset_path = os.path.abspath(
            carb.tokens.get_tokens_interface().resolve("${app}/../exts/omni.isaac.robot_engine_bridge/")
        )
        print("create application with: ", asset_path, json_path)
        self._re_bridge.create_application(asset_path, json_path, [], [])

    # Create and destroy the app
    async def test_spawn_reb_init(self):
        # Base create destroy test
        self.create_application()
        self._re_bridge.destroy_application()

        # Create after play
        self._timeline.play()
        self.create_application()
        await asyncio.sleep(0.5)
        self._timeline.stop()
        self._re_bridge.destroy_application()

        # Create before play
        self.create_application()
        self._timeline.play()
        await asyncio.sleep(0.5)
        self._re_bridge.destroy_application()
        self._timeline.stop()

    # This test spawns all REB components and then runs simulation
    async def test_spawn_reb_stopped(self):

        path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_DifferentialBase", True)
        prim = REBSchema.RobotEngineDifferentialBase.Define(self._stage, path)
        setup_base_prim(prim)

        path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_HolonomicBase", True)
        prim = REBSchema.RobotEngineHolonomicBase.Define(self._stage, path)
        setup_base_prim(prim)

        path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_Vehicle", True)
        prim = REBSchema.RobotEngineVehicle.Define(self._stage, path)
        setup_base_prim(prim)

        path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_JointControl", True)
        prim = REBSchema.RobotEngineJointControl.Define(self._stage, path)
        setup_base_prim(prim)

        path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_ScissorLiftSimulator", True)
        prim = REBSchema.RobotEngineScissorLift.Define(self._stage, path)
        setup_base_prim(prim)

        path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_SurfaceGripper", True)
        prim = REBSchema.RobotEngineSurfaceGripper.Define(self._stage, path)
        setup_base_prim(prim)

        path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_TwoFingerGripper", True)
        prim = REBSchema.RobotEngineTwoFingerGripper.Define(self._stage, path)
        setup_base_prim(prim)

        path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_RigidBodiesSink", True)
        prim = REBSchema.RobotEngineRigidBodySink.Define(self._stage, path)
        setup_base_prim(prim)

        path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_Teleport", True)
        prim = REBSchema.RobotEngineTeleport.Define(self._stage, path)
        setup_base_prim(prim)

        path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_ScenarioFromMessage", True)
        prim = REBSchema.RobotEngineScenarioFromMessage.Define(self._stage, path)
        setup_base_prim(prim)

        path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_Camera", True)
        prim = REBSchema.RobotEngineCamera.Define(self._stage, path)
        setup_base_prim(prim)

        path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_Lidar", True)
        prim = REBSchema.RobotEngineLidar.Define(self._stage, path)
        setup_base_prim(prim)
        self.create_application()
        self._timeline.play()
        await asyncio.sleep(0.125)
        # await omni.kit.asyncapi.next_update()
        self._timeline.stop()
        self._re_bridge.destroy_application()

        pass

    async def test_spawn_reb_active(self):
        self.create_application()
        self._timeline.play()
        path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_DifferentialBase", True)
        prim = REBSchema.RobotEngineDifferentialBase.Define(self._stage, path)
        setup_base_prim(prim)

        path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_HolonomicBase", True)
        prim = REBSchema.RobotEngineHolonomicBase.Define(self._stage, path)
        setup_base_prim(prim)

        path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_Vehicle", True)
        prim = REBSchema.RobotEngineVehicle.Define(self._stage, path)
        setup_base_prim(prim)

        path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_JointControl", True)
        prim = REBSchema.RobotEngineJointControl.Define(self._stage, path)
        setup_base_prim(prim)

        path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_ScissorLiftSimulator", True)
        prim = REBSchema.RobotEngineScissorLift.Define(self._stage, path)
        setup_base_prim(prim)

        path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_SurfaceGripper", True)
        prim = REBSchema.RobotEngineSurfaceGripper.Define(self._stage, path)
        setup_base_prim(prim)

        path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_TwoFingerGripper", True)
        prim = REBSchema.RobotEngineTwoFingerGripper.Define(self._stage, path)
        setup_base_prim(prim)

        path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_RigidBodiesSink", True)
        prim = REBSchema.RobotEngineRigidBodySink.Define(self._stage, path)
        setup_base_prim(prim)

        path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_Teleport", True)
        prim = REBSchema.RobotEngineTeleport.Define(self._stage, path)
        setup_base_prim(prim)

        path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_ScenarioFromMessage", True)
        prim = REBSchema.RobotEngineScenarioFromMessage.Define(self._stage, path)
        setup_base_prim(prim)

        path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_Camera", True)
        prim = REBSchema.RobotEngineCamera.Define(self._stage, path)
        setup_base_prim(prim)

        path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_Lidar", True)
        prim = REBSchema.RobotEngineLidar.Define(self._stage, path)
        setup_base_prim(prim)

        await asyncio.sleep(2)
        await omni.kit.asyncapi.next_update()
        self._timeline.stop()
        self._re_bridge.destroy_application()
        await asyncio.sleep(2)
        await omni.kit.asyncapi.next_update()
        pass
