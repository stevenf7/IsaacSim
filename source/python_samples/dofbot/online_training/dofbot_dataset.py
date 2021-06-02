#!/usr/bin/env python
# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


"""Cube Dataset with online randomized scene generation for Instance Segmentation training.

Use OmniKit to generate a simple scene. At each iteration, the scene is populated by
creating a cube that rests on a plane. The cube pose, colours and textures are randomized. 
The camera position is also randomized within a range expected for the Dofbot's POV 
before capturing groundtruth consisting of an RGB rendered image, and Tight 2D Bounding Boxes 
"""

import os
import torch
import random
import numpy as np
import signal

import omni
import carb
from omni.isaac.python_app import OmniKitHelper
from pxr import UsdGeom, Gf, Vt

# Setup default generation variables
# Value are (min, max) ranges
OBJ_TRANSLATION_X = (-40.0, 40.0)
OBJ_TRANSLATION_Z = (-40.0, 40.0)
OBJ_ROTATION_Y = (0.0, 360.0)
LIGHT_INTENSITY = (500.0, 50000.0)

# Camera POV generation variables
AZIMUTH_ROTATION = (-30.0, 30.0)
ELEVATION_ROTATION = (-70.0, -20.0)
CAM_TRANSLATION_XYZ = (-50.0, 50.0)

CUBE_SCALE = 20
DISTRACTOR_SCALE = (15, 25)
CAMERA_DISTANCE = 600
BBOX_AREA_THRESH = 16

# Default rendering parameters
RENDER_CONFIG = {
    "renderer": "PathTracing",
    "samples_per_pixel_per_frame": 12,
    "experience": f'{os.environ["EXP_PATH"]}/omni.isaac.sim.python.kit',
    "headless": False,
    "width": 640,
    "height": 480,
}


class RandomObjects(torch.utils.data.IterableDataset):
    """Dataset of cube + distractor objects - domain randomize position/colour/texture/lighting/camera angle
    The RGB image and BoundingBox are captured by moving a camera aimed at the centre of the scene
    which is positioned at random but at a fixed distance from the centre. 
    """

    def __init__(
        self, categories=["Cube", "Sphere", "Cone"], num_assets_min=1, num_assets_max=3, split=0.7, train=True
    ):
        assert len(categories) > 1
        assert (split > 0) and (split <= 1.0)
        self.kit = OmniKitHelper(config=RENDER_CONFIG)
        self.stage = self.kit.get_stage()

        from omni.isaac.synthetic_utils import SyntheticDataHelper
        from omni.isaac.synthetic_utils import DomainRandomization

        self.sd_helper = SyntheticDataHelper()
        self.dr_helper = DomainRandomization()
        self.dr_helper.toggle_manual_mode()

        from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server

        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error(
                "Could not find nucleus server with /Isaac folder. Please specify the correct nucleus server in experiences/isaac-sim-python.json"
            )
            return
        result, nucleus_server = find_nucleus_server("/Library/Props/Road_Tiles/Parts/")
        if result is False:
            carb.log_error(
                "Could not find nucleus server with /Library/Props/Road_Tiles/Parts/ folder. Please refer to the documentation to aquire the road tile assets"
            )
            return

        self.categories = categories
        self.range_num_assets = (num_assets_min, num_assets_max)
        self.asset_path = nucleus_server + "/Isaac"

        self._setup_world()
        self.cur_idx = 0
        self.exiting = False
        signal.signal(signal.SIGINT, self._handle_exit)

    def _handle_exit(self, *args, **kwargs):
        print("exiting dataset generation...")
        self.exiting = True

    def _setup_world(self):
        from pxr import Sdf, UsdPhysics, PhysxSchema

        # Create physics scene for collision testing
        scene = UsdPhysics.Scene.Define(self.stage, Sdf.Path("/World/physicsScene"))
        scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
        scene.CreateGravityMagnitudeAttr().Set(981.0)

        # Set physics scene to use cpu physics
        PhysxSchema.PhysxSceneAPI.Apply(self.stage.GetPrimAtPath("/World/physicsScene"))
        physxSceneAPI = PhysxSchema.PhysxSceneAPI.Get(self.stage, "/World/physicsScene")
        physxSceneAPI.CreateEnableCCDAttr(True)
        physxSceneAPI.CreateEnableStabilizationAttr(True)
        physxSceneAPI.CreateEnableGPUDynamicsAttr(False)
        physxSceneAPI.CreateBroadphaseTypeAttr("MBP")
        physxSceneAPI.CreateSolverTypeAttr("TGS")

        """Setup lights, walls, floor, ceiling and camera"""
        self.kit.create_prim(
            "/World/Room", "Sphere", attributes={"radius": 1e3, "primvars:displayColor": [(1.0, 1.0, 1.0)]}
        )
        self.kit.create_prim(
            "/World/Ground",
            "Cylinder",
            translation=(0.0, -0.5, 0.0),
            rotation=(90.0, 0.0, 0.0),
            attributes={"height": 1, "radius": 1e4, "primvars:displayColor": [(1.0, 1.0, 1.0)]},
        )
        self.kit.create_prim(
            "/World/Light1",
            "SphereLight",
            translation=(-450, 350, 350),
            attributes={"radius": 100, "intensity": 30000.0, "color": (0.0, 0.365, 0.848)},
        )
        self.kit.create_prim(
            "/World/Light2",
            "SphereLight",
            translation=(450, 350, 350),
            attributes={"radius": 100, "intensity": 30000.0, "color": (1.0, 0.278, 0.0)},
        )
        self.kit.create_prim("/World/Asset", "Xform")

        self.camera_rig = UsdGeom.Xformable(self.kit.create_prim("/World/CameraRig", "Xform"))
        self.camera = self.kit.create_prim("/World/CameraRig/Camera", "Camera", translation=(0.0, 0.0, CAMERA_DISTANCE))
        # Change azimuth angle
        self.camera_rig.AddRotateYOp().Set(0)
        # Change elevation angle
        self.camera_rig.AddRotateXOp().Set(-40)

        vpi = omni.kit.viewport.get_viewport_interface()
        vpi.get_viewport_window().set_active_camera(str(self.camera.GetPath()))
        self.viewport = omni.kit.viewport.get_default_viewport_window()

        self.create_dr_comp()
        self.kit.update()

    def _add_preview_surface(self, prim, diffuse, roughness, metallic):
        from pxr import UsdShade, Sdf

        """Add a preview surface material using the metallic workflow."""
        path = f"{prim.GetPath()}/mat"
        material = UsdShade.Material.Define(self.stage, path)
        pbrShader = UsdShade.Shader.Define(self.stage, f"{path}/shader")
        pbrShader.CreateIdAttr("UsdPreviewSurface")
        pbrShader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Float3).Set(diffuse)
        pbrShader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(roughness)
        pbrShader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(metallic)

        material.CreateSurfaceOutput().ConnectToSource(pbrShader, "surface")

        UsdShade.MaterialBindingAPI(prim).Bind(material)

    def load_single_asset(self, prim_type, scale, i):
        from omni.physx.scripts import utils
        from pxr import Semantics

        overlapping = True
        stage = self.kit.get_stage()

        # Randomly generate transforms until a valid position is found
        # (i.e. new object will not overlap with existing ones)
        while overlapping:
            x = random.uniform(*OBJ_TRANSLATION_X)
            y = scale  # assumes bounding box of standard prim is 1 cubic unit
            z = random.uniform(*OBJ_TRANSLATION_Z)
            rot_y = random.uniform(*OBJ_ROTATION_Y)

            # Validate this proposed transform
            rot = carb.Float4(0.0, 0.0, 1.0, 0.0)
            origin = carb.Float3(float(x), float(y), float(z))
            extent = carb.Float3(float(scale), float(scale), float(scale))
            overlapping = self.check_overlap(extent, origin, rot)

        # No overlap, define the prim and apply the transform
        prim = stage.DefinePrim(f"/World/Asset/obj{i}", prim_type)
        bound = UsdGeom.Mesh(prim).ComputeWorldBound(0.0, "default")
        box_min_y = bound.GetBox().GetMin()[1] * scale

        UsdGeom.XformCommonAPI(prim).SetScale((scale, scale, scale))
        UsdGeom.XformCommonAPI(prim).SetTranslate((x, -box_min_y, z))
        UsdGeom.XformCommonAPI(prim).SetRotate((0, rot_y, 0))

        # Add semantic label based on prim type
        sem = Semantics.SemanticsAPI.Apply(prim, "Semantics")
        sem.CreateSemanticTypeAttr()
        sem.CreateSemanticDataAttr()
        sem.GetSemanticTypeAttr().Set("class")
        sem.GetSemanticDataAttr().Set(prim_type)

        # Add physics to the prim
        utils.setCollider(prim, approximationShape="convexHull")
        return prim

    # OVERLAP --------------------------------------------
    def report_hit(self, hit):
        """ Existing object turns red if the proposed position would result in a collision
        Note: use for troubleshooting, material randomization must be disabled for this to work
        """
        hitColor = Vt.Vec3fArray([Gf.Vec3f(180.0 / 255.0, 16.0 / 255.0, 0.0)])
        usdGeom = UsdGeom.Mesh.Get(self.stage, hit.rigid_body)
        usdGeom.GetDisplayColorAttr().Set(hitColor)
        return True

    def check_overlap(self, extent, origin, rot):
        from omni.physx import get_physx_scene_query_interface

        numHits = get_physx_scene_query_interface().overlap_box(extent, origin, rot, self.report_hit, False)
        if numHits > 0:
            return True
        return False

    # POPULATE AND RANDOMIZE -------------------------------
    def create_dr_comp(self):
        """Creates DR components with various attributes.
        The asset prims to randomize is an empty list for most components
        since we get a new list of assets every iteration.
        The asset list will be updated for each component in update_dr_comp()
        """
        texture_list = [
            self.asset_path + "/Samples/DR/Materials/Textures/checkered.png",
            self.asset_path + "/Samples/DR/Materials/Textures/marble_tile.png",
            self.asset_path + "/Samples/DR/Materials/Textures/picture_a.png",
            self.asset_path + "/Samples/DR/Materials/Textures/picture_b.png",
            self.asset_path + "/Samples/DR/Materials/Textures/textured_wall.png",
            self.asset_path + "/Samples/DR/Materials/Textures/checkered_color.png",
        ]
        material_list = [
            self.asset_path + "/Samples/DR/Materials/checkered.mdl",
            self.asset_path + "/Samples/DR/Materials/checkered_color.mdl",
            self.asset_path + "/Samples/DR/Materials/marble_tile.mdl",
            self.asset_path + "/Samples/DR/Materials/picture_a.mdl",
            self.asset_path + "/Samples/DR/Materials/picture_b.mdl",
            self.asset_path + "/Samples/DR/Materials/textured_wall.mdl",
        ]
        light_list = ["World/Light1", "World/Light2"]
        self.texture_comp = self.dr_helper.create_texture_comp([], True, texture_list)
        self.color_comp = self.dr_helper.create_color_comp([])
        self.material_comp = self.dr_helper.create_material_comp([], material_list)
        self.movement_comp = self.dr_helper.create_movement_comp([])
        self.rotation_comp = self.dr_helper.create_rotation_comp([])
        self.scale_comp = self.dr_helper.create_scale_comp([], max_range=(50, 50, 50))
        self.light_comp = self.dr_helper.create_light_comp(light_list)
        self.visibility_comp = self.dr_helper.create_visibility_comp([])

    def update_dr_comp(self, dr_comp):
        """Updates DR component with the asset prim paths that will be randomized"""
        comp_prim_paths_target = dr_comp.GetPrimPathsRel()
        comp_prim_paths_target.ClearTargets(True)
        # Add targets for all objects in scene (cube + distractors)
        for asset in self.assets:
            comp_prim_paths_target.AddTarget(asset.GetPrimPath())
        # Add target for ground surface
        comp_prim_paths_target.AddTarget("/World/Ground")

    def populate_scene(self):
        from omni.physx.scripts import utils

        """Clear the scene and populate it with assets."""
        self.stage.RemovePrim("/World/Asset")
        self.assets = []

        # Start simulation so we can check overlaps before spawning
        self.kit.play()

        # Add at least one cube of desired size
        self.assets.append(self.load_single_asset("Cube", CUBE_SCALE, 0))
        self.kit.update()

        # Add random number of distractor objects
        num_distractors = random.randint(*self.range_num_assets) - 1
        for i in range(num_distractors):
            prim_type = random.choice(self.categories)
            prim_scale = random.uniform(*DISTRACTOR_SCALE)
            self.assets.append(self.load_single_asset(prim_type, prim_scale, i + 1))
            self.kit.update()

    def randomize_asset_material(self):
        """Randomize asset material properties"""
        for asset in self.assets:
            colour = (random.random(), random.random(), random.random())

            # Here we choose not to have materials unrealistically rough or reflective.
            roughness = random.uniform(0.1, 0.9)

            # Choose ratio of metallic vs non-metallic (choose more non-metallic)
            metallic = random.choices([0.0, 1.0], weights=(0.2, 0.8))[0]
            self._add_preview_surface(asset, colour, roughness, metallic)

    def randomize_camera(self):
        """Randomize the camera position."""
        # Clear previous transforms
        self.camera_rig.ClearXformOpOrder()
        # Change azimuth angle
        self.camera_rig.AddRotateYOp().Set(random.uniform(*AZIMUTH_ROTATION))
        # Change elevation angle
        self.camera_rig.AddRotateXOp().Set(random.uniform(*ELEVATION_ROTATION))
        # Move camera position (translate)
        translation_xyz = tuple(random.uniform(*CAM_TRANSLATION_XYZ) for _ in range(3))
        self.camera_rig.AddTranslateOp().Set(translation_xyz)

    def randomize_lighting(self):
        self.stage.RemovePrim("/World/Light1")
        intens = random.uniform(*LIGHT_INTENSITY)
        self.kit.create_prim(
            "/World/Light1",
            "SphereLight",
            translation=(-450, 350, 350),
            attributes={"radius": 100, "intensity": intens, "color": (0.0, 0.365, 0.848)},
        )
        self.kit.update()

    # ITERATION----------------------------------------------
    def __iter__(self):
        return self

    def __next__(self):
        print("next!------------------------------")
        # Generate a new scene
        self.populate_scene()
        self.randomize_camera()
        self.update_dr_comp(self.texture_comp)
        self.dr_helper.randomize_once()
        self.randomize_asset_material()
        self.randomize_lighting()

        # Step once and then wait for materials to load
        self.kit.update()
        print("waiting for materials to load...")
        while self.kit.is_loading():
            self.kit.update()
        print("done")
        self.kit.update()

        # Collect Groundtruth
        gt = self.sd_helper.get_groundtruth(["rgb", "boundingBox2DTight"], self.viewport)

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
        self.categories = ["Cube", "Sphere", "Cone"]
        mapping = {cat: i + 1 for i, cat in enumerate(self.categories)}
        bboxes = torch.tensor(gt_bbox[["x_min", "y_min", "x_max", "y_max"]].tolist())
        labels = torch.LongTensor([mapping[bb["semanticLabel"]] for bb in gt_bbox])

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

    dataset = RandomObjects()
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

        categories = categories = ["Cube", "Sphere", "Cone"]
        mapping = {i + 1: cat for i, cat in enumerate(categories)}
        labels = [mapping[label.item()] for label in target["labels"]]
        vis.plot_boxes(ax, target["boxes"].tolist(), labels=labels, colours=colours)

        plt.draw()
        plt.pause(0.01)
        plt.savefig(f"dataset{count}.png")
        count = count + 1

        if dataset.exiting:
            break

    # cleanup
    dataset.kit.stop()
    dataset.kit.shutdown()
