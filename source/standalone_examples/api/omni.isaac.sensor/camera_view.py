# Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

import os

import matplotlib.pyplot as plt
import numpy as np
import omni.isaac.core.utils.numpy.rotations as rot_utils
import omni.replicator.core as rep
from omni.isaac.core import World
from omni.isaac.core.objects import VisualCuboid
from omni.isaac.core.utils.prims import define_prim
from omni.isaac.core.utils.render_product import set_camera_prim_path
from omni.isaac.sensor import Camera, CameraView
from PIL import Image
from pxr import Gf, UsdGeom

my_world = World(stage_units_in_meters=1.0)

cube_1 = my_world.scene.add(
    VisualCuboid(
        prim_path="/new_cube_1",
        name="cube_1",
        position=np.array([0, 0, 0.2]),
        scale=np.array([0.1, 0.1, 0.1]),
        size=1.0,
        color=np.array([0, 0, 255]),
    )
)

cube_2 = my_world.scene.add(
    VisualCuboid(
        prim_path="/new_cube_2",
        name="cube_2",
        position=np.array([0, 0.5, 0.2]),
        scale=np.array([0.1, 0.1, 0.1]),
        size=1.0,
        color=np.array([0, 0, 255]),
    )
)

camera_01 = rep.create.camera(position=(1, 1, 1), look_at=(0, 0, 0))
camera_02 = rep.create.camera(position=(0, 1, 1), look_at=(0, 0, 0))
camera_03 = rep.create.camera(position=(1, 1, 0), look_at=(0, 0, 0))
camera_04 = rep.create.camera(position=(1, 0, 1), look_at=(0, 0, 0))

my_world.scene.add_default_ground_plane()
my_world.reset()

camera_view = CameraView(
    name="camera_prim_view", prim_paths_expr="/Replicator/Camera_Xform*/Camera", output_annotators=["rgb", "depth"]
)

i = 0
os.makedirs("output_camera_view", exist_ok=True)
while simulation_app.is_running():
    my_world.step(render=True)

    rgba = camera_view.get_rgba().astype(np.uint8)
    print(f"rgba.shape: {rgba.shape}")
    rgba_img = Image.fromarray(rgba)
    rgba_img.save(f"output_camera_view/{str(i).zfill(6)}_rgba.png")

    depth = camera_view.get_depth().astype(np.uint8)
    print(f"depth.shape: {depth.shape}")

    depth_img = Image.fromarray(depth)
    depth_img.save(f"output_camera_view/{str(i).zfill(6)}_depth.png")
    simulation_app.update()

    print(f"camera_view.get_local_poses(camera_axes='ros'): {camera_view.get_local_poses(camera_axes='ros')}")
    print(f"camera_view.get_local_poses(camera_axes='usd'): {camera_view.get_local_poses(camera_axes='usd')}")
    print(f"camera_view.get_local_poses(camera_axes='world'): {camera_view.get_local_poses(camera_axes='world')}")
    print(f"camera_view.get_world_poses(): {camera_view.get_world_poses()}")

    print(f"camera_view.get_focal_lengths(): {camera_view.get_focal_lengths()}")
    print(f"camera_view.get_focus_distances(): {camera_view.get_focus_distances()}")
    print(f"camera_view.get_lens_apertures(): {camera_view.get_lens_apertures()}")
    print(f"camera_view.get_horizontal_apertures(): {camera_view.get_horizontal_apertures()}")
    print(f"camera_view.get_vertical_apertures(): {camera_view.get_vertical_apertures()}")
    print(f"camera_view.get_projection_types(): {camera_view.get_projection_types()}")
    print(f"camera_view.get_projection_modes(): {camera_view.get_projection_modes()}")
    print(f"camera_view.get_stereo_roles(): {camera_view.get_stereo_roles()}")
    print(f"camera_view.get_shutter_properties(): {camera_view.get_shutter_properties()}")

    print(
        f"camera_view.set_shutter_properties(): {camera_view.set_shutter_properties(camera_view.get_shutter_properties())}"
    )

    print(f"camera_view.get_focus_distances(): {camera_view.get_focus_distances()}")

    if i == 10:
        break

    i += 1


simulation_app.close()
