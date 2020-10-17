import omni
from omni.isaac.dynamic_control import _dynamic_control
import omni.syntheticdata._syntheticdata as _synthetic_data

from pxr import UsdGeom, Gf, Sdf, Usd, PhysxSchema, PhysicsSchema, PhysicsSchemaTools, Semantics
import numpy as np


class Jetracer:
    def __init__(self, omni_kit):
        self.omni_kit = omni_kit
        nucleus_server = omni.kit.settings.get_settings_interface().get("/isaac/nucleus/default")
        self.usd_path = nucleus_server + "/Isaac/Robots/Jetracer/jetracer.usd"
        self.robot_prim = None
        self.dc = _dynamic_control.acquire_dynamic_control_interface()
        self.ar = None

    # rotation is in degrees
    def spawn(self, location, rotation):
        stage = self.omni_kit.get_stage()
        prefix = "/World/Robot/Jetracer"
        prim_path = omni.kit.utils.get_stage_next_free_path(stage, prefix, False)
        print(prim_path)
        self.robot_prim = stage.DefinePrim(prim_path, "Xform")
        self.robot_prim.GetReferences().AddReference(self.usd_path)
        xform = UsdGeom.Xformable(self.robot_prim)
        xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")
        mat = Gf.Matrix4d().SetTranslate(location)
        mat.SetRotateOnly(Gf.Rotation(Gf.Vec3d(0, 0, 1), rotation))
        xform_op.Set(mat)

        self.camera_path = prim_path + "/Jetracer/Vehicle/jetracer_camera"
        # self.camera_path = prim_path + "Vehicle/jetracer_camera"

    def teleport(self, location, rotation, settle=False):
        if self.ar is None:
            self.ar = self.dc.get_rigid_body(self.robot_prim.GetPath().pathString + "/Vehicle")
            self.chassis = self.ar
        self.dc.wake_up_rigid_body(self.ar)
        rot_quat = Gf.Rotation(Gf.Vec3d(0, 0, 1), rotation).GetQuaternion()

        tf = _dynamic_control.Transform(
            location,
            (rot_quat.GetImaginary()[0], rot_quat.GetImaginary()[1], rot_quat.GetImaginary()[2], rot_quat.GetReal()),
        )
        self.dc.set_rigid_body_pose(self.chassis, tf)
        self.dc.set_rigid_body_linear_velocity(self.chassis, [0, 0, 0])
        self.dc.set_rigid_body_angular_velocity(self.chassis, [0, 0, 0])
        self.command((0, 0))
        if settle:
            frame = 0
            velocity = 1
            print("Settling robot...")
            while velocity > 0.1 and frame < 120:
                self.omni_kit.update(1.0 / 60.0)
                lin_vel = self.dc.get_rigid_body_linear_velocity(self.chassis)
                velocity = np.linalg.norm([lin_vel.x, lin_vel.y, lin_vel.z])
                # print("velocity magnitude is: ", velocity)
                frame = frame + 1
            # print("done after frame: HERE", frame)

    def activate_camera(self):
        vpi = omni.kit.viewport.get_viewport_interface()
        vpi.get_viewport_window().set_active_camera(str(self.camera_path))

    def command(self, motor_value):
        if self.ar is None:
            vehicle_path = self.robot_prim.GetPath().pathString + "/Jetracer/Vehicle"
            print(vehicle_path)
            self.ar = self.dc.get_rigid_body(vehicle_path)
            self.chassis = self.ar
            print(self.chassis)

            stage = self.omni_kit.get_stage()

            # for child_prim in stage.Traverse():
            #     print(child_prim.GetPath().pathString)

            self.accelerator = stage.GetPrimAtPath(vehicle_path).GetAttribute("physxVehicleController:accelerator")
            self.left_steer = stage.GetPrimAtPath(vehicle_path).GetAttribute("physxVehicleController:steerLeft")
            # LOCMOD add brake physxVehicleController:brake

        self.dc.wake_up_rigid_body(self.ar)
        accel_cmd = self.wheel_speed_from_motor_value(motor_value[0])
        steer_left_cmd = self.wheel_speed_from_motor_value(motor_value[1])

        # self.accelerator.Set(np.clip(accel_cmd, -10, 10))
        # self.left_steer.Set(np.clip(steer_left_cmd, -10, 10))

        self.accelerator.Set(max(min(accel_cmd, 1), -1))
        self.left_steer.Set(max(min(steer_left_cmd, 1), -1))

    # idealized motor model that converts a pwm value to a velocity
    def wheel_speed_from_motor_value(self, input):
        threshold = 0.05
        if input >= 0:
            if input > threshold:
                return 1.604 * input - 0.05
            else:
                return 0
        elif input < 0:
            if input < -threshold:
                return 1.725 * input + 0.0757
            else:
                return 0

    def observations(self):
        if self.ar is None:
            self.ar = self.dc.get_rigid_body(self.robot_prim.GetPath().pathString + "/Vehicle")
            self.chassis = self.ar
        dc_pose = self.dc.get_rigid_body_pose(self.chassis)
        dc_lin_vel = self.dc.get_rigid_body_linear_velocity(self.chassis)
        dc_local_lin_vel = self.dc.get_rigid_body_local_linear_velocity(self.chassis)
        dc_ang_vel = self.dc.get_rigid_body_angular_velocity(self.chassis)
        return {
            "pose": (dc_pose.p.x, dc_pose.p.y, dc_pose.p.z, dc_pose.r.w, dc_pose.r.x, dc_pose.r.y, dc_pose.r.z),
            "linear_velocity": (dc_lin_vel.x, dc_lin_vel.y, dc_lin_vel.z),
            "local_linear_velocity": (dc_local_lin_vel.x, dc_local_lin_vel.y, dc_local_lin_vel.z),
            "angular_velocity": (dc_ang_vel.x, dc_ang_vel.y, dc_ang_vel.z),
        }
