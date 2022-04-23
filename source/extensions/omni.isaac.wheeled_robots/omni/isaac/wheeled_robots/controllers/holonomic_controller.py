# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


# Import packages.
from pickle import FALSE
import osqp
from scipy import sparse
import numpy as np
from numpy import linalg
from omni.isaac.core.prims.xform_prim import XFormPrim
from omni.isaac.core.robots.robot import Robot
from pxr import Usd, UsdGeom, UsdPhysics, Gf
import omni
import carb
from omni.isaac.core.utils.rotations import euler_to_rot_matrix
from omni.isaac.core.utils.math import cross
from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.core.controllers import BaseController

axis = {"X": Gf.Vec3d(1, 0, 0), "Y": Gf.Vec3d(0, 1, 0), "Z": Gf.Vec3d(0, 0, 1)}


class HolonomicController(BaseController):
    """[summary]
    Generic Holonomic drive controller. Model must have drive joints to mecanum wheels defined in the USD with the rollers angle and radius.
    Args:
        name (str): [description]
        articulation_root (UsdPrim): root of the robot articulation
        com_prim (Xformable):  Transform to the robot's center of mass, Used to compute the robot basis
    """

    def __init__(
        self,
        name: str,
        robot: Robot,
        com_prim: XFormPrim,
        max_linear_speed: float = 1.0e20,
        max_angular_speed: float = 1.0e20,
        max_wheel_speed: float = 1.0e20,
        linear_gain: float = 1.0,
        angular_gain: float = 1.0,
    ) -> None:
        super().__init__(name)
        self.articulation_root = robot
        self.com_prim = com_prim
        self.max_linear_speed = max_linear_speed
        self.max_angular_speed = max_angular_speed
        self.max_wheel_speed = (max_wheel_speed,)
        self.linear_gain = linear_gain
        self.angular_gain = angular_gain
        self.mecanum_joints = [
            j for j in Usd.PrimRange(self.articulation_root.prim) if j.GetAttribute("isaacmecanumwheel:angle")
        ]  # TODO Fix
        n = len(self.mecanum_joints)
        self.last_values = {i: 0.0 for i in self.mecanum_joints}
        self.wheel_radius = [j.GetAttribute("isaacmecanumwheel:radius").Get() for j in self.mecanum_joints]
        self.base_dir_array = np.zeros((3, n), dtype=float)
        self.wheel_dists_array = np.zeros((3, n), dtype=float)
        self.last_values = {j: float(0) for i, j in enumerate(self.mecanum_joints)}
        self.build_base()

        self.base_dir = self.base_dir_array
        self.wheel_dists = self.wheel_dists_array
        self.target_vel = [0.0, 0.0, 0.0]

        # Problem definition

        # min (x.T @ x)
        # s.t:
        #     V.T @ x == v_input
        #     cross(V,wheel_distances_to_com) @ x == w_input
        #

        self.P = sparse.csc_matrix(np.diag(self.wheel_radius) / np.linalg.norm(self.wheel_radius))
        self.b = sparse.csc_matrix(np.zeros((6, 1)))
        V = self.base_dir
        W = np.cross(V, self.wheel_dists, axis=0)
        self.A = sparse.csc_matrix(np.concatenate((V, W), axis=0))
        self.l = np.array([0.0, 0.0, -np.inf, -np.inf, -np.inf, 0.0])
        self.u = np.array([0.0, 0.0, np.inf, np.inf, np.inf, 0.0])

        self.prob = osqp.OSQP()

        self.prob.setup(self.P, A=self.A, l=self.l, u=self.u, verbose=False)

        self.prob.solve()

    def build_base(self):
        """
        Reads the kinematic structure from the robot, to find the distance relation from the wheels to the center of
        mass prim, and the `angle of attack` for each of the mecanum wheels, defined by the attribute `isaacmecanumwheel:angle`
        """
        base_pose = Gf.Matrix4f(omni.usd.utils.get_world_transform_matrix(self.com_prim.prim))
        stage = self.articulation_root.prim.GetStage()
        for i, j in enumerate(self.mecanum_joints):
            joint = UsdPhysics.RevoluteJoint(j)
            parent_prim = stage.GetPrimAtPath(joint.GetBody0Rel().GetTargets()[0])
            parent_pose = Gf.Matrix4f(omni.usd.utils.get_world_transform_matrix(parent_prim))
            p_0 = joint.GetLocalPos0Attr().Get()
            r_0 = joint.GetLocalRot0Attr().Get()
            local_0 = Gf.Matrix4f()
            local_0.SetTranslate(p_0)
            local_0.SetRotateOnly(r_0)
            joint_pose = local_0 * parent_pose
            mecanum_angle = j.GetAttribute("isaacmecanumwheel:angle").Get()
            mecanum_radius = j.GetAttribute("isaacmecanumwheel:radius").Get()
            m_rot = euler_to_rot_matrix(axis[UsdGeom.GetStageUpAxis(stage)] * mecanum_angle, True)
            j_axis = Gf.Vec3f(
                m_rot.TransformDir(joint_pose.TransformDir(axis[joint.GetAxisAttr().Get()]))
            ).GetNormalized()
            self.base_dir_array[0, i] = j_axis[0] / mecanum_radius
            self.base_dir_array[1, i] = j_axis[1] / mecanum_radius
            for k in range(2):
                self.wheel_dists_array[k, i] = 1 / (
                    (joint_pose.ExtractTranslation() - base_pose.ExtractTranslation())[k]
                )

    def forward(self, command: np.ndarray) -> ArticulationAction:
        """[summary]

        Args:
            command (np.ndarray): [forward_velocity, lateral_velocity, yaw_velocity].

        Returns:
            ArticulationAction: [description]
        """
        if isinstance(command, list):
            command = np.array(command)
        if command.shape[0] != 3:
            raise Exception("command should be of length 3")
        if (np.array(command) == 0).all():
            self.last_values = self.last_values = {j: float(0) for _, j in enumerate(self.mecanum_joints)}
            return ArticulationAction(joint_velocities=list(self.last_values.values()))

        v = np.array([command[0], command[1], 0]).reshape((3)) * self.linear_gain
        w = np.array([(command[2])]) * self.angular_gain

        if np.linalg.norm(v) > 0:
            v_norm = v / np.linalg.norm(v)
        else:
            v_norm = v

        if np.linalg.norm(v) > self.max_linear_speed:
            v = v_norm * self.max_linear_speed
        if np.linalg.norm(w) > self.max_angular_speed:
            w = w / abs(w) * np.array([self.max_angular_speed])

        self.l[0:2] = self.u[0:2] = v[0:2] / self.max_linear_speed
        self.l[-1] = self.u[-1] = w / self.max_linear_speed
        self.prob.update(l=self.l, u=self.u)
        res = None
        try:
            res = self.prob.solve()
        except Exception as e:
            carb.log_error("error:", e)

        if res is not None:
            values = res.x.reshape([res.x.shape[0]]) * self.max_linear_speed

            if np.max(np.abs(values)) > self.max_wheel_speed:
                m = np.max(np.abs(values))
                scale = self.max_wheel_speed / m
                values = values * scale
            self.last_values = {j: float(values[i]) for i, j in enumerate(self.mecanum_joints)}

        return ArticulationAction(joint_velocities=list(self.last_values.values()))
