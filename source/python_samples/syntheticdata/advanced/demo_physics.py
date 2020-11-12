#!/usr/bin/env python
# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


"""Demonstration of using OmniKit to generate a scene, collect groundtruth and visualize
the results. This advanced sample also simulates physics and uses a custom glass material
"""

import os
import random
import numpy as np
from pxr import UsdGeom, Semantics
from omni.isaac.synthetic_utils import visualization as vis
from omni.isaac.synthetic_utils import camera
from omni.isaac.synthetic_utils import OmniKitHelper
from omni.isaac.synthetic_utils import SyntheticDataHelper
from omni.isaac.synthetic_utils import utils as ut
import matplotlib.pyplot as plt

from pxr import Gf, Sdf, UsdShade, PhysicsSchema, PhysxSchema, PhysicsSchemaTools

TRANSLATION_RANGE = 300.0
SCALE = 50.0

# specify a custom config
CUSTOM_CONFIG = {
    "width": 1024,
    "height": 1024,
    "renderer": "PathTracing",
    "samples_per_pixel_per_frame": 128,
    "max_bounces": 10,
    "max_specular_transmission_bounces": 6,
    "max_volume_bounces": 4,
    "subdiv_refinement_level": 2,
    "headless": True,
    "experience": f'{os.environ["EXP_PATH"]}/isaac-sim-python.json',
}


def main():
    kit = OmniKitHelper(CUSTOM_CONFIG)
    sd_helper = SyntheticDataHelper()

    from omni.physx.scripts import utils
    import omni

    # SCENE SETUP
    # Get the current stage
    stage = kit.get_stage()

    # Add a sphere light
    kit.create_prim(
        "/World/Light1",
        "SphereLight",
        translation=(0, 200, 0),
        attributes={"radius": 100, "intensity": 100000.0, "color": (1, 1, 1)},
    )

    # Add physics scene
    scene = PhysicsSchema.PhysicsScene.Define(stage, Sdf.Path("/World/physicsScene"))
    # Set gravity vector
    scene.CreateGravityAttr().Set(Gf.Vec3f(0, -981.0, 0))
    # Set physics scene to use cpu physics
    PhysxSchema.PhysxSceneAPI.Apply(stage.GetPrimAtPath("/World/physicsScene"))
    physxSceneAPI = PhysxSchema.PhysxSceneAPI.Get(stage, "/World/physicsScene")
    physxSceneAPI.CreatePhysxSceneEnableCCDAttr(True)
    physxSceneAPI.CreatePhysxSceneEnableStabilizationAttr(True)
    physxSceneAPI.CreatePhysxSceneEnableGPUDynamicsAttr(False)
    physxSceneAPI.CreatePhysxSceneBroadphaseTypeAttr("MBP")
    physxSceneAPI.CreatePhysxSceneSolverTypeAttr("TGS")

    # Create a ground plane
    PhysicsSchemaTools.addGroundPlane(stage, "/World/groundPlane", "Y", 1000, Gf.Vec3f(0, -100, 0), Gf.Vec3f(1.0))

    # Create 10 randomly positioned and coloured spheres and cube
    # We will assign each a semantic label based on their shape (sphere/cube/cone)
    prims = []
    for i in range(10):
        prim_type = random.choice(["Cube", "Sphere", "Cylinder"])
        prim = stage.DefinePrim(f"/World/cube{i}", prim_type)
        translation = np.random.rand(3) * TRANSLATION_RANGE
        UsdGeom.XformCommonAPI(prim).SetTranslate(translation.tolist())
        UsdGeom.XformCommonAPI(prim).SetScale((SCALE, SCALE, SCALE))
        # prim.GetAttribute("primvars:displayColor").Set([np.random.rand(3).tolist()])

        # Add semantic label based on prim type
        sem = Semantics.SemanticsAPI.Apply(prim, "Semantics")
        sem.CreateSemanticTypeAttr()
        sem.CreateSemanticDataAttr()
        sem.GetSemanticTypeAttr().Set("class")
        sem.GetSemanticDataAttr().Set(prim_type)

        # Add physics to prims
        utils.setRigidBody(prim, "convexHull", False)
        # Set Mass to 1 kg
        mass_api = PhysicsSchema.MassAPI.Apply(prim)
        mass_api.CreateMassAttr(1)
        # add prim reference to list
        prims.append(prim)

    # Apply glass material
    for prim in prims:
        # Create Glass material
        mtl_created_list = []
        kit.execute(
            "CreateAndBindMdlMaterialFromLibrary",
            mdl_name="OmniGlass.mdl",
            mtl_name="OmniGlass",
            mtl_created_list=mtl_created_list,
        )
        mtl_prim = stage.GetPrimAtPath(mtl_created_list[0])

        # Set material inputs, these can be determined by looking at the .mdl file
        # or by selecting the Shader attached to the Material in the stage window and looking at the details panel
        color = Gf.Vec3f(random.random(), random.random(), random.random())
        omni.usd.create_material_input(mtl_prim, "glass_color", color, Sdf.ValueTypeNames.Color3f)
        omni.usd.create_material_input(mtl_prim, "glass_ior", 1.25, Sdf.ValueTypeNames.Float)
        # This value is the volumetric light absorption scale, reduce to zero to make glass clearer
        omni.usd.create_material_input(mtl_prim, "depth", 0.001, Sdf.ValueTypeNames.Float)
        # Enable for thin glass objects if needed
        omni.usd.create_material_input(mtl_prim, "thin_walled", False, Sdf.ValueTypeNames.Bool)
        # Bind the material to the prim
        prim_mat_shade = UsdShade.Material(mtl_prim)
        UsdShade.MaterialBindingAPI(prim).Bind(prim_mat_shade, UsdShade.Tokens.strongerThanDescendants)

    # force RayTracedLighting mode for better performance while simulating physics
    kit.set_setting("/rtx/rendermode", "RayTracedLighting")

    # start simulation
    kit.play()
    # Step simulation so that objects fall to rest
    # wait until all materials are loaded
    frame = 0
    print("simulating physics...")
    while frame < 60 or kit.is_loading():
        kit.update(1 / 60.0)
        frame = frame + 1
    print("done")

    # Return to user specified render mode
    kit.set_setting("/rtx/rendermode", CUSTOM_CONFIG["renderer"])
    print("capturing...")
    # Get groundtruth using glass material
    gt = sd_helper.get_groundtruth(
        [
            "rgb",
            "camera",
            "depth",
            "boundingBox2DTight",
            "boundingBox2DLoose",
            "instanceSegmentation",
            "semanticSegmentation",
            "boundingBox3D",
        ]
    )
    print("done")
    # everything is captured, stop simulating
    kit.stop()
    print("visualize results")
    # GROUNDTRUTH VISUALIZATION
    # Setup a figure
    _, axes = plt.subplots(2, 4, figsize=(20, 7))
    axes = axes.flat
    for ax in axes:
        ax.axis("off")

    # RGB
    axes[0].set_title("RGB")
    for ax in axes[:-1]:
        ax.imshow(ut.to_numpy(gt["rgb"]))

    # DEPTH
    axes[1].set_title("Depth")
    axes[1].imshow(ut.to_numpy(gt["depth"]))

    # BBOX2D TIGHT
    random.seed(1)
    axes[2].set_title("BBox 2D Tight")
    bboxes = gt["boundingBox2DTight"][["x_min", "y_min", "x_max", "y_max"]]
    labels = gt["boundingBox2DTight"]["semanticLabel"]
    label_ids = gt["boundingBox2DTight"]["semanticId"]
    label_colours = vis.random_colours(max(label_ids) + 1)
    colours = [label_colours[label_id] for label_id in label_ids]
    vis.plot_boxes(axes[2], bboxes, labels=labels, colours=colours)

    # BBOX2D LOOSE
    random.seed(1)
    axes[3].set_title("BBox 2D Loose")
    bboxes = gt["boundingBox2DLoose"][["x_min", "y_min", "x_max", "y_max"]]
    labels = gt["boundingBox2DLoose"]["semanticLabel"]
    label_ids = gt["boundingBox2DLoose"]["semanticId"]
    label_colours = vis.random_colours(max(label_ids) + 1)
    colours = [label_colours[label_id] for label_id in label_ids]
    vis.plot_boxes(axes[3], bboxes, labels=labels, colours=colours)

    # INSTANCE SEGMENTATION
    random.seed(1)
    axes[4].set_title("Instance Segmentation")
    _, instance_seg = gt["instanceSegmentation"]
    instance_rgb = vis.instance_segmentation_to_rgb(ut.to_numpy(instance_seg))
    axes[4].imshow(instance_rgb, alpha=1.0)

    # SEMANTIC SEGMENTATION
    random.seed(1)
    axes[5].set_title("Semantic Segmentation")
    _, semantic_seg = gt["semanticSegmentation"]
    semantic_rgb = vis.semantic_segmentation_to_rgb(ut.to_numpy(semantic_seg))
    axes[5].imshow(semantic_rgb, alpha=1.0)

    # BBOX 3D
    axes[6].set_title("BBox 3D")

    width = gt["camera"]["resolution"]["width"]
    height = gt["camera"]["resolution"]["height"]
    view_proj_mat = gt["camera"]["view_projection_matrix"]
    points = gt["boundingBox3D"].reshape(-1, 3)
    projected = camera.project_points(view_proj_mat, points)[..., :2] * np.array([[width, height]])

    face_idx_list = [[0, 1, 3, 2], [4, 5, 7, 6], [2, 3, 7, 6], [0, 1, 5, 4], [0, 2, 6, 4], [1, 3, 7, 5]]
    colours = vis.random_colours(len(face_idx_list))
    for p in projected.reshape(-1, 8, 2):
        for face_idxs, colour in zip(face_idx_list, colours):
            face = plt.Polygon(p[face_idxs], alpha=0.3, color=colour)
            axes[6].add_patch(face)

    # Display figure
    plt.tight_layout()
    plt.show()
    # uncomment to save to disk
    # plt.savefig("demo_physics.png")


if __name__ == "__main__":
    main()
