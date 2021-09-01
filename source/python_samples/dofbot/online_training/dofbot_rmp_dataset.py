# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


"""Dofbot RMP Dataset with online randomized scene generation for Bounding Box Detection training.

Use OmniKit to generate a simple scene. At each iteration, the scene is populated by
creating a target cube that rests on a plane. The cube pose, colours and textures are randomized, 
along with the groundplane texture, backdrop and lighting position/intensity.  
The Dofbot uses RMP to position its gripper's camera realistically at various distances and angles from the target, 
capturing groundtruth consisting of an RGB rendered image, and Tight 2D Bounding Boxes. 
"""

import omni
import carb
from omni.isaac.python_app import OmniKitHelper

import os
import numpy as np
import random
import signal
import torch

# Setup default generation variables
# Value are (min, max) ranges
OBJ_TRANSLATION_X = (-60.0, 60.0)
OBJ_TRANSLATION_Y = (-20.0, 20.0)
OBJ_ROTATION_Y = (0.0, 360.0)
DISTRACTOR_SCALE = (3, 4)
LIGHT_INTENSITY = (500.0, 50000.0)

# Randomization frequency for backdrop and ground
# Requires loading textures, randomize every n frames
BACKDROP_RAND = 25
GROUND_RAND = 15

# Default rendering parameters
RENDER_CONFIG = {
    "renderer": "PathTracing",
    "samples_per_pixel_per_frame": 12,
    "experience": f'{os.environ["EXP_PATH"]}/omni.isaac.sim.python.kit',
    "headless": False,
    "width": 640,
    "height": 480,
}


def create_dofbot_camera(stage, prim_env_path):
    """
    Creates and aligns prim with the dofbot camera mesh
    Returns viewport showing dofbot camera's POV
    """
    from pxr import UsdGeom

    # Align with the camera mesh on link4
    dofbot_camera = stage.DefinePrim(prim_env_path + "/link4/Camera", "Camera")
    UsdGeom.XformCommonAPI(dofbot_camera).SetTranslate((-6.0, -6.0, 0))
    UsdGeom.XformCommonAPI(dofbot_camera).SetRotate((0, 270, 180))

    # TODO: Adjust to match physical camera
    attributes = {"focalLength": 26.0, "focusDistance": 12.0, "horizontalAperture": 25.0, "horizontalAperture": 40.0}
    for k, v in attributes.items():
        dofbot_camera.GetAttribute(k).Set(v)

    # Set this before setting viewport window size
    carb.settings.acquire_settings_interface().set_int("/app/renderer/resolution/width", -1)
    carb.settings.acquire_settings_interface().set_int("/app/renderer/resolution/height", -1)

    vp_handle_dofbot = omni.kit.viewport.get_viewport_interface().create_instance()
    vp_window_dofbot = omni.kit.viewport.get_viewport_interface().get_viewport_window(vp_handle_dofbot)
    vp_window_dofbot.set_window_size(640, 480)
    vp_window_dofbot.set_window_pos(720, 0)
    vp_window_dofbot.set_active_camera(prim_env_path + "/link4/Camera")

    return vp_window_dofbot


def create_prim_from_usd(stage, prim_env_path, prim_usd_path, location):
    """
    Loads dofbot USD asset into a prim
    """
    from pxr import UsdGeom

    envPrim = stage.DefinePrim(prim_env_path, "Xform")  # create an empty Xform at the given path
    envPrim.GetReferences().AddReference(prim_usd_path)  # attach the USD to the given path
    UsdGeom.XformCommonAPI(envPrim).SetTranslate(location)


def create_prim(stage, prim_env_path, prim_type, translation, attributes={}):
    from pxr import UsdGeom

    prim = stage.DefinePrim(prim_env_path, prim_type)
    # Set the translation if provided
    if translation:
        UsdGeom.XformCommonAPI(prim).SetTranslate(translation)
    for k, v in attributes.items():
        prim.GetAttribute(k).Set(v)


class RMPRandomObjects(torch.utils.data.IterableDataset):
    """Dataset of cube + distractor objects - domain randomize position/colour/texture/lighting/backdrop
    The Dofbot uses RMP to position its gripper's camera realistically at various distances and angles from the target, 
    capturing groundtruth consisting of an RGB rendered image, and Tight 2D Bounding Boxes. 
    """

    def __init__(
        self, categories=["None", "Cube", "Sphere", "Cone"], num_assets_min=1, num_assets_max=3, split=0.7, train=True
    ):
        assert len(categories) > 1
        assert (split > 0) and (split <= 1.0)

        # Create kit instance
        self.kit = OmniKitHelper(config=RENDER_CONFIG)
        self.stage = self.kit.get_stage()

        # Imports
        from omni.isaac.motion_planning import _motion_planning
        from omni.isaac.dynamic_control import _dynamic_control

        # Interface handles
        self._timeline = omni.timeline.get_timeline_interface()
        self._mp = _motion_planning.acquire_motion_planning_interface()
        self._dc = _dynamic_control.acquire_dynamic_control_interface()

        self.viewport = omni.kit.viewport.get_default_viewport_window()
        self.cur_idx = 0
        self.first_step = True
        self.assets = []
        self.patterned_wall_paths = []

        # turn this on to fix the PathTracing + Play (needed for overlap test) producing line artifacts
        carb.settings.get_settings().set_bool("/rtx/resetPtAccumOnAnimTimeChange", True)

        self.exiting = False
        signal.signal(signal.SIGINT, self._handle_exit)

    def _handle_exit(self, *args, **kwargs):
        print("exiting dataset generation...")
        self.exiting = True

    # Create Robot + World Setup + Register Assets  ---------------------------------------------------------------------
    def create_robot(self):
        """ Acquire handles, load dofbot USD
        """
        from omni.isaac.utils.scripts.scene_utils import set_up_z_axis, setup_physics
        from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server
        from pxr import UsdGeom, Gf

        # Get handles, set up scene
        from omni.isaac.dynamic_control import _dynamic_control

        self._stage = self.kit.get_stage()
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
        asset_path = nucleus_server + "/Isaac/Robots/Dofbot"
        robot_usd = asset_path + "/dofbot_rmp.usd"
        robot_path = "/scene/robot"
        create_prim_from_usd(self._stage, robot_path, robot_usd, Gf.Vec3d(0, -20, 0.5))

        # The dofbot_gripper_smaller_maxforce.usd contains GroundPlane - make invisible
        UsdGeom.Mesh(self._stage.GetPrimAtPath(robot_path + "/GroundPlane/CollisionMesh")).MakeInvisible()

        self.dofbot_viewport = create_dofbot_camera(self._stage, robot_path)

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
        light1_attr = {"radius": 100, "intensity": 30000.0, "color": (1.0, 1.0, 1.0)}
        create_prim(self._stage, "/World/Light1", "SphereLight", (-115, 150, 500), light1_attr)

        light2_attr = {"radius": 100, "intensity": 20000.0, "color": (1.0, 1.0, 1.0)}
        create_prim(self._stage, "/World/Light2", "SphereLight", (300, 40, 220), light2_attr)

        # Makes ground plane (mesh)
        self.load_ground()
        self.randomize_ground()
        self.randomize_backdrop()

    def load_ground(self):
        """ Create mesh for ground plane, create material object
        """
        from pxr import UsdGeom, Sdf

        # Create ground plane (scaled mesh cube)
        self._stage.RemovePrim("/Cube")
        _, path = omni.kit.commands.execute("CreateMeshPrimCommand", prim_type="Cube")
        self.ground_prim = self._stage.GetPrimAtPath(path)
        UsdGeom.XformCommonAPI(self.ground_prim).SetScale((1.2, 0.8, 0.01))

        # Specify asset paths of desired ground textures
        self.asset_path = self.nucleus_server
        texture_list = [
            self.asset_path
            + "/Library/Environments/TowelRoom/Materials/PreviewSurfaceTextures/WorldGridMaterial_BaseColor.png",
            self.asset_path
            + "/Library/Environments/TowelRoom/Materials/PreviewSurfaceTextures/MI_WoodWall_BaseColor.png",
            self.asset_path
            + "/Library/Environments/TowelRoom/Materials/PreviewSurfaceTextures/MI_Parquet_Floor_BaseColor.png",
            self.asset_path
            + "/Library/Environments/TowelRoom/Materials/PreviewSurfaceTextures/MI_WhitePlastic2_Roughness.png",
            self.asset_path + "/Library/Environments/TowelRoom/Materials/PreviewSurfaceTextures/M_Glass_BaseColor.png",
            self.asset_path
            + "/Library/Environments/TowelRoom/Materials/PreviewSurfaceTextures/WorldGridMaterial_Roughness.png",
            self.asset_path + "/Isaac/Samples/DR/Materials/Textures/marble_tile.png",
            self.asset_path + "/Isaac/Samples/DR/Materials/Textures/checkered.png",
            self.asset_path + "/Isaac/Samples/DR/Materials/Textures/textured_wall.png",
        ]

        # Create list of material objects for ground plane,
        self.mtl_list = []
        for i in range(len(texture_list)):
            omni.kit.commands.execute(
                "CreateAndBindMdlMaterialFromLibrary",
                mdl_name="OmniPBR.mdl",
                mtl_name="OmniPBR",
                mtl_created_list=self.mtl_list,
            )

        # Load textures into the list of material prims
        self.mtl_prims = [self._stage.GetPrimAtPath(path) for path in self.mtl_list]
        for i, texture in enumerate(texture_list):
            omni.usd.create_material_input(self.mtl_prims[i], "diffuse_texture", texture, Sdf.ValueTypeNames.Asset)

    # Ground and Backdrop Randomization -----------------------------------------------------------------------------------
    def randomize_ground(self):
        """ Randomize ground plane material
        """
        from pxr import UsdGeom

        rand_xscale = random.randrange(50, 120) / 100
        rand_yscale = random.randrange(50, 120) / 100
        UsdGeom.XformCommonAPI(self.ground_prim).SetScale((rand_xscale, rand_yscale, 0.01))

        from pxr import UsdShade

        new_mat_shade = UsdShade.Material(random.choice(self.mtl_prims))
        UsdShade.MaterialBindingAPI(self.ground_prim).Bind(new_mat_shade, UsdShade.Tokens.strongerThanDescendants)

    def randomize_backdrop(self):
        """ Creates a background for the scene (DomeLight + HDR Texture)
        """
        from pxr import UsdGeom, UsdLux

        self.asset_path = self.nucleus_server + "/NVIDIA/Assets/Skies/Indoor"

        texture_files = [
            self.asset_path + "/carpentry_shop_01_4k.hdr",
            self.asset_path + "/adams_place_bridge_4k.hdr",
            self.asset_path + "/autoshop_01_4k.hdr",
            self.asset_path + "/en_suite_4k.hdr",
            self.asset_path + "/entrance_hall_4k.hdr",
            self.asset_path + "/hospital_room_4k.hdr",
            self.asset_path + "/surgery_4k.hdr",
            self.asset_path + "/vulture_hide_4k.hdr",
            self.asset_path + "/wooden_lounge_4k.hdr",
        ]
        prim_path = "/World/Env/BackgroundLight"
        create_prim(
            stage=self._stage,
            prim_env_path=prim_path,
            prim_type="DomeLight",
            translation=[],
            attributes={
                UsdLux.Tokens.intensity: 1000,
                UsdLux.Tokens.specular: 1,
                UsdLux.Tokens.textureFile: random.choice(texture_files),
                UsdLux.Tokens.textureFormat: UsdLux.Tokens.latlong,
                UsdGeom.Tokens.visibility: "inherited",
            },
        )

    def reposition_lights(self):
        """ Moves the two SphereLights in the scene
        """
        from pxr import UsdGeom

        light1_prim = self._stage.GetPrimAtPath("/World/Light1")
        orig_range_x = (-900, 100)
        orig_range_y = (-200, 600)
        orig_range_z = (0, 500)
        x_coord = np.random.uniform(*(orig_range_x))
        y_coord = np.random.uniform(*(orig_range_y))
        z_coord = np.random.uniform(*(orig_range_z))
        UsdGeom.XformCommonAPI(light1_prim).SetTranslate((x_coord, y_coord, z_coord))

        light2_prim = self._stage.GetPrimAtPath("/World/Light2")
        orig_range_x = (-300, 200)
        orig_range_y = (-300, 300)
        orig_range_z = (-200, 400)
        x_coord = np.random.uniform(*(orig_range_x))
        y_coord = np.random.uniform(*(orig_range_y))
        z_coord = np.random.uniform(*(orig_range_z))
        UsdGeom.XformCommonAPI(light2_prim).SetTranslate((x_coord, y_coord, z_coord))

    # Load Objects + Create Target ---------------------------------------------------------------------------------------
    def load_single_asset(self, prim_type, scale, i):
        """ Try to find an empty space (i.e. non overlapping) for the asset, then spawn
        """
        from pxr import Semantics, UsdGeom, Gf
        from omni.physx.scripts import utils

        # Try up to 5 times to find a spot, else return None
        overlapping = True
        attempts = 0
        max_attempts = 5

        # Check overlap:
        while overlapping and attempts < max_attempts:
            x = random.uniform(*OBJ_TRANSLATION_X)
            y = scale
            z = random.uniform(*OBJ_TRANSLATION_Y)

            rot = carb.Float4(0.0, 0.0, 1.0, 0.0)
            origin = carb.Float3(float(x), float(y), float(z))
            extent = carb.Float3(float(scale), float(scale), float(scale))
            overlapping = self.check_overlap(extent, origin, rot)

        # Exceeded max attempts at overlap test
        if overlapping:
            return None

        # For cubes use USDGeom and add wrappers around
        if prim_type == "Cube":
            new_asset_path = f"/scene/Asset/obj{i}"
            asset_geom = UsdGeom.Cube.Define(self._stage, new_asset_path)
            offset = Gf.Vec3d(x, y, z)
            asset_geom.CreateSizeAttr(scale)
            prim = self._stage.GetPrimAtPath(new_asset_path)
            UsdGeom.XformCommonAPI(prim).SetTranslate(offset)

            lid_path = f"/scene/Asset/obj{i}" + "/lid"
            self.patterned_wall_paths.append(lid_path)
            lid = UsdGeom.Cube.Define(self._stage, lid_path)
            lid.CreateSizeAttr(scale)
            UsdGeom.XformCommonAPI(lid).SetScale((1.0, 1.0, 0.00001))
            UsdGeom.XformCommonAPI(lid).SetTranslate((0.0, 0.0, scale / 2))

            # Front-back faces
            fb_scale = (0.00001, 1.0, 1.0)
            fb_translate = (scale / 2, 0.0, 0.0)
            wall_a_path = f"/scene/Asset/obj{i}" + "/wall_a"
            self.patterned_wall_paths.append(wall_a_path)
            wall = UsdGeom.Cube.Define(self._stage, wall_a_path)
            wall.CreateSizeAttr(scale)
            UsdGeom.XformCommonAPI(wall).SetScale(fb_scale)
            UsdGeom.XformCommonAPI(wall).SetTranslate(fb_translate)

            # Left-right faces
            lr_scale = (1.0, 0.00001, 1.0)
            lr_translate = (0.0, scale / 2, 0.0)
            wall_b_path = f"/scene/Asset/obj{i}" + "/wall_b"
            self.patterned_wall_paths.append(wall_b_path)
            wall = UsdGeom.Cube.Define(self._stage, wall_b_path)
            wall.CreateSizeAttr(scale)
            UsdGeom.XformCommonAPI(wall).SetScale(lr_scale)
            UsdGeom.XformCommonAPI(wall).SetTranslate(lr_translate)

        else:
            new_asset_path = f"/scene/Distractor/obj{i}"
            self.distractor_paths.append(new_asset_path)
            prim = self._stage.DefinePrim(new_asset_path, prim_type)
            UsdGeom.XformCommonAPI(prim).SetScale((scale, scale, scale))
            UsdGeom.XformCommonAPI(prim).SetTranslate((x, y, scale))

        # Add semantic label based on prim type
        sem = Semantics.SemanticsAPI.Apply(prim, "Semantics")
        sem.CreateSemanticTypeAttr()
        sem.CreateSemanticDataAttr()
        sem.GetSemanticTypeAttr().Set("class")
        sem.GetSemanticDataAttr().Set(prim_type)

        # Add physics to the prim
        utils.setCollider(prim, approximationShape="convexHull")

        self._world.register_object(0, new_asset_path, f"obj{i}")
        return prim

    def populate_scene(self):
        """ Choose random # of distractors, of random types
            Can just call once at the beginning 
        """
        num_cubes = random.randint(*(1, 4))
        for i in range(num_cubes):
            scale = random.uniform(*(DISTRACTOR_SCALE))
            prim = self.load_single_asset("Cube", scale, i)
            colour = np.random.choice(range(256), size=3) / 255
            prim.GetAttribute("primvars:displayColor").Set(colour)
            self.assets.append(prim)

        self.distractors = []
        self.distractor_paths = []
        num_distractors = random.randint(*(3, 6))
        for i in range(num_distractors):
            scale = random.uniform(*(DISTRACTOR_SCALE))
            prim_type = random.choice(["Cone", "Sphere"])
            prim = self.load_single_asset(prim_type, scale, i)
            colour = np.random.choice(range(256), size=3) / 255
            prim.GetAttribute("primvars:displayColor").Set(colour)
            self.assets.append(prim)

    def reposition_objects(self):
        """ Move the target and distractors around
            Occasionally move out-of-view, rather than deleting object
        """
        from pxr import UsdGeom, Gf

        all_assets = self.assets + self.distractors
        for asset in all_assets:
            # Try up to 5 times to find a spot, else return None
            overlapping = True
            attempts = 0
            max_attempts = 10

            # Check overlap:
            while overlapping and attempts < max_attempts:
                x = random.uniform(*OBJ_TRANSLATION_X)
                y = random.uniform(*OBJ_TRANSLATION_Y)
                scale = max(DISTRACTOR_SCALE)
                z = scale

                rot = carb.Float4(0.0, 0.0, 1.0, 0.0)
                origin = carb.Float3(float(x), float(y), float(z))
                extent = carb.Float3(float(scale), float(scale), float(scale))
                overlapping = self.check_overlap(extent, origin, rot)
                attempts = attempts + 1

            # If still overlapping, will move on to other object

            rotation = Gf.Matrix3d(1.0)
            position = Gf.Vec3d(x, y, scale)

            if asset.GetAttribute("xformOp:transform"):
                mat = Gf.Matrix4d().SetTransform(rotation, position)
                rotation = random.uniform(*(0.0, 180.0))
                mat.SetRotateOnly(Gf.Rotation(Gf.Vec3d(0, 0, 1), rotation))
                asset.GetAttribute("xformOp:transform").Set(mat)

            else:
                UsdGeom.XformCommonAPI(asset).SetTranslate(position)

        self._world.update()
        self._robot.update()

    def rand_obj_appearance(self):
        from pxr import UsdGeom

        all_assets = self.assets + self.distractors + [self._target_prim]
        for asset in all_assets:
            colour = np.random.choice(range(256), size=3) / 255
            asset.GetAttribute("primvars:displayColor").Set(colour)
        self.update_dr_targets(self.texture_comp)

    # OVERLAP --------------------------------------------
    def report_hit(self, hit):
        return True

    def check_overlap(self, extent, origin, rot):
        from omni.physx import get_physx_scene_query_interface

        numHits = get_physx_scene_query_interface().overlap_box(extent, origin, rot, self.report_hit, False)
        return numHits > 0

    # Domain Randomizers -------------------------------------------------------------------------------------------------
    def create_dr_comp(self):
        # Imports placed here to ensure kit has been initialized first
        from omni.isaac.synthetic_utils import SyntheticDataHelper
        import omni.isaac.dr as dr

        self.sd_helper = SyntheticDataHelper()
        self.dr = dr
        self.dr.commands.ToggleManualModeCommand().do()

        """Creates DR components with various attributes.
        The list of asset prims to randomize gets updated for each component in  update call
        """
        self.asset_path = self.nucleus_server + "/Isaac"
        texture_list = [
            self.asset_path + "/Samples/DR/Materials/Textures/marble_tile.png",
            self.asset_path + "/Samples/DR/Materials/Textures/checkered.png",
            self.asset_path + "/Samples/DR/Materials/Textures/textured_wall.png",
            self.asset_path + "/Samples/DR/Materials/Textures/picture_b.png",
            self.asset_path + "/Samples/DR/Materials/Textures/checkered_color.png",
        ]
        self.texture_comp = self.dr.commands.CreateTextureComponentCommand(
            prim_paths=[], enable_project_uvw=True, texture_list=texture_list, duration=1.0
        ).do()

    def update_dr_targets(self, dr_comp):
        """Updates DR component with the asset prim paths that will be randomized"""
        comp_prim_paths_target = dr_comp.GetPrimPathsRel()
        comp_prim_paths_target.ClearTargets(True)

        # For cubes: Randomly choose a set of walls to re-texture
        sample_paths = random.sample(self.patterned_wall_paths, 2)
        for wall_path in sample_paths:
            comp_prim_paths_target.AddTarget(wall_path)

        # For distractors: Randomly choose a number of objects to re-texture
        num = random.randint(*(0, 2))
        comp_prim_paths_target.AddTarget(f"/scene/Distractor/obj{num}")

    # Load Objects + Create Target  ----------------------------------------------------------------------------------------
    def register_assets(self):
        """ Instantiate classes World, Dofbot, LookAtCommander
        """
        from omni.isaac.samples.scripts.utils.dofbot import Dofbot, default_config, LookAtCommander
        from omni.isaac.samples.scripts.utils.world import World

        # register world with RMP
        self._world = World(self._dc, self._mp)

        # register robot with RMP
        robot_path = "/scene/robot"
        self._robot = Dofbot(
            self._stage, self._stage.GetPrimAtPath(robot_path), self._dc, self._mp, self._world, default_config
        )
        # instantiate look_at commander (uses RMP to make robot look at target)
        self._look_at_commander = LookAtCommander(self._robot)

    def follow_target(self):
        """ Create a target cube with semantic label, physics, mp and dc handles
        """
        from pxr import Semantics, UsdGeom, Gf
        from omni.physx.scripts import utils

        # Create target prim with TransformOp
        target_path = "/scene/target"
        target_geom = UsdGeom.Cube.Define(self._stage, target_path)
        offset = Gf.Vec3d(15.0, 15.0, 5.0)  # these are in cm
        mat = Gf.Matrix4d().SetTranslate(offset)
        target_size = 5
        target_geom.CreateSizeAttr(target_size)
        self._target_prim = self._stage.GetPrimAtPath(target_path)

        if self._target_prim.GetAttribute("xformOp:transform"):
            self._target_prim.GetAttribute("xformOp:transform").Set(mat)
        else:
            target_geom.AddTransformOp().Set(mat)

        self._target_prim.GetAttribute("primvars:displayColor").Set([(0.0, 1.0, 0.0)])
        # Add semantic label to the target, based on prim type
        sem = Semantics.SemanticsAPI.Apply(self._target_prim, "Semantics")
        sem.CreateSemanticTypeAttr()
        sem.CreateSemanticDataAttr()
        sem.GetSemanticTypeAttr().Set("class")
        sem.GetSemanticDataAttr().Set("Cube")

        # Specify polygonal area in which to randomly place the target
        polygon_points = [(-26, -10, 0), (-24, 14, 0), (-20, 16, 0), (0, 18, 0), (20, 16, 0), (24, 14, 0), (26, -10, 0)]

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

        self.assets.append(self._target_prim)

        # set flag so the dofbot starts following in step()
        self.following = True

    def position_camera(self):
        """ Specify the gripper's position, tell it to look at the target cube (RMP)
        """
        target_mat = omni.usd.utils.get_world_transform_matrix(self._target_prim)
        target_pos = target_mat.ExtractTranslation()
        target_rot = target_mat.ExtractRotationMatrix()

        # Position the gripper at an offset distance from the target
        offset_range_x = (3, 5)
        offset_range_y = (0, 5)
        offset_range_z = (5, 20)

        x_shift = np.random.uniform(*(offset_range_x))
        y_shift = np.random.uniform(*(offset_range_y))
        z_shift = np.random.uniform(*(offset_range_z))

        # Absolute value on y, to avoid Dofbot leaning backwards
        shift = np.array([x_shift, y_shift, z_shift])
        camera_pos = np.array([target_pos[0], abs(target_pos[1]), target_pos[2]]) + shift
        print(camera_pos)

        self._target = {
            "orig": camera_pos * self._meters_per_unit,
            "axis_x": np.array(-target_rot[0]),
            "axis_y": np.array(target_rot[1]),
            "axis_z": np.array(-target_rot[2]),
        }

        # Use go_local for locked y_axis
        self._robot.end_effector.go_local(target=self._target, use_default_config=True, wait_for_target=True)

    # ITERATION----------------------------------------------
    def __iter__(self):
        return self

    def __next__(self):
        print("next!------------------------------")
        if self.first_step:
            self.create_robot()
            self.setup_world()
            self.viewport.set_camera_position("/OmniverseKit_Persp", 142, -127, 56, True)
            self.viewport.set_camera_target("/OmniverseKit_Persp", -180, 234, -27, True)
            self.kit.play()
            self.first_step = False

            if self._timeline.is_playing():
                self.create_dr_comp()
                self.register_assets()
                self.follow_target()
                self.populate_scene()
                self.update_dr_targets(self.texture_comp)
                self._world.update()
                self._robot.update()

        # Randomize these every n frames, involves loading textures
        if self.cur_idx % BACKDROP_RAND == 0:
            self.randomize_backdrop()
        if self.cur_idx % GROUND_RAND == 0:
            self.randomize_ground()

        # Randomize these every frame
        self.reposition_lights()
        self.reposition_objects()
        self.rand_obj_appearance()
        self.dr.commands.RandomizeOnceCommand().do()

        if self.following:
            self.position_camera()

        # Step once and then wait for materials to load
        self.kit.update()
        print("waiting for materials to load...")
        while self.kit.is_loading():
            self.kit.update()
        print("done")
        self.kit.update()

        self._world.update()
        self._robot.update()

        from omni.isaac.synthetic_utils import SyntheticDataHelper

        self.sd_helper = SyntheticDataHelper()

        # Collect Groundtruth
        gt = self.sd_helper.get_groundtruth(["rgb", "boundingBox2DTight"], self.dofbot_viewport)

        # RGB
        # Drop alpha channel
        image = gt["rgb"][..., :3]
        # Cast to tensor if numpy array
        if isinstance(gt["rgb"], np.ndarray):
            image = torch.tensor(image, dtype=torch.float, device="cuda")
        # Normalize between 0. and 1. and change order to channel-first.
        image = image.float() / 255.0
        image = image.permute(2, 0, 1)

        # Bounding Box
        gt_bbox = gt["boundingBox2DTight"]

        # Create mapping from categories to index
        self.categories = ["None", "Cube", "Sphere", "Cone"]
        mapping = {cat: i + 1 for i, cat in enumerate(self.categories)}
        bboxes = torch.tensor(gt_bbox[["x_min", "y_min", "x_max", "y_max"]].tolist())
        labels = torch.LongTensor([mapping[bb["semanticLabel"]] for bb in gt_bbox])

        # If no objects present in view
        if bboxes.nelement() == 0:
            print("No object present in view")
            target = {
                "boxes": torch.zeros((0, 4), dtype=torch.float32),
                "labels": torch.tensor([1], dtype=torch.int64),
                "image_id": torch.LongTensor([self.cur_idx]),
                "area": torch.tensor(0, dtype=torch.float32),
                "iscrowd": torch.zeros((0,), dtype=torch.int64),
            }

        else:
            # Calculate bounding box area for each area
            areas = (bboxes[:, 2] - bboxes[:, 0]) * (bboxes[:, 3] - bboxes[:, 1])
            # Identify invalid bounding boxes to filter final output
            valid_areas = (areas > 0.0) * (areas < (image.shape[1] * image.shape[2]))

            target = {
                "boxes": bboxes[valid_areas],
                "labels": labels[valid_areas],
                "image_id": torch.LongTensor([self.cur_idx]),
                "area": areas[valid_areas],
                "iscrowd": torch.BoolTensor([False] * len(bboxes[valid_areas])),  # Assume no crowds
            }
        self.cur_idx += 1
        return image, target


if __name__ == "__main__":
    "Typical usage"
    import argparse
    import matplotlib.pyplot as plt

    dataset = RMPRandomObjects()
    from omni.isaac.synthetic_utils import visualization as vis

    # Iterate through dataset and visualize the output
    plt.ion()
    _, axes = plt.subplots(1, 2, figsize=(10, 5))
    plt.tight_layout()
    count = 0

    for image, target in dataset:
        for ax in axes:
            ax.clear()
            ax.axis("off")

        np_image = image.permute(1, 2, 0).cpu().numpy()
        axes[0].imshow(np_image)

        num_instances = len(target["boxes"])
        colours = vis.random_colours(num_instances, enable_random=False)

        axes[1].imshow(np_image)
        categories = categories = ["None", "Cube", "Sphere", "Cone"]
        mapping = {i + 1: cat for i, cat in enumerate(categories)}
        labels = [mapping[label.item()] for label in target["labels"]]
        vis.plot_boxes(ax, target["boxes"].tolist(), labels=labels, colours=colours)

        plt.draw()
        plt.savefig("dataset.png")

        if dataset.exiting:
            break

    # cleanup
    dataset.kit.stop()
    dataset.kit.shutdown()
