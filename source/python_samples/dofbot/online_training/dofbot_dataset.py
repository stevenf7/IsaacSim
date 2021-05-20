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
before capturing groundtruth consisting of an RGB rendered image, Tight 2D Bounding Boxes 
and Instance Segmentation masks.
"""

import os
import torch
import random
import numpy as np
import signal

import omni
import carb
from omni.isaac.python_app import OmniKitHelper

# Setup default generation variables
# Value are (min, max) ranges
OBJ_TRANSLATION_X = (-30.0, 30.0)
OBJ_TRANSLATION_Z = (-30.0, 30.0)
OBJ_ROTATION_Y = (0.0, 360.0)
LIGHT_INTENSITY = (500.0, 50000.0)

# Camera POV generation variables
AZIMUTH_ROTATION = (-30.0, 30.0)
ELEVATION_ROTATION = (-70.0, -20.0)
CAM_TRANSLATION_XYZ = (-50.0, 50.0)

SCALE = 20
CAMERA_DISTANCE = 500
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
    """Dataset of random cubes - domain randomize position/colour/texture/lighting/camera angle
    The RGB, BoundingBox and Instance Segmentation are captured by moving a camera aimed at the centre of the scene
    which is positioned at random but at a fixed distance from the centre. 
    """

    def __init__(
        # self, root, categories, max_asset_size=None, num_assets_min=1, num_assets_max=3, split=0.7, train=True
        self,
        num_assets_min=1,
        num_assets_max=3,
        split=0.7,
        train=True,
    ):
        assert (split > 0) and (split <= 1.0)

        self.kit = OmniKitHelper(config=RENDER_CONFIG)
        from omni.isaac.synthetic_utils import SyntheticDataHelper
        from omni.isaac.synthetic_utils import DomainRandomization

        self.sd_helper = SyntheticDataHelper()
        self.dr_helper = DomainRandomization()
        self.dr_helper.toggle_manual_mode()
        self.stage = self.kit.get_stage()

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

        self.asset_path = nucleus_server + "/Isaac"
        self._setup_world()
        self.cur_idx = 0
        self.exiting = False

        signal.signal(signal.SIGINT, self._handle_exit)

    def _handle_exit(self, *args, **kwargs):
        print("exiting dataset generation...")
        self.exiting = True

    def _setup_world(self):
        from pxr import UsdGeom

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

    def load_single_asset(self):
        from pxr import UsdGeom, Semantics

        x = random.uniform(*OBJ_TRANSLATION_X)
        z = random.uniform(*OBJ_TRANSLATION_Z)
        rot_y = random.uniform(*OBJ_ROTATION_Y)

        stage = self.kit.get_stage()
        prim_type = "Cube"
        prim = stage.DefinePrim("/World/cube", prim_type)

        UsdGeom.XformCommonAPI(prim).SetScale((SCALE, SCALE, SCALE))
        bound = UsdGeom.Mesh(prim).ComputeWorldBound(0.0, "default")
        box_min_y = bound.GetBox().GetMin()[1]
        UsdGeom.XformCommonAPI(prim).SetTranslate((x, -(box_min_y * SCALE), z))
        UsdGeom.XformCommonAPI(prim).SetRotate((0, rot_y, 0))

        # Add semantic label based on prim type
        sem = Semantics.SemanticsAPI.Apply(prim, "Semantics")
        sem.CreateSemanticTypeAttr()
        sem.CreateSemanticDataAttr()
        sem.GetSemanticTypeAttr().Set("class")
        sem.GetSemanticDataAttr().Set(prim_type)

        return prim

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
        # Add targets for all objects in scene (the cube)
        for asset in self.assets:
            comp_prim_paths_target.AddTarget(asset.GetPrimPath())
        # Add target for ground surface
        comp_prim_paths_target.AddTarget("/World/Ground")

    def load_distractor(self, id):
        from pxr import UsdGeom, Semantics

        x = random.uniform(*OBJ_TRANSLATION_X)
        z = random.uniform(*OBJ_TRANSLATION_Z)
        rot_y = random.uniform(*OBJ_ROTATION_Y)

        stage = self.kit.get_stage()
        prim_type = random.choice(["Sphere", "Cone"])
        prim = stage.DefinePrim(f"/World/obj{id}", prim_type)

        bound = UsdGeom.Mesh(prim).ComputeWorldBound(0.0, "default")
        box_min_y = bound.GetBox().GetMin()[1]
        UsdGeom.XformCommonAPI(prim).SetTranslate((x, -(box_min_y * SCALE), z))
        UsdGeom.XformCommonAPI(prim).SetRotate((0, rot_y, 0))
        UsdGeom.XformCommonAPI(prim).SetScale((SCALE, SCALE, SCALE))

        # Add semantic label based on prim type
        sem = Semantics.SemanticsAPI.Apply(prim, "Semantics")
        sem.CreateSemanticTypeAttr()
        sem.CreateSemanticDataAttr()
        sem.GetSemanticTypeAttr().Set("class")
        sem.GetSemanticDataAttr().Set(prim_type)

        return prim

    def populate_scene(self):
        """Clear the scene and populate it with assets."""
        self.stage.RemovePrim("/World/Asset")
        self.assets = []
        self.assets.append(self.load_single_asset())
        # self.assets.append(self.load_distractor(2))

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
        # By simply rotating a camera "rig" instead repositioning the camera
        # itself, we greatly simplify our job.

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

    def __iter__(self):
        return self

    def __next__(self):
        # Generate a new scene
        self.populate_scene()
        self.randomize_camera()
        self.update_dr_comp(self.texture_comp)
        self.dr_helper.randomize_once()
        self.randomize_asset_material()
        self.randomize_lighting()

        # step once and then wait for materials to load
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

    count = 0

    # Iterate through dataset and visualize the output
    plt.ion()
    _, axes = plt.subplots(1, 2, figsize=(10, 5))
    plt.tight_layout()

    for image, target in dataset:
        for ax in axes:
            ax.clear()
            ax.axis("off")

        np_image = image.permute(1, 2, 0).cpu().numpy()
        axes[0].imshow(np_image)

        num_instances = len(target["boxes"])
        colours = vis.random_colours(num_instances, enable_random=False)
        overlay = np.zeros_like(np_image)
        for mask, colour in zip(target["masks"].cpu().numpy(), colours):
            overlay[mask, :3] = colour

        axes[1].imshow(overlay)
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
    dataset.kit.shutdown()
