# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
"""Generate a synthetic dataset similar to the YCB Video Dataset, which can be used to train a PoseCNN model.
"""

import os
import torch
import signal
import argparse
import numpy as np
import carb
import json
from omni.isaac.kit import SimulationApp

parser = argparse.ArgumentParser("Pose Generation data generator")
parser.add_argument("--num_mesh", type=int, default=30, help="Number of frames to record similar to MESH dataset")
parser.add_argument("--num_dome", type=int, default=30, help="Number of frames to record similar to DOME dataset")
parser.add_argument("--max_queue_size", type=int, default=500, help="Max size of queue to store and process data")
parser.add_argument("--output_folder", "-o", type=str, default="output", help="Output directory.")
args, unknown_args = parser.parse_known_args()

# Path to config file:
CONFIG_FILE = "ycb_config.json"

CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", CONFIG_FILE)

with open(CONFIG_FILE_PATH) as f:
    config_data = json.load(f)

# Default rendering parameters
CONFIG = config_data["CONFIG"]

# Index of part in array of classes in PoseCNN training
CLASS_NAME_TO_INDEX = config_data["CLASS_NAME_TO_INDEX"]

# Maximum force component to apply to objects to keep them in motion
FORCE_RANGE = config_data["FORCE_RANGE"]

# Camera Intrinsics
WIDTH = config_data["WIDTH"]
HEIGHT = config_data["HEIGHT"]
F_X = config_data["F_X"]
F_Y = config_data["F_Y"]
C_X = config_data["C_X"]
C_Y = config_data["C_Y"]

# Default Camera Horizontal Aperture
HORIZONTAL_APERTURE = config_data["HORIZONTAL_APERTURE"]

# Number of sphere lights added to the scene
NUM_LIGHTS = config_data["NUM_LIGHTS"]

# Minimum and maximum distances of objects away from the camera (along the optical axis)
MIN_DISTANCE = config_data["MIN_DISTANCE"]
MAX_DISTANCE = config_data["MAX_DISTANCE"]

# Rotation of camera rig with respect to world frame, expressed as XYZ euler angles
CAMERA_RIG_ROTATION = np.array(config_data["CAMERA_RIG_ROTATION"])

# Rotation of camera with respect to camera rig, expressed as XYZ euler angles. Please note that in this example, we
# define poses with respect to the camera rig instead of the camera prim. By using the rig's frame as a surrogate for
# the camera's frame, we effectively change the coordinate system of the camera. When
# CAMERA_ROTATION = np.array([0, 0, 0]), this corresponds to the default Isaac-Sim camera coordinate system of -z out
# the face of the camera, +x to the right, and +y up. When CAMERA_ROTATION = np.array([180, 0, 0]), this corresponds to
# the YCB Video Dataset camera coordinate system of +z out the face of the camera, +x to the right, and +y down.
CAMERA_ROTATION = np.array(config_data["CAMERA_ROTATION"])

# Minimum and maximum XYZ euler angles for the part being trained on to be rotated, with respect to the camera rig
MIN_ROTATION_RANGE = np.array(config_data["MIN_ROTATION_RANGE"])
MAX_ROTATION_RANGE = np.array(config_data["MAX_ROTATION_RANGE"])

# How close the center of the part being trained on is allowed to be to the edge of the screen
FRACTION_TO_SCREEN_EDGE = config_data["FRACTION_TO_SCREEN_EDGE"]

# MESH and DOME datasets
SHAPE_SCALE = np.array(config_data["SHAPE_SCALE"])
SHAPE_MASS = config_data["SHAPE_MASS"]
OBJECT_SCALE = np.array(config_data["OBJECT_SCALE"])
OBJECT_MASS = config_data["OBJECT_MASS"]

# MESH dataset
NUM_MESH_SHAPES = config_data["NUM_MESH_SHAPES"]
NUM_MESH_OBJECTS = config_data["NUM_MESH_OBJECTS"]
MESH_FRACTION_GLASS = config_data["MESH_FRACTION_GLASS"]

# DOME dataset
NUM_DOME_SHAPES = config_data["NUM_DOME_SHAPES"]
NUM_DOME_OBJECTS = config_data["NUM_DOME_OBJECTS"]
DOME_FRACTION_GLASS = config_data["DOME_FRACTION_GLASS"]
DOME_TEXTURES = config_data["DOME_TEXTURES"]

kit = SimulationApp(launch_config=CONFIG)

from omni.isaac.core.utils.stage import is_stage_loading
from omni.isaac.core import World
import omni.replicator.core as rep
from omni.replicator.isaac.scripts.writers import YCBVideoWriter
from omni.syntheticdata import SyntheticData
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.semantics import add_update_semantics
from omni.isaac.core.utils.rotations import euler_angles_to_quat
from omni.isaac.core.utils.transformations import tf_matrix_from_pose, pose_from_tf_matrix
from omni.isaac.core.prims import XFormPrim
import math

world = World()
world.reset()

from flying_distractors.collision_box import CollisionBox
from flying_distractors.dynamic_shape_set import DynamicShapeSet
from flying_distractors.dynamic_object import DynamicObject
from flying_distractors.dynamic_object_set import DynamicObjectSet
from flying_distractors.flying_distractors import FlyingDistractors
from utils import save_points_xyz, get_world_pose_from_relative, get_random_world_pose_in_view


class RandomScenario(torch.utils.data.IterableDataset):
    def __init__(self, max_queue_size, num_mesh, num_dome, output_folder):
        self.result = True
        assets_root_path = get_assets_root_path()
        if assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            self.result = False
            return
        self.dome_texture_path = assets_root_path + "/NVIDIA/Assets/Skies/"
        self.ycb_asset_path = assets_root_path + "/Isaac/Props/YCB/Axis_Aligned/"
        self.asset_path = assets_root_path + "/Isaac/Props/YCB/Axis_Aligned/"

        self.light_paths = []
        self.train_parts = []
        self.train_part_mesh_path_to_prim_path_map = {}
        self.mesh_distractors = FlyingDistractors()
        self.dome_distractors = FlyingDistractors()
        self.mesh_recording_active = True

        self.max_queue_size = max_queue_size
        self.data_writer = None
        self.num_mesh = num_mesh
        self.num_dome = num_dome
        self.train_size = num_mesh + num_dome

        self._output_folder = os.path.join(os.getcwd(), output_folder)

        self._setup_world()

        self.cur_idx = 0
        self.exiting = False

        signal.signal(signal.SIGINT, self._handle_exit)

    def _handle_exit(self, *args, **kwargs):
        print("Exiting dataset generation..")
        self.exiting = True

    def _setup_world(self):
        """Populate scene with assets and prepare for synthetic data generation.
        """
        # Setup camera in simulation
        focal_length = HORIZONTAL_APERTURE * F_X / WIDTH

        # Setup camera and render product
        self.camera = rep.create.camera(
            position=(0, 0, -MAX_DISTANCE),
            rotation=CAMERA_ROTATION,
            focal_length=focal_length,
            clipping_range=(0.01, 10000),
        )

        self.render_product = rep.create.render_product(self.camera, (WIDTH, HEIGHT))

        camera_node = self.camera.node
        camera_xform_path = rep.utils.get_node_targets(camera_node, "inputs:prims")[0]
        self.camera_path = str(camera_xform_path) + "/Camera"

        with rep.get.prims(prim_types=["Camera"]):
            rep.modify.pose(rotation=rep.distribution.uniform((0, 0, 0), (0, 0, 0)))

        # Define a prim relative to the camera with the camera's rotation "undone". Poses will be defined with respect to this prim.
        camera_orientation = euler_angles_to_quat(CAMERA_ROTATION, degrees=True)
        camera_transform = tf_matrix_from_pose(translation=(0, 0, 0), orientation=camera_orientation)
        camera_transform_inv = np.linalg.inv(camera_transform)
        _, rig_local_orientation = pose_from_tf_matrix(camera_transform_inv)

        self.rig = XFormPrim(
            prim_path=f"{self.camera_path}/rig", translation=np.array([0, 0, 0]), orientation=rig_local_orientation
        )

        rep.settings.set_render_rtx_realtime()

        # Allow flying distractors to float
        world.get_physics_context().set_gravity(0.0)

        # Create a collision box in view of the camera, allowing distractors placed in the box to be within
        # [MIN_DISTANCE, MAX_DISTANCE] of the camera. The collision box will be placed in front of the camera,
        # regardless of CAMERA_ROTATION or CAMERA_RIG_ROTATION.
        self.fov_x = 2 * math.atan(WIDTH / (2 * F_X))
        self.fov_y = 2 * math.atan(HEIGHT / (2 * F_Y))
        theta_x = self.fov_x / 2.0
        theta_y = self.fov_y / 2.0

        # Collision box dimensions lower than 1.3 do not work properly
        collision_box_width = max(2 * MAX_DISTANCE * math.tan(theta_x), 1.3)
        collision_box_height = max(2 * MAX_DISTANCE * math.tan(theta_y), 1.3)
        collision_box_depth = MAX_DISTANCE - MIN_DISTANCE

        collision_box_path = "/World/collision_box"
        collision_box_name = "collision_box"

        # Collision box is centered between MIN_DISTANCE and MAX_DISTANCE, with translation relative to camera in the z
        # direction being negative due to cameras in Isaac Sim having coordinates of -z out, +y up, and +x right.
        collision_box_translation_from_camera = np.array([0, 0, -(MIN_DISTANCE + MAX_DISTANCE) / 2.0])

        # Collision box has no rotation with respect to the camera.
        collision_box_rotation_from_camera = np.array([0, 0, 0])
        collision_box_orientation_from_camera = euler_angles_to_quat(collision_box_rotation_from_camera, degrees=True)

        # Render a frame to ensure the Replicator Camera's underlying USD attributes are populated.
        world.render()

        # Get the desired pose of the collision box from a pose defined locally with respect to the camera.
        collision_box_center, collision_box_orientation = get_world_pose_from_relative(
            self.camera_path, collision_box_translation_from_camera, collision_box_orientation_from_camera
        )

        collision_box = CollisionBox(
            collision_box_path,
            collision_box_name,
            position=collision_box_center,
            orientation=collision_box_orientation,
            width=collision_box_width,
            height=collision_box_height,
            depth=collision_box_depth,
        )
        world.scene.add(collision_box)

        usd_filename_prefix_list = [
            "002_master_chef_can",
            "004_sugar_box",
            "005_tomato_soup_can",
            "006_mustard_bottle",
            "007_tuna_fish_can",
            "008_pudding_box",
            "009_gelatin_box",
            "010_potted_meat_can",
            "011_banana",
            "019_pitcher_base",
            "021_bleach_cleanser",
            "024_bowl",
            "025_mug",
            "035_power_drill",
            "036_wood_block",
            "037_scissors",
            "040_large_marker",
            "051_large_clamp",
            "052_extra_large_clamp",
            "061_foam_brick",
        ]

        usd_path_list = [
            f"{self.ycb_asset_path}{usd_filename_prefix}.usd" for usd_filename_prefix in usd_filename_prefix_list
        ]
        mesh_list = [f"_{usd_filename_prefix[1:]}" for usd_filename_prefix in usd_filename_prefix_list]

        # Distractors for the MESH dataset
        mesh_shape_set = DynamicShapeSet(
            "/World/mesh_shape_set",
            "mesh_shape_set",
            "mesh_shape",
            "mesh_shape",
            NUM_MESH_SHAPES,
            collision_box,
            scale=SHAPE_SCALE,
            mass=SHAPE_MASS,
            fraction_glass=MESH_FRACTION_GLASS,
        )
        self.mesh_distractors.add(mesh_shape_set)

        mesh_object_set = DynamicObjectSet(
            "/World/mesh_object_set",
            "mesh_object_set",
            usd_path_list,
            mesh_list,
            "mesh_object",
            "mesh_object",
            NUM_MESH_OBJECTS,
            collision_box,
            scale=OBJECT_SCALE,
            mass=OBJECT_MASS,
            fraction_glass=MESH_FRACTION_GLASS,
        )
        self.mesh_distractors.add(mesh_object_set)

        # Distractors for the DOME dataset
        dome_shape_set = DynamicShapeSet(
            "/World/dome_shape_set",
            "dome_shape_set",
            "dome_shape",
            "dome_shape",
            NUM_DOME_SHAPES,
            collision_box,
            scale=SHAPE_SCALE,
            mass=SHAPE_MASS,
            fraction_glass=DOME_FRACTION_GLASS,
        )
        self.dome_distractors.add(dome_shape_set)

        dome_object_set = DynamicObjectSet(
            "/World/dome_object_set",
            "dome_object_set",
            usd_path_list,
            mesh_list,
            "dome_object",
            "dome_object",
            NUM_DOME_OBJECTS,
            collision_box,
            scale=OBJECT_SCALE,
            mass=OBJECT_MASS,
            fraction_glass=DOME_FRACTION_GLASS,
        )
        self.dome_distractors.add(dome_object_set)

        # Add the part to train the network on
        part_name = "003_cracker_box"
        ref_path = self.asset_path + part_name + ".usd"
        prim_type = f"_{part_name[1:]}"
        path = "/World/" + prim_type
        mesh_path = path + "/" + prim_type
        name = "train_part"

        self.train_part_mesh_path_to_prim_path_map[mesh_path] = path

        train_part = DynamicObject(
            usd_path=ref_path,
            prim_path=path,
            mesh_path=mesh_path,
            name=name,
            position=np.array([0.0, 0.0, 0.0]),
            scale=OBJECT_SCALE,
            mass=1.0,
        )

        train_part.prim.GetAttribute("physics:rigidBodyEnabled").Set(False)

        self.train_parts.append(train_part)

        # Add semantic information
        mesh_prim = world.stage.GetPrimAtPath(mesh_path)
        add_update_semantics(mesh_prim, prim_type)

        # Save the vertices of the part in '.xyz' format. This will be used in one of PoseCNN's loss functions
        save_points_xyz(path, mesh_path, prim_type, self._output_folder)

        self._setup_randomizers()

        while is_stage_loading():
            kit.app.update()

        self._register_pose_annotator()
        self._setup_writer()

        world.play()
        world.step()
        world.step()

        self.dome_distractors.set_visible(False)

    def _setup_randomizers(self):
        """Add domain randomization with Replicator Randomizers
        """
        # Create and randomize sphere lights
        def randomize_sphere_lights():
            lights = rep.create.light(
                light_type="Sphere",
                color=rep.distribution.uniform((0.0, 0.0, 0.0), (1.0, 1.0, 1.0)),
                intensity=rep.distribution.uniform(100000, 3000000),
                position=rep.distribution.uniform((-250, -250, -250), (250, 250, 100)),
                scale=rep.distribution.uniform(1, 20),
                count=NUM_LIGHTS,
            )
            return lights.node

        # Randomize prim colors
        def randomize_colors(prim_path_regex):
            prims = rep.get.prims(path_pattern=prim_path_regex)
            mats = rep.create.material_omnipbr(
                metallic=rep.distribution.uniform(0.0, 1.0),
                roughness=rep.distribution.uniform(0.0, 1.0),
                diffuse=rep.distribution.uniform((0, 0, 0), (1, 1, 1)),
                count=100,
            )
            with prims:
                rep.randomizer.materials(mats)
            return prims.node

        rep.randomizer.register(randomize_sphere_lights, override=True)
        rep.randomizer.register(randomize_colors, override=True)

        with rep.trigger.on_frame():
            rep.randomizer.randomize_sphere_lights()
            rep.randomizer.randomize_colors("(?=.*shape)(?=.*nonglass).*")

    def _register_pose_annotator(self):
        """Register custom pose annotator, specifying its upstream inputs required for computation and its output data
           type.
        """
        NodeConnectionTemplate = SyntheticData.NodeConnectionTemplate

        rep.AnnotatorRegistry.register_annotator_from_node(
            name="PoseSync",
            input_rendervars=[
                NodeConnectionTemplate(
                    "PostProcessDispatch", attributes_mapping={"outputs:swhFrameNumber": "inputs:syncValue"}
                ),
                NodeConnectionTemplate("CameraParams", attributes_mapping={"outputs:exec": "inputs:execIn"}),
                NodeConnectionTemplate("InstanceMapping", attributes_mapping={"outputs:exec": "inputs:execIn"}),
            ],
            node_type_id="omni.graph.action.SyncGate",
        )

        rep.AnnotatorRegistry.register_annotator_from_node(
            name="pose",
            input_rendervars=[
                NodeConnectionTemplate("PoseSync", attributes_mapping={"outputs:execOut": "inputs:exec"}),
                "InstanceMapping",
                "CameraParams",
            ],
            node_type_id="omni.replicator.isaac.Pose",
            init_params={"getCenters": True},
            output_data_type=np.dtype(
                [
                    ("semanticId", "<u4"),
                    ("prims_to_desired_camera", "<f4", (4, 4)),
                    ("center_coords_image_space", "<f4", (2,)),
                ]
            ),
            output_is_2d=False,
        )

    def _setup_writer(self):
        """Setup the YCB Video Dataset writer and attach it to a render product.
        """
        # Initialize and attach writer
        self.writer = rep.WriterRegistry.get("YCBVideoWriter")
        self.writer.initialize(
            output_dir=self._output_folder,
            num_frames=self.train_size,
            semantic_types=None,
            rgb=True,
            bounding_box_2d_tight=True,
            semantic_segmentation=True,
            distance_to_image_plane=True,
            pose=True,
            class_name_to_index_map=CLASS_NAME_TO_INDEX,
            factor_depth=10000,
            intrinsic_matrix=np.array([[F_X, 0, C_X], [0, F_Y, C_Y], [0, 0, 1]]),
        )

        self.writer.attach([self.render_product])

        # TODO Is this needed/generating an extra frame?
        world.step()

    def randomize_movement_in_view(self, prim):
        """Randomly move and rotate prim such that it stays in view of camera.

        Args:
            prim (DynamicObject): prim to randomly move and rotate.
        """
        translation, orientation = get_random_world_pose_in_view(
            self.camera_path,
            MIN_DISTANCE,
            MAX_DISTANCE,
            self.fov_x,
            self.fov_y,
            FRACTION_TO_SCREEN_EDGE,
            self.rig.prim_path,
            MIN_ROTATION_RANGE,
            MAX_ROTATION_RANGE,
        )

        prim.set_world_pose(translation, orientation)

    def __iter__(self):
        return self

    def __next__(self):
        if self.cur_idx == self.num_mesh:  # MESH datset generation complete, switch to DOME dataset

            rep.orchestrator.stop()  # This is necessary to ensure that the first new frame will have been randomized

            # Increase subframes to 3 to clear the frames in flight and ensure dome light texture is loaded
            rep.settings.carb_settings("/omni/replicator/RTSubframes", 3)

            self.mesh_recording_active = False

            # Hide the FlyingDistractors used for the MESH dataset
            self.mesh_distractors.set_visible(False)

            # Show the FlyingDistractors used for the DOME dataset
            self.dome_distractors.set_visible(True)

            # Create and randomize a dome light for the DOME dataset
            def randomize_domelight(texture_paths):
                lights = rep.create.light(
                    light_type="Dome",
                    rotation=rep.distribution.uniform((0, 0, 0), (360, 360, 360)),
                    texture=rep.distribution.choice(texture_paths),
                )

                return lights.node

            rep.randomizer.register(randomize_domelight, override=True)

            dome_texture_paths = [self.dome_texture_path + dome_texture + ".hdr" for dome_texture in DOME_TEXTURES]

            with rep.trigger.on_frame():
                rep.randomizer.randomize_domelight(dome_texture_paths)

            world.step(render=False)

        if self.mesh_recording_active:
            flying_distractors = self.mesh_distractors
        else:
            flying_distractors = self.dome_distractors

        flying_distractors.apply_force_to_assets(FORCE_RANGE)

        flying_distractors.randomize_asset_glass_color()

        for train_part in self.train_parts:
            self.randomize_movement_in_view(train_part)

        world.step(render=False)

        rep.settings.carb_settings("/rtx/rendermode", "RaytracedLighting")  # temporary fix, remove once 1.3.6 is out
        rep.orchestrator.step()

        self.cur_idx += 1

        return


dataset = RandomScenario(
    max_queue_size=args.max_queue_size, num_mesh=args.num_mesh, num_dome=args.num_dome, output_folder=args.output_folder
)

num_frames = args.num_mesh + args.num_dome

if dataset.result:
    # Iterate through dataset and visualize the output
    print("Loading materials. Will generate data soon...")

    import datetime

    start_time = datetime.datetime.now()
    print("start:", start_time.strftime("%m/%d/%Y, %H:%M:%S"))

    for image in dataset:
        print("ID: ", dataset.cur_idx)
        if dataset.cur_idx == num_frames:
            break
        if dataset.exiting:
            break

    # Stop the simulation
    world.stop()

    print("end:", datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    print("Total time taken: ", str(datetime.datetime.now() - start_time).split(".")[0])

kit.update()

# cleanup
kit.close()
