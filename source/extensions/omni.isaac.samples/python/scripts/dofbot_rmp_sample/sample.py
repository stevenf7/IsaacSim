# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import carb
import omni.ext
import omni.usd
import omni.kit.settings

from omni.isaac.motion_planning import _motion_planning
from omni.isaac.dynamic_control import _dynamic_control
import omni.physx as _physx

from omni.isaac.samples.scripts.utils.dofbot import Dofbot, default_config, LookAtCommander
from omni.isaac.samples.scripts.utils.world import World
from omni.isaac.samples.scripts.utils.reactive_behavior import FrameTerminationCriteria
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server
from omni.isaac.utils.scripts.scene_utils import set_up_z_axis, setup_physics

from pxr import UsdGeom, Gf, UsdPhysics
from omni.isaac.synthetic_utils import visualization as vis

import numpy as np
import os
import asyncio
import random

# Setup default generation variables
# Value are (min, max) ranges
OBJ_TRANSLATION_X = (-20.0, 20.0)
OBJ_TRANSLATION_Y = (-20.0, 20.0)
OBJ_ROTATION_Y = (0.0, 360.0)
NUM_DISTRACTORS = (0, 3)
DISTRACTOR_SCALE = 5


def create_dofbot_camera(stage, prim_env_path):
    """
    Creates and aligns prim with the dofbot camera mesh
    Returns viewport showing dofbot camera's POV
    """
    # Align with the camera mesh on link4
    dofbot_camera = stage.DefinePrim(prim_env_path + "/link4/Camera", "Camera")
    UsdGeom.XformCommonAPI(dofbot_camera).SetTranslate((-6.0, -6.0, 0))
    UsdGeom.XformCommonAPI(dofbot_camera).SetRotate((0, 270, 180))
    # TODO: Adjust to match physical camera
    attributes = {"focalLength": 11.0, "focusDistance": 12.0, "horizontalAperture": 25.0, "horizontalAperture": 40.0}
    for k, v in attributes.items():
        dofbot_camera.GetAttribute(k).Set(v)

    # Set this before setting viewport window size
    carb.settings.acquire_settings_interface().set_int("/app/renderer/resolution/width", -1)
    carb.settings.acquire_settings_interface().set_int("/app/renderer/resolution/height", -1)

    # Create new viewport, set active camera as dofbot POV
    viewport_handle_dofbot = omni.kit.viewport.get_viewport_interface().create_instance()
    viewport_window_dofbot = omni.kit.viewport.get_viewport_interface().get_viewport_window(viewport_handle_dofbot)
    viewport_window_dofbot.set_active_camera(prim_env_path + "/link4/Camera")
    viewport_window_dofbot.set_window_pos(0, 0)

    # match resolution of physical dofbot camera
    viewport_window_dofbot.set_window_size(640, 480)

    return viewport_window_dofbot


def create_prim_from_usd(stage, prim_env_path, prim_usd_path, location):
    """
    Loads dofbot USD asset into a prim
    """
    envPrim = stage.DefinePrim(prim_env_path, "Xform")  # create an empty Xform at the given path
    envPrim.GetReferences().AddReference(prim_usd_path)  # attach the USD to the given path
    UsdGeom.XformCommonAPI(envPrim).SetTranslate(location)


def create_prim(stage, prim_env_path, prim_type, translation, attributes={}):
    prim = stage.DefinePrim(prim_env_path, prim_type)
    if translation:
        UsdGeom.XformCommonAPI(prim).SetTranslate(translation)
    for k, v in attributes.items():
        prim.GetAttribute(k).Set(v)


class RMPSample:
    def __init__(self):

        # Interface handles
        self._timeline = omni.timeline.get_timeline_interface()
        # self._physxIFace = _physx.acquire_physx_interface()
        self._mp = _motion_planning.acquire_motion_planning_interface()
        self._dc = _dynamic_control.acquire_dynamic_control_interface()

        self.dofbot_viewport = None
        self._viewport = omni.kit.viewport.get_default_viewport_window()
        self.categories = ["None", "Cube", "Sphere", "Cone"]
        self.distractor_categories = ["Sphere", "Cone"]

        # Keep track of steps
        self.first_step = True
        self.step_counter = 0
        self.iter_counter = 0
        self.following = False  # is the task running
        self.created = False

        # Objects in scene
        self.obstacle_on = False  # is the obstacle active
        self.gripper_open = False
        self._block_prim = None
        self._target = None
        self._robot = None
        self._world = None
        self.randomize = True

        self._save_data = False
        self._save_dir = os.path.join(os.getcwd(), "")
        self._termination_criteria = FrameTerminationCriteria(orig_thresh=0.001)

    # Create Robot + World Setup + Register Assets + Step ----------------------------------------------------------------
    def create_robot(self):
        """ Acquire handles, load dofbot USD
        """
        # Get handles, set up scene
        self._stage = omni.usd.get_context().get_stage()
        self._ar = _dynamic_control.INVALID_HANDLE
        set_up_z_axis(self._stage)
        setup_physics(self._stage)

        ## Unit conversions: RMP is in meters, kit is by default in cm
        self._meters_per_unit = UsdGeom.GetStageMetersPerUnit(self._stage)
        self._units_per_meter = 1.0 / UsdGeom.GetStageMetersPerUnit(self._stage)

        # Get dofbot USD
        result, nucleus_server = find_nucleus_server()
        self.nucleus_server = nucleus_server
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return
        asset_path = nucleus_server + "/Users/kting/nano_arm"
        robot_usd = asset_path + "/dofbot_urdf_no_gravity.usd"
        robot_path = "/scene/robot"
        create_prim_from_usd(self._stage, robot_path, robot_usd, Gf.Vec3d(0, -20, 0))
        self.dofbot_viewport = create_dofbot_camera(self._stage, robot_path)

        self.gt = None
        self.first_step = True
        self.following = False
        self.robot = None
        self.created = True

    def setup_world(self):
        """ Create physics scene, setup lights and room
        """
        from pxr import Sdf, UsdGeom, Gf, UsdPhysics, PhysxSchema

        # Create physics scene for collision testing
        scene = UsdPhysics.Scene.Define(self._stage, Sdf.Path("/World/physicsScene"))
        scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
        scene.CreateGravityMagnitudeAttr().Set(981.0)

        # Set physics scene to use cpu physics
        PhysxSchema.PhysxSceneAPI.Apply(self._stage.GetPrimAtPath("/World/physicsScene"))
        physxSceneAPI = PhysxSchema.PhysxSceneAPI.Get(self._stage, "/World/physicsScene")
        physxSceneAPI.CreateEnableCCDAttr(True)
        physxSceneAPI.CreateEnableStabilizationAttr(True)
        physxSceneAPI.CreateEnableGPUDynamicsAttr(False)
        physxSceneAPI.CreateBroadphaseTypeAttr("MBP")
        physxSceneAPI.CreateSolverTypeAttr("TGS")

        # Set up lights and room
        light1_attr = {"radius": 100, "intensity": 30000.0, "color": (0.0, 0.365, 0.848)}
        create_prim(self._stage, "/World/Light1", "SphereLight", (-300, 250, 500), light1_attr)

        light2_attr = {"radius": 100, "intensity": 20000.0, "color": (1.0, 0.278, 0.0)}
        create_prim(self._stage, "/World/Light2", "SphereLight", (300, 40, 220), light2_attr)

        self.load_room()

    def load_room(self):
        """ Setup room and ground attributes + DR for ground and lights
        """
        room_attr = {"radius": 500, "primvars:displayColor": [(1.0, 1.0, 2.0)]}
        create_prim(self._stage, "/World/Room", "Sphere", None, room_attr)

        ground_attr = {"height": 1, "radius": 500, "primvars:displayColor": [(1.0, 1.0, 1.0)]}
        create_prim(self._stage, "/World/Ground", "Cylinder", (0.0, -1.0, -0.5), ground_attr)

        # For the ground, randomize colour only
        result, prim = omni.kit.commands.execute(
            "CreateColorComponentCommand",
            prim_paths=["/World/Ground"],
            first_color_range=(0.0, 0.0, 0.0),
            second_color_range=(1.0, 1.0, 1.0),
            roughness_range=(0.0, 1.0),
            metallic_range=(0.0, 0.0),
            duration=1.0,
            include_children=False,
        )

        # Randomize intensity and temperature of lights
        result, prim = omni.kit.commands.execute(
            "CreateLightComponentCommand",
            light_paths=["/World/Light1"],
            first_color_range=(0.9, 0.9, 0.9),
            second_color_range=(1.0, 1.0, 1.0),
            intensity_range=(40000.0, 70000.0),
            temperature_range=(1500.0, 6500.0),
            enable_temperature=True,
            duration=1.0,
            include_children=False,
        )

    def register_assets(self):
        # register world with RMP
        self._world = World(self._dc, self._mp)

        # register robot with RMP
        robot_path = "/scene/robot"
        self._robot = Dofbot(
            self._stage, self._stage.GetPrimAtPath(robot_path), self._dc, self._mp, self._world, default_config
        )
        # instantiate look_at commander (uses RMP to make robot look at target)
        self._look_at_commander = LookAtCommander(self._robot)

    # Load Objects + Move/Toggle  ----------------------------------------------------------------------------------------
    def follow_target(self):
        from pxr import Semantics
        from omni.physx.scripts import utils

        # Create target prim with TransformOp
        target_path = "/scene/target"
        target_geom = UsdGeom.Cube.Define(self._stage, target_path)
        offset = Gf.Vec3d(30, 0.0, 30.0)  # these are in cm
        mat = Gf.Matrix4d().SetTranslate(offset)
        target_size = 8
        target_geom.CreateSizeAttr(target_size)
        target_geom.AddTransformOp().Set(mat)
        self._target_prim = self._stage.GetPrimAtPath(target_path)

        # Add semantic label to the target, based on prim type
        sem = Semantics.SemanticsAPI.Apply(self._target_prim, "Semantics")
        sem.CreateSemanticTypeAttr()
        sem.CreateSemanticDataAttr()
        sem.GetSemanticTypeAttr().Set("class")
        sem.GetSemanticDataAttr().Set("Cube")

        # Specify polygonal area in which to randomly place the target
        polygon_points = [(-26, -10, 0), (-24, 16, 0), (-20, 20, 0), (0, 24, 0), (20, 20, 0), (24, 16, 0), (26, -10, 0)]

        # Create DR transform component
        # translate ranges specify min/max z positions of cube
        result, prim = omni.kit.commands.execute(
            "CreateTransformComponentCommand",
            prim_paths=["/scene/target"],
            translate_min_range=(0.0, 0.0, target_size / 2),
            translate_max_range=(0.0, 0.0, target_size / 2),
            polygon_points=polygon_points,
            # draw_polygon=True,
            duration=0.6,
        )
        # Add physics for overlap testing
        utils.setCollider(self._target_prim, approximationShape="convexHull")

        # Add motion planning and dynamic control handles
        self._world.register_object(0, target_path, "target")

        # set flag so the dofbot starts following in step()
        self.following = True

    def load_single_asset(self, prim_type, scale, i):
        """ Try to find an empty space (i.e. non overlapping) for the asset, then spawn
        """
        from pxr import Semantics, UsdGeom
        from omni.physx.scripts import utils

        # Try up to 5 times to find a spot, else return None
        overlapping = True
        attempts = 0
        max_attempts = 5

        new_asset_path = f"/scene/Asset/obj{i}"
        prim = self._stage.DefinePrim(new_asset_path, prim_type)
        bound = UsdGeom.Mesh(prim).ComputeWorldBound(0.0, "default")
        box_min_z = bound.GetBox().GetMin()[2] * scale

        # Check overlap:
        while overlapping and attempts < max_attempts:
            x = random.uniform(*OBJ_TRANSLATION_X)
            y = random.uniform(*OBJ_TRANSLATION_Y)
            rot_y = random.uniform(*OBJ_ROTATION_Y)

            rot = carb.Float4(0.0, 0.0, 1.0, 0.0)
            origin = carb.Float3(float(x), float(y), -box_min_z)
            extent = carb.Float3(float(scale), float(scale), float(scale))
            overlapping = self.check_overlap(extent, origin, rot)

        # if after max_attempts still overlapping, just return None
        if overlapping:
            return None

        UsdGeom.XformCommonAPI(prim).SetScale((scale, scale, scale))
        UsdGeom.XformCommonAPI(prim).SetTranslate((x, y, -box_min_z))
        UsdGeom.XformCommonAPI(prim).SetRotate((0, rot_y, 0))

        # Add semantic label based on prim type
        sem = Semantics.SemanticsAPI.Apply(prim, "Semantics")
        sem.CreateSemanticTypeAttr()
        sem.CreateSemanticDataAttr()
        sem.GetSemanticTypeAttr().Set("class")
        sem.GetSemanticDataAttr().Set(prim_type)

        # Add physics to the prim
        utils.setCollider(prim, approximationShape="convexHull")

        # Add motion planning and dynamic control handles
        self._world.register_object(0, new_asset_path, f"obj{i}")

        return prim

    def populate_scene(self):
        """ Choose random # of distractors, of random types
        """
        # Clear assets from previous randomized scene
        self.assets = []
        self._stage.RemovePrim("/scene/Asset")
        scale = DISTRACTOR_SCALE

        num_objects = random.randint(*NUM_DISTRACTORS)
        for i in range(num_objects):
            prim_type = random.choice(self.distractor_categories)
            new_asset = self.load_single_asset(prim_type, scale, i)
            if new_asset:
                self.assets.append(new_asset)
        self.update_dr_comp(self.texture_comp)

    def load_fixed_asset(self, asset_pos):
        # Create target prim with TransformOp
        self._stage.RemovePrim("/scene/Asset")
        self._stage.RemovePrim("/scene/target")
        self._stage.RemovePrim("/scene/test")
        fixed_target_path = "/scene/test/fixed_target"
        target_geom = UsdGeom.Cube.Define(self._stage, fixed_target_path)
        offset = asset_pos  # these are in cm
        mat = Gf.Matrix4d().SetTranslate(offset)
        target_size = 8
        target_geom.CreateSizeAttr(target_size)
        target_geom.AddTransformOp().Set(mat)
        self._target_prim = self._stage.GetPrimAtPath(fixed_target_path)

        # Add motion planning and dynamic control handles
        self._world.register_object(0, fixed_target_path, "target")

        # set flag so the dofbot starts following in step()
        self.following = True

    # RMP + Synthetic Data -----------------------------------------------------------------------------------------------
    def position_camera(self, target_pos):
        """ Specify the gripper's position, tell it to look at the target cube (RMP)
        """
        # Set arbitary ranges that match our use case
        orig_range_x = (-15, 15)
        orig_range_y = (8, 12)
        orig_range_z = (5, 20)

        if self.randomize:
            x_coord = np.random.uniform(*(orig_range_x))
            y_coord = np.random.uniform(*(orig_range_y))
            z_coord = np.random.uniform(*(orig_range_z))

        else:
            x_coord = 10
            y_coord = 10
            z_coord = 10

        origin_pos = np.array([x_coord, y_coord, z_coord]) * self._meters_per_unit
        target_pos = (float(target_pos[0]), float(target_pos[1]), float(target_pos[2]))
        self._look_at_commander.go_pos(origin_pos, target_pos)

    def check_groundtruth(self):
        if self.gt is not None:
            return True
        return False

    def collect_groundtruth(self):
        """ Use synthetic data helper to get RGB image + 2D bbox from dofbot POV
        """
        # Collect image from dofbot camera
        self.gt = self.sd_helper.get_groundtruth(["rgb", "boundingBox2DTight"], self.dofbot_viewport)
        return self.gt

    def step(self, step):
        """ This function is called every timestep in the editor (physX sub)
        """
        self.step_counter += 1

        # If robot has been created and timeline playing
        if self.created and self._timeline.is_playing():
            if self.first_step:
                print("first step")
                self.register_assets()
                self.create_dr_comp()
                self.follow_target()
                self.populate_scene()
                self.first_step = False

            # Use RMP to set gripper position and target
            if self.following:
                target_mat = self._target_prim.GetAttribute("xformOp:transform").Get()
                target_pos = target_mat.ExtractTranslation()

                # Use RMP to solve for specified gripper position (uses look_at function of dofbot class)
                if self.step_counter % 30 == 0:
                    self.position_camera(target_pos)

            # update RMP's world and robot states to sync with Kit
            self._world.update()
            self._robot.update()

    # Domain Randomizers -------------------------------------------------------------------------------------------------
    def create_dr_comp(self):
        # Put imports here to ensure kit has been initialized first
        from omni.isaac.synthetic_utils import SyntheticDataHelper
        from omni.isaac.synthetic_utils import DomainRandomization

        self.sd_helper = SyntheticDataHelper()
        self.dr_helper = DomainRandomization()

        """Creates DR components with various attributes.
        The list of asset prims to randomize gets updated for each component in update_dr_comp()
        """
        self.asset_path = self.nucleus_server + "/Isaac"
        texture_list = [
            self.asset_path + "/Samples/DR/Materials/Textures/checkered.png",
            self.asset_path + "/Samples/DR/Materials/Textures/marble_tile.png",
            self.asset_path + "/Samples/DR/Materials/Textures/picture_a.png",
            self.asset_path + "/Samples/DR/Materials/Textures/picture_b.png",
            self.asset_path + "/Samples/DR/Materials/Textures/textured_wall.png",
            self.asset_path + "/Samples/DR/Materials/Textures/checkered_color.png",
        ]
        self.texture_comp = self.dr_helper.create_texture_comp([], True, texture_list, duration=1.0)
        loading = True
        while loading:
            _, _, loading = omni.usd.get_context().get_stage_loading_status()
        print("Done Loading Materials!")

    def update_dr_comp(self, dr_comp):
        """Updates DR component with the asset prim paths that will be randomized"""
        comp_prim_paths_target = dr_comp.GetPrimPathsRel()
        comp_prim_paths_target.ClearTargets(True)

        # Add targets for all objects in newly randomized scene (cube + distractors)
        comp_prim_paths_target.AddTarget("/scene/target")
        for asset in self.assets:
            comp_prim_paths_target.AddTarget(asset.GetPrimPath())

    # Overlap -------------------------------------------------------------------------------------------------------------
    def report_hit(self, hit):
        """ Existing object turns red if the proposed position would result in a collision
        Note: use for troubleshooting, material randomization must be disabled for this to work
        """
        # from pxr import UsdGeom, Gf, Vt
        # hitColor = Vt.Vec3fArray([Gf.Vec3f(180.0 / 255.0, 16.0 / 255.0, 0.0)])
        # usdGeom = UsdGeom.Mesh.Get(self._stage, hit.rigid_body)
        # usdGeom.GetDisplayColorAttr().Set(hitColor)
        return True

    def check_overlap(self, extent, origin, rot):
        from omni.physx import get_physx_scene_query_interface

        numHits = get_physx_scene_query_interface().overlap_box(extent, origin, rot, self.report_hit, False)
        return numHits > 0

    # Check State ---------------------------------------------------------------------------------------------------------
    def target_reached(self):
        """ Check if end effector has reached target
        """
        state = self._robot.end_effector.status.current_frame
        target = self._robot.end_effector.status.current_target
        statedic = {0: "orig", 1: "axis_x", 2: "axis_y", 3: "axis_z"}
        for i in [1, 2, 3]:
            k = statedic[i]
            state_v = state[k]
            target_v = target[k]
            error = np.linalg.norm(state_v - target_v)
            if error > 1.5:
                return False, error
        # Errors in all three directions (x, y, z) must be < 2.0 for it to have reached target
        return True, error

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

    # Save and Reset --------------------------------------------------------------------------------------------------------
    def stop_tasks(self):
        self._robot = None
        self.first_step = True
        self.following = False
        self.created = False
        self.obstacle_on = False
        # self.gripper_open = False

    def save_dir(self, dir_name):
        self._save_dir = dir_name
