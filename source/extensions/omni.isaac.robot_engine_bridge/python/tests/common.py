# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni
import carb
import numpy as np
from omni.isaac.pyalice import Codelet, Composite
import time
import logging


class PyaliceApp:
    def __init__(self):
        from omni.isaac.pyalice import Application
        from omni.isaac.pyalice.bindings import set_severity, severity

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.robot_engine_bridge")
        self._reb_extension_path = ext_manager.get_extension_path(ext_id)
        set_severity(severity.ERROR)
        self.app = Application(name="test", asset_path=self._reb_extension_path)
        self.app.logger.setLevel(logging.ERROR)
        self._stopped = True

    def run(self, duration: float = 1.0):
        self.app.start_wait_stop(duration)

    def start(self):
        self.app.start()
        self._stopped = False

    def stop(self):
        if self._stopped is False:
            self.app.stop()
            self._stopped = True
            time.sleep(2.0)

    def __del__(self):
        self.stop()


def create_application(json_file: str = "isaacsim.app.json"):
    ext_manager = omni.kit.app.get_app().get_extension_manager()
    ext_id = ext_manager.get_enabled_extension_id("omni.isaac.robot_engine_bridge")
    reb_extension_path = ext_manager.get_extension_path(ext_id)
    app_file = f"{reb_extension_path}/resources/isaac_engine/json/{json_file}"
    carb.log_info(f"create application with: {reb_extension_path} {app_file}")
    return omni.kit.commands.execute(
        "RobotEngineBridgeCreateApplication", asset_path=reb_extension_path, app_file=app_file
    )


class ConstantDiffBaseControl(Codelet):
    """
    Publish constant speed command
    """

    def start(self):
        self.tx = self.isaac_proto_tx("StateProto", "cmd")
        self.tick_periodically(0.05)

    def tick(self):
        ELEMENT_TYPE_F64 = 3
        tx_message = self.tx.init()
        pack = tx_message.proto.pack
        pack.elementType = ELEMENT_TYPE_F64
        sizes = pack.init("sizes", 3)
        sizes[0] = 1
        sizes[1] = 1
        sizes[2] = 2
        pack.scanlineStride = 0
        pack.dataBufferIndex = 0
        tx_message.buffers = [np.array([self.config.linear, self.config.rotation])]
        self.tx.publish()


class VehicleControl(Codelet):
    """
    Controls a REB vehicle
    """

    def start(self):
        self.tx = self.isaac_proto_tx("CompositeProto", "cmd")
        self._entities = [["body", "acceleration", 1], ["steering", "position", 1]]
        self.tick_periodically(0.05)

    def tick(self):
        values = np.array([self.config.accelerator, self.config.steering])
        self.tx._msg = Composite.create_composite_message(self._entities, values)
        self.tx.publish()


class BodyMonitor(Codelet):
    """Compares received velocity from diffbase and from rigidbody sink pose change (ground truth)"""

    def start(self):
        self.rx_bodies = self.isaac_proto_rx("RigidBody3GroupProto", "bodies")
        self.rx_state = self.isaac_proto_rx("StateProto", "state")
        self.tick_on_message(self.rx_state)
        self.position = None
        self.rotation = None
        self.acqtime = None
        self.threshold = 0.07

    def tick(self):
        # show state
        msg = self.rx_state.message
        print("MESSAGE", msg)
        if msg is None:
            return

        diff_state = msg.tensor[0][0]
        self.show("state.vt", diff_state[0])
        self.show("state.vr", diff_state[1])
        # msg = self.rx_bodies.message
        # p = msg.json["bodies"][0]["refTBody"]["translation"]
        # position = np.array([p["x"], p["y"]])
        # q = msg.json["bodies"][0]["refTBody"]["rotation"]["q"]
        # qw, qx, qy, qz = q["w"], q["x"], q["y"], q["z"]
        # cosq = 1.0 - (qx * qx + qy * qy + 2 * qz * qz)
        # sinq = 2.0 * qz * qw

        # rotation = np.arctan2(sinq, cosq)

        if self.acqtime is not None:
            # dt = (msg.acqtime - self.acqtime) * 1e-9
            # gt_v = [np.linalg.norm(position - self.position) / dt, (rotation - self.rotation) / dt]
            # self.logger.debug("linear speed (diffbase vs gt): {0:0.4f} / {1:0.4f}".format(diff_state[0], gt_v[0]))
            # self.logger.debug("angular speed (diffbase vs gt): {0:0.4f} / {" "1:0.4f}".format(diff_state[1], gt_v[1]))
            print(diff_state[0], diff_state[1])
            if (
                abs(diff_state[0] - self.config.linear_target) < self.threshold
                and abs(diff_state[1] - self.config.angular_target) < self.threshold
            ):
                self.config.check = True

        self.acqtime = msg.acqtime
        # self.position = position
        # self.rotation = rotation


def get_selected_path():
    selectedPrims = omni.usd.get_context().get_selection().get_selected_prim_paths()

    if len(selectedPrims) > 0:
        curr_prim = selectedPrims[-1]
    else:
        curr_prim = None
    return curr_prim


def add_cube(stage, path, size, offset, physics=False):
    from pxr import UsdPhysics, UsdGeom

    cubeGeom = UsdGeom.Cube.Define(stage, path)
    cubePrim = stage.GetPrimAtPath(path)

    cubeGeom.CreateSizeAttr(size)
    cubeGeom.AddTranslateOp().Set(offset)
    if physics:
        rigid_api = UsdPhysics.RigidBodyAPI.Apply(cubePrim)
        rigid_api.CreateRigidBodyEnabledAttr(True)

    UsdPhysics.CollisionAPI.Apply(cubePrim)

    return cubePrim


def create_physics_scene(stage, gravity=9.81):
    from pxr import UsdPhysics, PhysxSchema, Gf

    scene = UsdPhysics.Scene.Define(stage, "/physics/scene")
    scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
    scene.CreateGravityMagnitudeAttr().Set(gravity)

    PhysxSchema.PhysxSceneAPI.Apply(stage.GetPrimAtPath("/physics/scene"))
    physxSceneAPI = PhysxSchema.PhysxSceneAPI.Get(stage, "/physics/scene")
    physxSceneAPI.CreateEnableCCDAttr(True)
    physxSceneAPI.CreateEnableStabilizationAttr(True)
    physxSceneAPI.CreateEnableGPUDynamicsAttr(False)
    physxSceneAPI.CreateBroadphaseTypeAttr("MBP")
    physxSceneAPI.CreateSolverTypeAttr("TGS")
