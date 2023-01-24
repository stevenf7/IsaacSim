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
import carb.tokens
import gc
import asyncio

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.dynamic_control import _dynamic_control

from omni.isaac.core.utils.stage import open_stage_async
from omni.isaac.core.utils.nucleus import get_assets_root_path
from .common import PyaliceApp, create_application
from omni.isaac.pyalice import Composite
from omni.isaac.core.utils.physics import simulate_async

from pxr import Gf, UsdGeom, PhysicsSchemaTools
import numpy as np


def set_translate(prim, new_loc):
    properties = prim.GetPropertyNames()
    if "xformOp:translate" in properties:
        translate_attr = prim.GetAttribute("xformOp:translate")

        translate_attr.Set(new_loc)
    elif "xformOp:translation" in properties:
        translation_attr = prim.GetAttribute("xformOp:translate")
        translation_attr.Set(new_loc)
    elif "xformOp:transform" in properties:
        transform_attr = prim.GetAttribute("xformOp:transform")
        matrix = prim.GetAttribute("xformOp:transform").Get()
        matrix.SetTranslateOnly(new_loc)
        transform_attr.Set(matrix)
    else:
        xform = UsdGeom.Xformable(prim)
        xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")
        xform_op.Set(Gf.Matrix4d().SetTranslate(new_loc))


def set_rotate(prim, rot_mat):
    properties = prim.GetPropertyNames()
    if "xformOp:rotate" in properties:
        rotate_attr = prim.GetAttribute("xformOp:rotate")
        rotate_attr.Set(rot_mat)
    elif "xformOp:transform" in properties:
        transform_attr = prim.GetAttribute("xformOp:transform")
        matrix = prim.GetAttribute("xformOp:transform").Get()
        matrix.SetRotateOnly(rot_mat.ExtractRotation())
        transform_attr.Set(matrix)
    else:
        xform = UsdGeom.Xformable(prim)
        xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")
        xform_op.Set(Gf.Matrix4d().SetRotate(rot_mat))


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestREBPyaliceSurfaceGripper(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        self._timeline = omni.timeline.get_timeline_interface()
        self._usd_context = omni.usd.get_context()
        self._dc = _dynamic_control.acquire_dynamic_control_interface()

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.robot_engine_bridge")
        self._reb_extension_path = ext_manager.get_extension_path(ext_id)

        self._asset_path = self._reb_extension_path

        self._assets_root_path = get_assets_root_path()
        if self._assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return

        self.assertTrue(create_application()[1])

        self._physics_rate = 60
        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(self._physics_rate))
        carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(self._physics_rate))
        await omni.kit.app.get_app().next_update_async()

        pass

    # After running each test
    async def tearDown(self):
        self.assertTrue(omni.kit.commands.execute("RobotEngineBridgeDestroyApplication")[1])
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        gc.collect()
        pass

    async def test_klt_grasping(self):
        states = {}
        states["bin_1"] = {
            "grab": [-3.6246972, -1.9399462, -1.9311233, -0.8515033, 1.5707023, -0.48315188],
            "lift": [-3.624738, -1.7179015, -1.6415617, -1.364, 1.570694, -0.48314723],
        }
        states["bin_2"] = {
            "grab": [-2.2353225, -1.7653593, -1.7642521, -1.1936475, 1.5708172, 0.9060481],
            "lift": [-2.2353387, -1.717932, -1.6415195, -1.3640339, 1.5708125, 0.9060407],
        }
        states["bin_3"] = {
            "grab": [-3.4586642, -2.3406546, -0.99169415, -1.3797174, 1.5731614, -0.31733325],
            "lift": [-3.4579735, -2.3299344, -0.75304776, -1.6444204, 1.5707126, -0.3164174],
        }
        (result, error) = await open_stage_async(
            self._assets_root_path + "/Isaac/Samples/Isaac_SDK/Robots/UR10_Long_Suction_REB.usd"
        )
        self.assertTrue(result)

        stage = omni.usd.get_context().get_stage()

        PhysicsSchemaTools.addGroundPlane(stage, "/World/groundPlane", "Z", 1500, Gf.Vec3f(0, 0, 0), Gf.Vec3f(0.5))

        self.assertTrue(result)

        binPrim = stage.DefinePrim("/World/bin_1", "Xform")
        binPrim.GetReferences().AddReference(self._assets_root_path + "/Isaac/Props/KLT_Bin/small_KLT.usd")
        set_translate(binPrim, (60, -50, 20))
        set_rotate(binPrim, Gf.Matrix3d(Gf.Rotation((1, 0, 0), 0)))

        binPrim = stage.DefinePrim("/World/bin_2", "Xform")
        binPrim.GetReferences().AddReference(self._assets_root_path + "/Isaac/Props/KLT_Bin/small_KLT.usd")
        set_translate(binPrim, (60, 50, 20))
        set_rotate(binPrim, Gf.Matrix3d(Gf.Rotation((0, 1, 0), -90)))

        binPrim = stage.DefinePrim("/World/bin_3", "Xform")
        binPrim.GetReferences().AddReference(self._assets_root_path + "/Isaac/Props/KLT_Bin/small_KLT.usd")
        set_translate(binPrim, (100, -50, 20))
        set_rotate(binPrim, Gf.Matrix3d(Gf.Rotation((0, 1, 0), 180)))

        self._timeline.play()

        await omni.kit.app.get_app().next_update_async()

        test_app = PyaliceApp()
        test_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )
        sim_in = test_app.app.nodes["simulation.interface"]["input"]
        sim_out = test_app.app.nodes["simulation.interface"]["output"]

        test_app.start()
        # Run test so tcp is connected
        await simulate_async(1)

        handle_1 = self._dc.get_rigid_body("/World/bin_1")
        handle_2 = self._dc.get_rigid_body("/World/bin_2")
        handle_3 = self._dc.get_rigid_body("/World/bin_3")
        self.assertLess(self._dc.get_rigid_body_pose(handle_1).p.z, 10)
        self.assertLess(self._dc.get_rigid_body_pose(handle_2).p.z, 10)
        self.assertLess(self._dc.get_rigid_body_pose(handle_3).p.z, 10)

        def send_close_message():
            close_gripper = Composite.create_composite_message(
                [["gripper", "none", 1]], np.array([1.0], dtype=np.dtype("float64"))
            )
            test_app.app.publish("simulation.interface", "input", "io_command", close_gripper)

        def send_open_message():
            open_gripper = Composite.create_composite_message(
                [["gripper", "none", 1]], np.array([0.0], dtype=np.dtype("float64"))
            )
            test_app.app.publish("simulation.interface", "input", "io_command", open_gripper)

        joints = [
            "shoulder_pan_joint",
            "shoulder_lift_joint",
            "elbow_joint",
            "wrist_1_joint",
            "wrist_2_joint",
            "wrist_3_joint",
        ]
        quantities = [[x, "position", 1] for x in joints]

        def send_joint_message(angles):
            values = np.array(angles, dtype=np.dtype("float64"))
            cmd_msg = Composite.create_composite_message(quantities, values)
            test_app.app.publish("simulation.interface", "input", "joint_position", cmd_msg)

        # Run test for a while for the arm to move
        # For each bin we go to its lifting pose, come down, grab, lift and release
        send_joint_message(states["bin_1"]["lift"])
        send_open_message()
        await simulate_async(4)
        send_joint_message(states["bin_1"]["grab"])
        await simulate_async(2)
        send_close_message()
        await simulate_async(2)
        send_joint_message(states["bin_1"]["lift"])
        await simulate_async(2)
        self.assertGreater(self._dc.get_rigid_body_pose(handle_1).p.z, 10)

        send_open_message()
        await simulate_async(2)
        send_joint_message(states["bin_2"]["lift"])
        await simulate_async(2)
        send_joint_message(states["bin_2"]["grab"])
        await simulate_async(2)
        send_close_message()
        await simulate_async(2)
        send_joint_message(states["bin_2"]["lift"])
        await simulate_async(2)
        self.assertGreater(self._dc.get_rigid_body_pose(handle_2).p.z, 10)

        send_open_message()
        await simulate_async(2)
        send_joint_message(states["bin_3"]["lift"])
        await simulate_async(2)
        send_joint_message(states["bin_3"]["grab"])
        await simulate_async(2)
        send_close_message()
        await simulate_async(2)
        send_joint_message(states["bin_3"]["lift"])
        await simulate_async(2)
        self.assertGreater(self._dc.get_rigid_body_pose(handle_3).p.z, 10)

        send_open_message()
        await simulate_async(2)
        self._timeline.stop()
        test_app.stop()
        test_app = None

        pass
