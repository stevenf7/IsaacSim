# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import carb
from pxr import UsdGeom, Gf, UsdPhysics, Sdf, UsdLux
import omni.ext
import omni.usd
import omni.kit.settings

from omni.isaac.motion_planning import _motion_planning
from omni.isaac.dynamic_control import _dynamic_control
import omni.physx as _physx

from omni.physx.scripts.physicsUtils import add_ground_plane
from omni.isaac.samples.scripts.utils.franka import Franka, default_config

from omni.isaac.samples.scripts.utils.world import World
from omni.isaac.samples.scripts.utils.reactive_behavior import FrameTerminationCriteria
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server
from omni.isaac.utils.scripts.scene_utils import set_translate, set_up_z_axis, setup_physics

import numpy as np
import os
import asyncio


def create_prim_from_usd(stage, prim_env_path, prim_usd_path, location):
    envPrim = stage.DefinePrim(prim_env_path, "Xform")  # create an empty Xform at the given path
    envPrim.GetReferences().AddReference(prim_usd_path)  # attach the USD to the given path
    set_translate(envPrim, location)  # set pose


class RMPSample:
    def __init__(self):
        self._timeline = omni.timeline.get_timeline_interface()

        self._mp = _motion_planning.acquire_motion_planning_interface()
        self._dc = _dynamic_control.acquire_dynamic_control_interface()

        self._physxIFace = _physx.acquire_physx_interface()

        self.first_step = True
        self.following = False  # is the task running
        self.created = False
        self.obstacle_on = False  # is the obstacle active
        self.gripper_open = False
        self._block_prim = None
        self._target = None
        self._robot = None
        self._world = None
        self._save_data = False
        self._save_dir = None
        self._ar = _dynamic_control.INVALID_HANDLE
        self._termination_criteria = FrameTerminationCriteria(orig_thresh=0.001)

    def create_robot(self):
        """ load robot from USD
        """

        self._stage = omni.usd.get_context().get_stage()
        self._ar = _dynamic_control.INVALID_HANDLE

        ## unit conversions: RMP is in meters, kit is by default in cm
        self._meters_per_unit = UsdGeom.GetStageMetersPerUnit(self._stage)
        self._units_per_meter = 1.0 / UsdGeom.GetStageMetersPerUnit(self._stage)

        set_up_z_axis(self._stage)
        add_ground_plane(self._stage, "/physics/groundPlane", "Z", 1000.0, Gf.Vec3f(0.0), Gf.Vec3f(1.0))
        setup_physics(self._stage)

        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return
        asset_path = nucleus_server + "/Isaac"
        robot_usd = asset_path + "/Robots/Franka/franka.usd"
        robot_path = "/scene/robot"
        create_prim_from_usd(self._stage, robot_path, robot_usd, Gf.Vec3d(0, 0, 0))

        # self._physxIFace.release_physics_objects()
        # self._physxIFace.force_load_physics_from_usd()

        light_prim = UsdLux.DistantLight.Define(self._stage, Sdf.Path("/World/defaultLight"))
        light_prim.CreateIntensityAttr(500)

        self.first_step = True
        self.following = False
        self.robot = None
        self.created = True

    def register_assets(self):
        # register world with RMP
        self._world = World(self._dc, self._mp)

        # register robot with RMP
        robot_path = "/scene/robot"
        self._robot = Franka(
            self._stage, self._stage.GetPrimAtPath(robot_path), self._dc, self._mp, self._world, default_config
        )

    def step(self, step):
        """This function is called every timestep in the editor
        
        Arguments:
            step (float): elapsed time between steps
        """
        if self.created and self._timeline.is_playing():
            if self.first_step:
                self.register_assets()
                self.first_step = False
            if self.following:
                target_mat = self._target_prim.GetAttribute("xformOp:transform").Get()
                target_pos = target_mat.ExtractTranslation()
                target_rot = target_mat.ExtractRotationMatrix()

                # go to target by specify translation and orientation of the final pose
                # note: not all axes needs to be specified. Two is enough completely constrain the motion, or just use one for partial pose constraints.
                self._target = {
                    "orig": np.array([target_pos[0], target_pos[1], target_pos[2]]) * self._meters_per_unit,
                    "axis_x": np.array(-target_rot[0]),
                    "axis_y": np.array(target_rot[1]),
                    "axis_z": np.array(-target_rot[2]),
                }
                self._robot.end_effector.go_local(target=self._target, use_default_config=True, wait_for_target=True)

            # update RMP's world and robot states to sync with Kit
            self._world.update()
            self._robot.update()

            if self._save_data:
                self.collect_action_state()

    def follow_target(self):
        # create target
        target_path = "/scene/target"
        if not self._stage.GetPrimAtPath(target_path):
            target_geom = UsdGeom.Cube.Define(self._stage, target_path)
            offset = Gf.Vec3d(30, 0.0, 30.0)  # these are in cm
            mat = Gf.Matrix4d().SetTranslate(offset)
            colors = Gf.Vec3f(1.0, 0, 0)
            target_size = 8
            target_geom.CreateSizeAttr(target_size)
            target_geom.AddTransformOp().Set(mat)
            target_geom.CreateDisplayColorAttr().Set([colors])
            self._target_prim = self._stage.GetPrimAtPath(target_path)

        # start following it
        self.following = True

    def add_obstacle(self):
        if self._world is None:
            return
        # set ground as an obstacles in RMP
        self._world.register_object(0, "/physics/groundPlane/CollisionPlane", "ground")
        self._world.make_obstacle(
            "ground", 3, (500 * self._meters_per_unit, 500 * self._meters_per_unit, 10 * self._meters_per_unit)
        )

        # add a block in Kit
        self._block_path = "/scene/block"
        size = 10
        if not self._stage.GetPrimAtPath(self._block_path):
            self._block_geom = UsdGeom.Cube.Define(self._stage, self._block_path)
            offset = Gf.Vec3f(30, -20, 5)
            obstacle_color = Gf.Vec3f(1.0, 1.0, 0)

            self._block_geom.CreateSizeAttr(size)
            self._block_geom.AddTranslateOp().Set(offset)
            self._block_geom.CreateDisplayColorAttr().Set([obstacle_color])
            self._block_prim = self._stage.GetPrimAtPath(self._block_path)

            async def setup_block_physics():
                await omni.kit.app.get_app().next_update_async()
                # make this obstacle a rigid body with physics and collision properties
                UsdPhysics.RigidBodyAPI.Apply(self._block_prim)
                await omni.kit.app.get_app().next_update_async()
                UsdPhysics.CollisionAPI.Apply(self._block_prim)
                massAPI = UsdPhysics.MassAPI.Apply(self._block_prim)
                massAPI.CreateMassAttr(0.08)

            asyncio.ensure_future(setup_block_physics())

        self._block_prim = self._stage.GetPrimAtPath(self._block_path)
        # set the block as an obstacle in RMP
        self._world.register_object(0, self._block_path, "block")
        self._world.make_obstacle(
            "block", 3, (size * self._meters_per_unit, size * self._meters_per_unit, size * self._meters_per_unit)
        )

        self.obstacle_on = True

    def toggle_obstacle(self):
        """an obstacle can be temporarily suppressed so that the collision avoidance algorithm ignores it. This can be useful if you need to get very close to an object.
        """
        if self._world is None:
            return
        try:
            block_suppressor = self._world.get_object_from_name("block")
        except KeyError:
            print("Please Press Add Obstacles Button")
            return
        invisible_color = Gf.Vec3f(0.0, 0.0, 1.0)
        obstacle_color = Gf.Vec3f(1.0, 1.0, 0)

        if self.obstacle_on:
            block_suppressor.suppress()
            self._block_geom.GetDisplayColorAttr().Set([invisible_color])
            self.obstacle_on = False
        else:
            block_suppressor.unsuppress()
            self._block_geom.GetDisplayColorAttr().Set([obstacle_color])
            self.obstacle_on = True

    def toggle_gripper(self):
        if self._robot is None:
            return
        if self.gripper_open:
            print("closing gripper")
            self._robot.end_effector.gripper.close()
            self.gripper_open = False
        else:
            print("opening gripper")
            self._robot.end_effector.gripper.open()
            self.gripper_open = True

    def reset(self):
        self.following = False
        if self._robot is not None:
            # put robot (an articulated prim) in a specific joint configuration
            reset_config = np.array([0.00, -1.3, 0.00, -2.57, 0.00, 2.20, 0.75])
            self._robot.send_config(reset_config)
            self._robot.end_effector.go_local(use_default_config=True, wait_for_target=False)
            self._robot.end_effector.gripper.close()
            self.gripper_open = False

        # put target back (a visual prim) in position
        if self._target:
            reset_orig = Gf.Vec3d(30.0, 0.0, 30)
            reset_rot = Gf.Matrix3d(1.0)
            reset_mat = Gf.Matrix4d(reset_rot, reset_orig)
            self._target_prim.GetAttribute("xformOp:transform").Set(reset_mat)

        # put obstacle block (a rigid body prim) back in position
        if self._block_prim:
            start_pose = _dynamic_control.Transform()
            start_pose.p = (30.0, -20.0, 5)
            start_pose.r = (0, 0, 0, 1)
            block_handle = self._dc.get_rigid_body(self._block_path)
            self._dc.set_rigid_body_pose(block_handle, start_pose)

        self._robot = None
        self.first_step = True

    def stop_tasks(self):
        self._robot = None
        self.first_step = True
        self.following = False
        self.created = False
        self.obstacle_on = False
        self.gripper_open = False

    def has_arrived(self):
        """if multiple targets are sent, the later one will overwrite the earlier one. 
            Use this function to check for arrived condition to be met before going to the next target.
        """
        if self._termination_criteria is None or self._robot is None:
            return False
        return self._termination_criteria(self._target, self._robot.end_effector.status.current_frame)

    def gripper_state(self):
        """ Returns state of gripper
        """
        if self._robot is None:
            return False
        return self._robot.end_effector.gripper.status()

    def get_states(self):

        if self._block_prim:
            # get block pose
            block_handle = self._dc.get_rigid_body(self._block_path)
            block_pose = self._dc.get_rigid_body_pose(block_handle)
            print("\nblock pose:\n \tposition:( {}, {}, {})".format(block_pose.p.x, block_pose.p.y, block_pose.p.z))
            print("\trotation: ({},{},{},{})".format(block_pose.r.x, block_pose.r.y, block_pose.r.z, block_pose.r.w))

        # get end effector pose
        if not self._timeline.is_playing():
            print("editor must be playing to get robot state")
            return
        if self._robot is not None:
            ee_state = self._robot.end_effector.status.current_frame
            print(
                "end effector position: \n \t{}".format(ee_state["orig"] * self._units_per_meter)
            )  # position retrieved from RMP is in meters
            print("end effector alignment:")
            print("\tx_axis: {}".format(ee_state["axis_x"]))
            print("\ty_axis: {}".format(ee_state["axis_y"]))
            print("\tz_axis: {}".format(ee_state["axis_z"]))

        # get robot joint states
        if self._ar == _dynamic_control.INVALID_HANDLE:
            self._ar = self._dc.get_articulation("/scene/robot")
        dof_states = self._dc.get_articulation_dof_states(self._ar, _dynamic_control.STATE_POS)
        if dof_states is not None:
            print("robot joint states:")
            print(dof_states["pos"])

        # get robot joint command
        num_dofs = self._dc.get_articulation_dof_count(self._ar)
        dof_position_target = np.zeros(num_dofs)
        dof_velocity_target = np.zeros(num_dofs)

        for dofIdx in range(num_dofs):
            dof_handle = self._dc.get_articulation_dof(self._ar, dofIdx)
            dof_position_target[dofIdx] = self._dc.get_dof_position_target(dof_handle)
            dof_velocity_target[dofIdx] = self._dc.get_dof_velocity_target(dof_handle)

        print("joint position command: ", dof_position_target)
        print("joint velocity command: ", dof_velocity_target)

        # get robot end_effector command
        print("end_effector command: ", self._target)

    def move_target(self, position: Gf.Vec3d, rotation: Gf.Matrix3d = Gf.Matrix3d(1.0)):
        """Move the target to a new location
        """
        if self._target_prim is not None:
            mat = Gf.Matrix4d().SetTransform(rotation, position)
            self._target_prim.GetAttribute("xformOp:transform").Set(mat)

    def saving_data(self):
        if self._save_data:
            print("stop saving")
            self._save_data = False

            f = open(self._save_dir, "w")
            f.write(str(self.get_action_state_dict()))
            f.close()
            print("data written to: ", self._save_dir)
        else:
            print("saving data")
            # if filename already exist, append a number to it
            if os.path.isfile(self._save_dir):
                file_num = 0
                self._save_dir_orig = self._save_dir
                while os.path.isfile(self._save_dir):
                    self._save_dir = self._save_dir_orig[:-4] + "_" + str(file_num) + ".txt"
                    file_num += 1
            print("data will be saved to: ", self._save_dir)
            self._save_data = True
            self.reset_action_state_dict()

    def save_dir(self, dir_name):
        self._save_dir = dir_name

    def get_action_state_dict(self):
        return self.state_dict_save

    def reset_action_state_dict(self):
        self.state_dict_save = {}
        self.state_dict_save["joint command"] = []
        self.state_dict_save["joint state"] = []

    def collect_action_state(self):
        # get robot joint states
        if self._ar == _dynamic_control.INVALID_HANDLE:
            self._ar = self._dc.get_articulation("/scene/robot")
        self.num_dofs = self._dc.get_articulation_dof_count(self._ar)

        dof_position_target = np.zeros(self.num_dofs)
        dof_velocity_target = np.zeros(self.num_dofs)

        for dofIdx in range(self.num_dofs):
            dof_handle = self._dc.get_articulation_dof(self._ar, dofIdx)
            dof_position_target[dofIdx] = self._dc.get_dof_position_target(dof_handle)
            dof_velocity_target[dofIdx] = self._dc.get_dof_velocity_target(dof_handle)

        dof_states = self._dc.get_articulation_dof_states(self._ar, _dynamic_control.STATE_POS)

        self.state_dict_save["joint command"].append(dof_position_target.tolist())
        self.state_dict_save["joint state"].append(dof_states["pos"].tolist())
