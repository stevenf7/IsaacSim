# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import random
import argparse
import carb
from omni.isaac.kit import SimulationApp

CONFIG = {"width": 1280, "height": 720, "sync_loads": True, "headless": True, "renderer": "RayTracedLighting"}

# D435
FOCAL_LEN = 1.93
HORIZONTAL_APERTURE = 2.682
VERTICAL_APERTURE = 1.509
FOCUS_DIST = 400

RANDOMIZE_SCENE_EVERY_N_STEPS = 10

kit = SimulationApp(launch_config=CONFIG)
from omni.isaac.core.utils.extensions import enable_extension
from omni.isaac.core.utils.stage import set_stage_up_axis, add_reference_to_stage
import omni
from pxr import UsdGeom, Gf
import omni.isaac.dr as dr
from omni.isaac.core import SimulationContext
from omni.isaac.core.utils.nucleus_utils import find_nucleus_server
from omni.isaac.core.utils import rotations, prims
import numpy as np

# enable SDK bridge extension
enable_extension("omni.isaac.robot_engine_bridge")

context = SimulationContext(stage_units_in_meters=0.01)
stage = context.stage
viewport = omni.kit.viewport.get_viewport_interface()
set_stage_up_axis("z")

result, nucleus_server = find_nucleus_server()
if result is False:
    carb.log_error("Could not find nucleus server with /Isaac folder")
    kit.close()
    exit()
asset_path = nucleus_server + "/Isaac"
stage_path = asset_path + "/Environments/Simple_Room/simple_room.usd"

environment = stage.DefinePrim("/environment", "Xform")
room = add_reference_to_stage(stage_path, "/environment/room")

# create target prim

target_prim = prims.create_prim(
    stage,
    "/objects/cube",
    "Cube",
    position=np.array([0, 0, 100]),
    scale=np.array([10, 10, 50]),
    semantic_label="target",
)

camera_prim = prims.create_prim(
    stage,
    "/World/Camera",
    "Camera",
    attributes={
        "focusDistance": FOCUS_DIST,
        "focalLength": FOCAL_LEN,
        "horizontalAperture": HORIZONTAL_APERTURE,
        "verticalAperture": VERTICAL_APERTURE,
    },
)
viewport.get_viewport_window().set_active_camera(str(camera_prim.GetPath()))
camera_proxy = prims.create_prim(
    stage,
    "/World/Camera/proxy",
    "Xform",
    orientation=rotations.gf_rotation_to_np_array(Gf.Rotation(Gf.Vec3d(1, 0, 0), 180)),
)

texture_list = [
    asset_path + "/Samples/DR/Materials/Textures/checkered.png",
    asset_path + "/Samples/DR/Materials/Textures/marble_tile.png",
    asset_path + "/Samples/DR/Materials/Textures/picture_a.png",
    asset_path + "/Samples/DR/Materials/Textures/picture_b.png",
    asset_path + "/Samples/DR/Materials/Textures/textured_wall.png",
    asset_path + "/Samples/DR/Materials/Textures/checkered_color.png",
]
base_path = str(room.GetPath())
texture_comp = dr.commands.CreateTextureComponentCommand(
    prim_paths=[base_path], enable_project_uvw=False, texture_list=texture_list
).do()
# self.color_comp = self.dr.commands.CreateColorComponentCommand(prim_paths=[base_path+"/floor"]).do()
# disable automatic DR, we run it ourselves in the step function

# add a movement and rotation component
# the movement component is offset by 100cm in z so that the object remains above the table
movement_comp = dr.commands.CreateMovementComponentCommand(
    prim_paths=[str(target_prim.GetPath())], min_range=(-10, -10, -10 + 100), max_range=(10, 10, 10 + 100)
).do()
rotation_comp = dr.commands.CreateRotationComponentCommand(prim_paths=[str(target_prim.GetPath())]).do()

dr.commands.ToggleManualModeCommand().do()

kit.update()
kit.update()

while kit.is_stage_loading():
    kit.update()

result, occluded_provider = omni.kit.commands.execute(
    "RobotEngineBridgeCreateCamera",
    path="/World/REB_Occluded_Provider",
    parent=None,
    rgb_output_component="output",
    rgb_output_channel="encoder_color",
    depth_output_component="output",
    depth_output_channel="encoder_depth",
    segmentation_output_component="output",
    segmentation_output_channel="encoder_segmentation",
    bbox2d_output_component="output",
    bbox2d_output_channel="encoder_bbox",
    bbox2d_class_list="",
    bbox3d_output_component="output",
    bbox3d_output_channel="encoder_bbox3d",
    bbox3d_class_list="",
    rgb_enabled=True,
    depth_enabled=False,
    segmentaion_enabled=True,
    bbox2d_enabled=False,
    bbox3d_enabled=False,
    camera_prim_rel=[camera_prim.GetPath()],
    resolution=Gf.Vec2i(1280, 720),
)

result, unoccluded_provider = omni.kit.commands.execute(
    "RobotEngineBridgeCreateCamera",
    path="/World/REB_Unoccluded_Provider",
    parent=None,
    rgb_output_component="output",
    rgb_output_channel="decoder_color",
    depth_output_component="output",
    depth_output_channel="decoder_depth",
    segmentation_output_component="output",
    segmentation_output_channel="decoder_segmentation",
    bbox2d_output_component="output",
    bbox2d_output_channel="decoder_bbox",
    bbox2d_class_list="",
    bbox3d_output_component="output",
    bbox3d_output_channel="decoder_bbox3d",
    bbox3d_class_list="",
    rgb_enabled=True,
    depth_enabled=False,
    segmentaion_enabled=True,
    bbox2d_enabled=False,
    bbox3d_enabled=False,
    camera_prim_rel=[camera_prim.GetPath()],
    resolution=Gf.Vec2i(1280, 720),
)

# turn both cameras off so that we don't send an image when time is stepped
occluded_provider.GetEnabledAttr().Set(False)
unoccluded_provider.GetEnabledAttr().Set(False)

# create rigid body sink to publish ground truth pose information
result, rbs_provider = omni.kit.commands.execute(
    "RobotEngineBridgeCreateRigidBodySink",
    path="/World/REB_RigidBodiesSink",
    parent=None,
    enabled=False,
    output_component="output",
    output_channel="bodies",
    rigid_body_prims_rel=[camera_proxy.GetPath(), target_prim.GetPath()],
)
# disable rigid body sink until the final image is sent out so its only published once
rbs_provider.GetEnabledAttr().Set(False)

ext_manager = omni.kit.app.get_app().get_extension_manager()
ext_id = ext_manager.get_enabled_extension_id("omni.isaac.robot_engine_bridge")
reb_extension_path = ext_manager.get_extension_path(ext_id)
app_file = f"{reb_extension_path}/resources/isaac_engine/json/isaacsim.app.json"
carb.log_info(f"create application with: {reb_extension_path} {app_file}")
omni.kit.commands.execute("RobotEngineBridgeCreateApplication", asset_path=reb_extension_path, app_file=app_file)

frame = 0
context.play()


def toggle_environment(state):
    imageable = UsdGeom.Imageable(environment)
    if state:
        imageable.MakeVisible()
    else:
        imageable.MakeInvisible()


parser = argparse.ArgumentParser(description="Generate Occluded and Unoccluded data")
parser.add_argument("--test", action="store_true")
args, unknown = parser.parse_known_args()
# On start if state creation was successful
while kit.is_running():
    # randomize camera every frame
    viewport.get_viewport_window().set_camera_position(
        str(camera_prim.GetPath()),
        random.randrange(-250, 250),
        random.randrange(-250, 250),
        random.randrange(10, 250),
        True,
    )

    # get target pose and point camera at it
    pose = omni.usd.get_world_transform_matrix(target_prim)
    # can specify an offset on target position
    target = pose.ExtractTranslation() + Gf.Vec3d(0, 0, 0)

    viewport.get_viewport_window().set_camera_target(str(camera_prim.GetPath()), target[0], target[1], target[2], True)

    # randomize textures every 10 frames
    if frame % RANDOMIZE_SCENE_EVERY_N_STEPS == 0:
        dr.commands.RandomizeOnceCommand().do()

    toggle_environment(True)
    kit.update()
    # render occluded view
    omni.kit.commands.execute("RobotEngineBridgeTickComponent", path=str(occluded_provider.GetPath()))
    # hide everything but the object
    toggle_environment(False)
    kit.update()
    # render unoccluded view
    omni.kit.commands.execute("RobotEngineBridgeTickComponent", path=str(unoccluded_provider.GetPath()))
    omni.kit.commands.execute("RobotEngineBridgeTickComponent", path=str(rbs_provider.GetPath()))
    # output fps every 100 frames
    if frame % 100 == 0:
        print("FPS: ", viewport.get_viewport_window().get_fps())
    frame = frame + 1
    # in test mode exist after the first frame
    if args.test:
        break
context.stop()
kit.close()
