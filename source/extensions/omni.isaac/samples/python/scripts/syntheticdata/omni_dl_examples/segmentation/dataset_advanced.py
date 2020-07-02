#!/usr/bin/env python
# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


"""Dataset with online randomized scene generation for Instance Segmentation training.

Use OmniKit to generate a simple scene. At each iteration, the scene is populated by
adding assets from the user-specified classes with randomized pose and colour. 
The camera position is also randomized before capturing groundtruth consisting of
an RGB rendered image, Tight 2D Bounding Boxes and Instance Segmentation masks. 
"""


import os
import glob
import torch
import random
import asyncio
import numpy as np

import omni
from pxr import UsdGeom, UsdShade, Sdf, Semantics, Gf, PhysicsSchema, PhysxSchema, PhysicsSchemaTools

from omni_dl_examples.helpers import OmniKitHelper, SyntheticDataHelper, shapenet


# Setup default generation variables
# Value are (min, max) ranges
RANDOM_TRANSLATION_X = (-30.0, 30.0)
RANDOM_TRANSLATION_Z = (-30.0, 30.0)
RANDOM_ROTATION_Y = (0.0, 360.0)
SCALE = 20
CAMERA_DISTANCE = 300
BBOX_AREA_THRESH = 16

# Default rendering parameters
RENDER_CONFIG = {
    "width": 600,
    "height": 600,
    "renderer": "PathTracing",
    "samples_per_pixel_per_frame": 32,
    "headless": True,
    "max_bounces": 10,
    "max_specular_transmission_bounces": 6,
    "max_volume_bounces": 4,
}


class RandomObjects(torch.utils.data.IterableDataset):
    """Dataset of random ShapeNet objects.
    Objects are randomly chosen from selected categories and are positioned, rotated and coloured
    randomly in an empty room. RGB, BoundingBox2DTight and Instance Segmentation are captured by moving a
    camera aimed at the centre of the scene which is positioned at random at a fixed distance from the centre.

    This dataset is intended for use with ShapeNet but will function with any dataset of USD models
    structured as `root/category/**/*.usd. One note is that this is designed for assets without materials
    attached. This is to avoid requiring to compile MDLs and load textures while training.
    """

    def __init__(
        self, root, categories, max_asset_size=None, num_assets_min=3, num_assets_max=5, split=0.7, train=True
    ):
        self.kit = OmniKitHelper(config=RENDER_CONFIG)
        self.sd_helper = SyntheticDataHelper()

        self.categories = categories
        self.range_num_assets = (num_assets_min, max(num_assets_min, num_assets_max))
        self.references = self._find_usd_assets(root, categories, max_asset_size, split, train)

        self.cur_idx = 0

    async def setup_world(self):
        """Setup lights, walls, floor, ceiling and camera"""
        await omni.kit.asyncapi.new_stage()
        self.stage = self.kit.get_stage()
        # In a practical setting, the room parameters should attempt to match those of the
        # target domain. Here, we insteady choose for simplicity.
        self.create_prim(
            "/World/Room", "Sphere", attributes={"radius": 1e3, "primvars:displayColor": [(1.0, 1.0, 1.0)]}
        )
        # self.create_prim(
        #     "/World/Ground",
        #     "Cylinder",
        #     translation=(0.0, -0.5, 0.0),
        #     rotation=(90.0, 0.0, 0.0),
        #     attributes={"height": 1, "radius": 1e4, "primvars:displayColor": [(1.0, 1.0, 1.0)]},
        # )
        self.create_prim(
            "/World/Light1",
            "SphereLight",
            translation=(-450, 350, 350),
            attributes={"radius": 100, "intensity": 30000.0, "color": (0.0, 0.365, 0.848)},
        )
        self.create_prim(
            "/World/Light2",
            "SphereLight",
            translation=(450, 350, 350),
            attributes={"radius": 100, "intensity": 30000.0, "color": (1.0, 0.278, 0.0)},
        )
        self.create_prim("/World/Asset", "Xform")

        self.camera_rig = UsdGeom.Xformable(self.create_prim("/World/CameraRig", "Xform"))
        self.camera = self.create_prim("/World/CameraRig/Camera", "Camera", translation=(0.0, 0.0, CAMERA_DISTANCE))
        vpi = omni.kit.viewport.get_viewport_interface()
        vpi.get_viewport_window().set_active_camera(str(self.camera.GetPath()))
        self.kit.setup_renderer()
        await omni.kit.asyncapi.next_update()

    def setup_physics(self):
        # Add physics scene
        scene = PhysicsSchema.PhysicsScene.Define(self.stage, Sdf.Path("/World/physicsScene"))
        # Set gravity vector
        scene.CreateGravityAttr().Set(Gf.Vec3f(0.0, -981.0, 0))
        # Set physics scene to use cpu physics
        PhysxSchema.PhysxSceneAPI.Apply(self.stage.GetPrimAtPath("/World/physicsScene"))
        physxSceneAPI = PhysxSchema.PhysxSceneAPI.Get(self.stage, "/World/physicsScene")
        physxSceneAPI.CreatePhysxSceneEnableCCDAttr(True)
        physxSceneAPI.CreatePhysxSceneEnableStabilizationAttr(True)
        physxSceneAPI.CreatePhysxSceneEnableGPUDynamicsAttr(False)
        physxSceneAPI.CreatePhysxSceneBroadphaseTypeAttr("MBP")
        physxSceneAPI.CreatePhysxSceneSolverTypeAttr("TGS")

        # Create a ground plance
        PhysicsSchemaTools.addGroundPlane(self.stage, "/World/groundPlane", "Y", 500, Gf.Vec3f(0, 0, 0), Gf.Vec3f(1.0))

    def _find_usd_assets(self, root, categories, max_asset_size, split, train=True):
        """Look for USD files under root/category for each category specified.
        For each category, generate a list of all USD files found and select
        assets up to split * len(num_assets) if `train=True`, otherwise select the
        remainder.
        """
        references = {}
        for category in categories:
            all_assets = glob.glob(os.path.join(root, category, "**/*.usd"), recursive=True)

            # Filter out large files (which can prevent OOM errors during training)
            if max_asset_size is None:
                assets_filtered = all_assets
            else:
                assets_filtered = []
                for a in all_assets:
                    if os.stat(a).st_size > max_asset_size * 1e6:
                        print(f"{a} skipped as it exceeded the max size {max_asset_size} MB.")
                    else:
                        assets_filtered.append(a)

            num_assets = len(assets_filtered)
            if num_assets == 0:
                raise ValueError(f"No USDs found for category {category} under max size {max_asset_size} MB.")

            if train:
                references[category] = assets_filtered[: int(num_assets * split)]
            else:
                references[category] = assets_filtered[int(num_assets * split) :]
        return references

    def create_prim(
        self, path, prim_type, translation=None, rotation=None, scale=None, ref=None, semantic_label=None, attributes={}
    ):
        """Create a prim, apply specified transforms, apply semantic label and
        set specified attributes.

        args:
            path (str): The path of the new prim.
            prim_type (str): Prim type name
            translation (tuple(float, float, float), optional): prim translation (applied last)
            rotation (tuple(float, float, float), optional): prim rotation in radians with rotation
                order ZYX.
            scale (tuple(float, float, float), optional): scaling factor in x, y, z.
            ref (str, optional): Path to the USD that this prim will reference.
            semantic_label (str, optional): Semantic label.
            attributes (dict, optional): Key-value pairs of prim attributes to set.
        """
        prim = self.stage.DefinePrim(path, prim_type)

        for k, v in attributes.items():
            prim.GetAttribute(k).Set(v)
        xform_api = UsdGeom.XformCommonAPI(prim)
        if ref:
            prim.GetReferences().AddReference(ref)
        if semantic_label:
            sem = Semantics.SemanticsAPI.Apply(prim, "Semantics")
            sem.CreateSemanticTypeAttr()
            sem.CreateSemanticDataAttr()
            sem.GetSemanticTypeAttr().Set("class")
            sem.GetSemanticDataAttr().Set(semantic_label)
        if rotation:
            xform_api.SetRotate(rotation, UsdGeom.XformCommonAPI.RotationOrderZYX)
        if scale:
            xform_api.SetScale(scale)
        if translation:
            xform_api.SetTranslate(translation)
        return prim

    def _add_preview_surface(self, prim, diffuse, roughness, metallic):
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

    def load_single_asset(self, ref, semantic_label, suffix=""):
        """Load a USD asset with random pose.
        args
            ref (str): Path to the USD that this prim will reference.
            semantic_label (str): Semantic label.
            suffix (str): String to add to the end of the prim's path.
        """
        x = random.uniform(*RANDOM_TRANSLATION_X)
        z = random.uniform(*RANDOM_TRANSLATION_Z)
        rot_y = random.uniform(*RANDOM_ROTATION_Y)
        asset = self.create_prim(
            f"/World/Asset/mesh{suffix}",
            "Xform",
            translation=(0, 50, 0),
            scale=(SCALE, SCALE, SCALE),
            rotation=(0.0, rot_y, 0.0),
            ref=ref,
            semantic_label=semantic_label,
        )
        # bound = UsdGeom.Mesh(asset).ComputeWorldBound(0.0, "default")
        # box_min_y = bound.GetBox().GetMin()[1]
        # UsdGeom.XformCommonAPI(asset).SetTranslate((x, -box_min_y, z))

        from omni.physx.scripts import utils

        # Add physics to prims
        utils.setRigidBody(asset, "boundingCube", False)
        # Set Mass to 1 kg
        mass_api = PhysicsSchema.MassAPI.Apply(asset)
        mass_api.CreateMassAttr(1)
        return asset

    def populate_scene(self):
        """populate scene with assets."""
        self.assets = []
        num_assets = random.randint(*self.range_num_assets)
        for i in range(num_assets):
            category = random.choice(list(self.references.keys()))
            ref = random.choice(self.references[category])
            self.assets.append(self.load_single_asset(ref, category, i))

    def randomize_asset_material(self):
        """Ranomize asset material properties"""
        for asset in self.assets:
            mtl_created_list = []
            self.kit.execute(
                "CreateAndBindMdlMaterialFromLibrary",
                mdl_name="OmniGlass.mdl",
                mtl_name="OmniGlass",
                mtl_created_list=mtl_created_list,
            )
            mtl_prim = self.stage.GetPrimAtPath(mtl_created_list[0])

            # Set material inputs, these can be determined by looking at the .mdl file
            # or by selecting the Shader attached to the Material in the stage window and looking at the details panel
            color = Gf.Vec3f(random.random(), random.random(), random.random())
            omni.kit.usd.create_material_input(mtl_prim, "glass_color", color, Sdf.ValueTypeNames.Color3f)
            omni.kit.usd.create_material_input(mtl_prim, "glass_ior", 1.45, Sdf.ValueTypeNames.Float)
            # Bind the material to the prim
            prim_mat_shade = UsdShade.Material(mtl_prim)
            UsdShade.MaterialBindingAPI(asset).Bind(prim_mat_shade, UsdShade.Tokens.strongerThanDescendants)

    def randomize_camera(self):
        """Randomize the camera position."""
        # By simply rotating a camera "rig" instead repositioning the camera
        # itself, we greatly simplify our job.

        # Clear previous transforms
        self.camera_rig.ClearXformOpOrder()
        # Change azimuth angle
        self.camera_rig.AddRotateYOp().Set(random.random() * 360)
        # Change elevation angle
        self.camera_rig.AddRotateXOp().Set(random.random() * -90)

    def __iter__(self):
        return self

    def __next__(self):
        # Generate a new scene
        setup_task = asyncio.ensure_future(self.setup_world())
        # # Add objects in the scene
        while not setup_task.done():
            self.kit.update()

        self.setup_physics()
        self.populate_scene()
        self.randomize_camera()

        # force RT mode for better performance while simulating physics
        self.kit.set_setting("/rtx/rendermode", "RayTracedLighting")

        # start simulation
        self.kit.play()
        # Step simulation so that objects fall to rest
        # wait until all materials are loaded
        frame = 0
        print("simulating physics...")
        while frame < 60 or self.kit.is_loading():
            self.kit.update(1 / 60.0)
            frame = frame + 1
        print("done")

        # pause simulation to capture frame
        self.kit.pause()

        # Collect Groundtruth in RT mode
        gt = self.sd_helper.get_groundtruth(["boundingBox2DTight", "instanceSegmentation", "semanticSegmentation"])

        # Once we have the ground truth captured, update materials and re-render to get final RGB image
        self.randomize_asset_material()
        # step once and then wait for materials to load
        self.kit.update()
        print("waiting for materials to load...")
        while self.kit.is_loading():
            self.kit.update()
        print("done")
        # Return to user specified render mode
        self.kit.set_setting("/rtx/rendermode", RENDER_CONFIG["renderer"])
        # Collect Groundtruth in PT mode for RGB only
        gt_pt = self.sd_helper.get_groundtruth(["rgb"])

        # everything is captured, stop simulating
        self.kit.stop()

        # RGB
        # Drop alpha channel
        image = gt_pt["rgb"][..., :3]
        # Cast to tensor if numpy array
        if isinstance(gt_pt["rgb"], np.ndarray):
            image = torch.tensor(image, dtype=torch.float, device="cuda")
        # Normalize between 0. and 1. and change order to channel-first.
        image = image.float() / 255.0
        image = image.permute(2, 0, 1)

        # Bounding Box
        gt_bbox = gt["boundingBox2DTight"]

        # Create mapping from categories to index
        mapping = {cat: i + 1 for i, cat in enumerate(self.categories)}
        bboxes = torch.tensor(gt_bbox[["x_min", "y_min", "x_max", "y_max"]].tolist())
        # For each bounding box, map semantic label to label index
        labels = torch.LongTensor([mapping[bb["semanticLabel"]] for bb in gt_bbox])

        # Calculate bounding box area for each area
        areas = (bboxes[:, 2] - bboxes[:, 0]) * (bboxes[:, 3] - bboxes[:, 1])
        # Idenfiy invalid bounding boxes to filter final output
        valid_areas = (areas > 0.0) * (areas < (image.shape[1] * image.shape[2]))
        print("valid_areas", valid_areas)
        # Instance Segmentation
        _, masks = gt["instanceSegmentation"]
        print("masks", masks.shape)
        if isinstance(masks, np.ndarray):
            masks = torch.tensor(masks, device="cuda")
        # Semantic Segmentation
        _, classes = gt["semanticSegmentation"]
        print("classes", classes.shape)
        if isinstance(classes, np.ndarray):
            classes = torch.tensor(classes, device="cuda")

        target = {
            "boxes": bboxes[valid_areas],
            "labels": labels[valid_areas],
            "masks": masks[valid_areas],
            "classes": classes,
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
    from omni_dl_examples.helpers import visualization as vis

    parser = argparse.ArgumentParser("Dataset test")
    parser.add_argument("--categories", type=str, nargs="+", required=True, help="List of object classes to use")
    parser.add_argument(
        "--max-asset-size",
        type=float,
        default=10.0,
        help="Maximum asset size to use in MB. Larger assets will be skipped.",
    )
    parser.add_argument(
        "--root",
        type=str,
        default=None,
        help="Root directory containing USDs. If not specified, use {SHAPENET_LOCAL_DIR}_nomat as root.",
    )
    args = parser.parse_args()

    # If root is not specified use the environment variable SHAPENET_LOCAL_DIR with the _nomat suffix as root
    if args.root is None:
        args.root = f"{os.path.abspath(os.environ['SHAPENET_LOCAL_DIR'])}_nomat"

    # If ShapeNet categories are specified with their names, convert to synset ID
    # Remove this if using with a different dataset than ShapeNet
    args.categories = [shapenet.LABEL_TO_SYNSET.get(c, c) for c in args.categories]

    dataset = RandomObjects(args.root, args.categories, max_asset_size=args.max_asset_size)

    # Iterate through dataset and visualize the output
    plt.ion()
    _, axes = plt.subplots(1, 3, figsize=(10, 5))
    plt.tight_layout()
    for image, target in dataset:
        for ax in axes:
            ax.clear()
            ax.axis("off")

        np_image = image.permute(1, 2, 0).cpu().numpy()
        axes[0].imshow(np_image)
        axes[0].set_title("RGB")

        num_instances = len(target["boxes"])
        colours = vis.random_colours(num_instances)
        overlay = np.zeros_like(np_image)
        for mask, colour in zip(target["masks"].cpu().numpy(), colours):
            overlay[mask, :3] = colour

        axes[1].imshow(overlay)
        axes[1].set_title("Instance Image with Tight BBox")

        mapping = {i + 1: cat for i, cat in enumerate(args.categories)}
        labels = [shapenet.SYNSET_TO_LABEL[mapping[label.item()]] for label in target["labels"]]
        vis.plot_boxes(axes[1], target["boxes"].tolist(), labels=labels, colours=colours)

        num_classes = target["classes"].shape[0]
        colours = vis.random_colours(num_classes)
        overlay = np.zeros_like(np_image)
        for mask, colour in zip(target["classes"].cpu().numpy(), colours):
            overlay[mask, :3] = colour

        axes[2].imshow(overlay)
        axes[2].set_title("Semantic Image")

        plt.draw()
        plt.pause(0.01)
