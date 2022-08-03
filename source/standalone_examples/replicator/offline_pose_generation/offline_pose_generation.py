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
parser.add_argument("--output_folder", type=str, default="data", help="Output directory.")
parser.add_argument("--use_s3", action="store_true", help="Saves output to s3 bucket. Only supported by DOPE writer.")
parser.add_argument("--endpoint", type=str, default="https://pbss.s8k.io", help="s3 endpoint to write to.")
parser.add_argument(
    "--writer", type=str, default="DOPE", help="Which writer to use to output data. Choose between: [YCBVideo, DOPE]"
)
args, unknown_args = parser.parse_known_args()

CONFIG_FILES = {"dope": "dope_config.json", "ycbvideo": "ycb_config.json"}

# Path to config file:
CONFIG_FILE = CONFIG_FILES[args.writer.lower()]

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
from omni.isaac.synthetic_utils import SyntheticDataHelper, DOPEWriter, YCBVideoWriter
import omni.replicator.core as rep
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.semantics import add_update_semantics
from omni.isaac.core.utils.rotations import euler_angles_to_quat
from pxr import Usd, UsdGeom
import math

world = World()
world.reset()

from flying_distractors.collision_box import CollisionBox
from flying_distractors.dynamic_shape_set import DynamicShapeSet
from flying_distractors.dynamic_object import DynamicObject
from flying_distractors.dynamic_object_set import DynamicObjectSet
from flying_distractors.flying_distractors import FlyingDistractors
from camera_rig import CameraRig
from utils import save_points_xyz, get_world_pose_from_relative


class RandomScenario(torch.utils.data.IterableDataset):
    def __init__(self, max_queue_size, num_mesh, num_dome, output_folder, use_s3=False, endpoint="", writer="dope"):

        self.sd_helper = SyntheticDataHelper()

        if writer == "dope":
            self.writer_helper = DOPEWriter
        elif writer == "ycbvideo":
            self.writer_helper = YCBVideoWriter
        else:
            raise Exception("Invalid writer specified. Please ensure that writer is valid.")

        self.result = True
        assets_root_path = get_assets_root_path()
        if assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            self.result = False
            return
        self.dome_texture_path = assets_root_path + "/NVIDIA/Assets/Skies/"
        self.ycb_asset_path = assets_root_path + "/Isaac/Props/YCB/Axis_Aligned/"
        self.asset_path = assets_root_path + "/Isaac/Props/YCB/Axis_Aligned/"

        self._output_folder = os.getcwd() + "/output"
        if not os.path.exists(self._output_folder):
            os.mkdir(self._output_folder)

        self.light_paths = []
        self.train_parts = []
        self.train_part_mesh_path_to_prim_path_map = {}
        self.mesh_distractors = FlyingDistractors()
        self.dome_distractors = FlyingDistractors()
        self.mesh = True

        self.max_queue_size = max_queue_size
        self.data_writer = None
        self.num_mesh = num_mesh
        self.num_dome = num_dome
        self.train_size = num_mesh + num_dome

        self.output_folder = output_folder
        self.use_s3 = use_s3
        self.endpoint = endpoint

        self._setup_world()
        self.cur_idx = 0
        self.exiting = False

        signal.signal(signal.SIGINT, self._handle_exit)

    def _handle_exit(self, *args, **kwargs):

        print("exiting dataset generation...")
        self.exiting = True

    def _setup_world(self):
        """Populate scene with assets and prepare for synthetic data generation.
        """

        # Setup camera in simulation
        self.camera_rig = CameraRig(
            "/World/Rig",
            "Rig",
            "Camera",
            WIDTH,
            HEIGHT,
            F_X,
            F_Y,
            C_X,
            C_Y,
            camera_rotation=CAMERA_ROTATION,
            position=np.array([0, 0, -MAX_DISTANCE]),
            orientation=euler_angles_to_quat(CAMERA_RIG_ROTATION),
        )

        rep.settings.set_render_rtx_realtime()

        # Allow flying distractors to float
        world.get_physics_context().set_gravity(0.0)

        # Create a collision box in view of the camera, allowing distractors placed in the box to be within
        # [MIN_DISTANCE, MAX_DISTANCE] of the camera. The collision box will be placed in front of the camera,
        # regardless of CAMERA_ROTATION or CAMERA_RIG_ROTATION.
        theta_x = self.camera_rig.fov_x / 2.0
        theta_y = self.camera_rig.fov_y / 2.0

        # collision box dimensions lower than 1.3 do not work properly
        collision_box_width = max(2 * MAX_DISTANCE * math.tan(theta_x), 1.3)
        collision_box_height = max(2 * MAX_DISTANCE * math.tan(theta_y), 1.3)
        collision_box_depth = MAX_DISTANCE - MIN_DISTANCE

        print(
            f"collision_box_width: {collision_box_width} collision_box_height: {collision_box_height} collision_box_depth: {collision_box_depth} "
        )

        collision_box_path = "/World/collision_box"
        collision_box_name = "collision_box"

        # Collision box is centered between MIN_DISTANCE and MAX_DISTANCE, with translation relative to camera in the z
        # direction being negative due to cameras in Isaac Sim having coordinates of -z out, +y up, and +x right.
        collision_box_translation_from_camera = np.array([0, 0, -(MIN_DISTANCE + MAX_DISTANCE) / 2.0])

        # Collision box has no rotation with respect to the camera
        collision_box_rotation_from_camera = np.array([0, 0, 0])
        collision_box_orientation_from_camera = euler_angles_to_quat(collision_box_rotation_from_camera, degrees=True)

        # Get the desired pose of the collision box from a pose defined locally with respect to the camera.
        collision_box_center, collision_box_orientation = get_world_pose_from_relative(
            self.camera_rig.camera_path, collision_box_translation_from_camera, collision_box_orientation_from_camera
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

        if self.writer_helper == YCBVideoWriter:
            # Save the vertices of the part in '.xyz' format. This will be used in one of PoseCNN's loss functions
            save_points_xyz(path, mesh_path, prim_type, self._output_folder)

        # Add domain randomization with Omniverse Replicator Randomizers
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

        while is_stage_loading():
            kit.app.update()

        world.play()

        world.step()
        world.step()

        self.dome_distractors.set_visible(False)

    def get_transform_matrices(self, bbox_data):
        """Get transformation matrices for semantically labeled objects in view using bounding box data.

        Args:
            bbox_data (np.ndarray): Tight bounding box data. See get_bounding_box_2d_tight() in 
                                    omni.syntheticdata.scripts.sensors for more details.

        Returns:
            np.ndarray: Column-major transformation matrices from frame of each visible prim to the world frame. Shape 
                        is (num_visible_prims, 4, 4).
        """
        n = len(bbox_data)
        if n > 0:
            transform_matrices = np.zeros((n, 4, 4))
        else:
            return np.array([[[]]])

        for i, bbox in enumerate(bbox_data):
            mesh_path = bbox[1]
            prim_path = self.train_part_mesh_path_to_prim_path_map[mesh_path]
            prim = world.stage.GetPrimAtPath(prim_path)
            prim_transform_matrix = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
            prim_to_world = np.transpose(prim_transform_matrix)
            transform_matrices[i, ...] = prim_to_world

        return transform_matrices

    def randomize_movement_in_view(self, prim):
        """Randomly move and rotate prim such that it stays in view of camera.

        Args:
            prim (DynamicObject): prim to randomly move and rotate.
        """

        translation, orientation = self.camera_rig.get_random_world_pose_in_view(
            MIN_DISTANCE,
            MAX_DISTANCE,
            FRACTION_TO_SCREEN_EDGE,
            self.camera_rig.prim_path,
            MIN_ROTATION_RANGE,
            MAX_ROTATION_RANGE,
        )

        prim.set_world_pose(translation, orientation)

    def _capture_viewport(self):
        """Capture groundtruth data from the viewport and add the captured data to the data writer's queue.

        Returns:
            np.ndarray: Image data in RGBA order. Shape is (Height, Width, 4).
        """
        image_id = "{:06d}".format(self.cur_idx)

        groundtruth = {
            "IMAGEID": image_id,
            "RGB": {},
            "DEPTH": {},
            "SEMANTIC": {},
            "BBOX2DTIGHT": {},
            "POSE": {},
            "POSEOLD": {},
            "BBOX3D": {},
            "OCCLUSION": {},
        }

        if self.writer_helper == DOPEWriter:
            gt_list = ["rgb", "boundingBox3D", "occlusion"]
        elif self.writer_helper == YCBVideoWriter:
            gt_list = ["rgb", "depthLinear", "boundingBox2DTight", "semanticSegmentation"]

        # Collect Groundtruth
        viewport = self.camera_rig.viewport_window

        # on the first frame make sure sensors are initialized
        if self.cur_idx == 0:
            self.sd_helper.initialize(sensor_names=gt_list, viewport=viewport)
            kit.update()
            kit.update()
        # Render new frame
        kit.update()

        # Collect Groundtruth
        gt = self.sd_helper.get_groundtruth(gt_list, viewport)

        # RGB
        image = gt["rgb"]
        groundtruth["RGB"] = image

        if self.writer_helper == YCBVideoWriter:
            # Depth
            groundtruth["DEPTH"] = gt["depthLinear"].squeeze()

            # Semantic Segmentation
            semantic_data = np.array(
                self.sd_helper.get_mapped_semantic_data(gt["semanticSegmentation"], CLASS_NAME_TO_INDEX)
            )
            semantic_data[semantic_data == 65535] = 0  # deals with invalid semantic id
            groundtruth["SEMANTIC"] = semantic_data

            # 2D Tight BBox
            groundtruth["BBOX2DTIGHT"] = gt["boundingBox2DTight"]

            # Pose
            groundtruth["POSE"]["PRIMSTOWORLD"] = self.get_transform_matrices(gt["boundingBox2DTight"])
            groundtruth["POSE"]["CAMERAINTRINSICS"] = self.camera_rig.get_camera_intrinsic_matrix()

        if self.writer_helper == DOPEWriter:
            groundtruth["POSE"]["INDEXTOCLASSNAME"] = {
                index: class_name for class_name, index in CLASS_NAME_TO_INDEX.items()
            }
            # 3D BBox
            groundtruth["BBOX3D"] = gt["boundingBox3D"]

            # Occlusion
            groundtruth["OCCLUSION"] = gt["occlusion"]

        # Pose
        rig_transform = UsdGeom.Xformable(self.camera_rig.prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
        rig_to_world = np.transpose(rig_transform)
        groundtruth["POSE"]["DESIREDCAMERATOWORLD"] = rig_to_world
        groundtruth["POSE"]["VIEWPARAMS"] = self.sd_helper.generic_helper_lib.get_view_params(
            self.camera_rig.viewport_window
        )
        groundtruth["POSE"]["CLASSNAMETOINDEX"] = CLASS_NAME_TO_INDEX

        self.data_writer.q.put(groundtruth)
        return image

    def __iter__(self):
        return self

    def __next__(self):

        if self.cur_idx == self.num_mesh:  # MESH datset generation complete, switch to DOME dataset

            self.mesh = False

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

        if self.mesh:
            flying_distractors = self.mesh_distractors
        else:
            flying_distractors = self.dome_distractors

        flying_distractors.apply_force_to_assets(FORCE_RANGE)

        flying_distractors.randomize_asset_glass_color()

        for train_part in self.train_parts:
            self.randomize_movement_in_view(train_part)

        rep.orchestrator.preview()

        world.step()

        self._num_worker_threads = 4

        # Write to disk
        if self.data_writer is None:
            if self.writer_helper == DOPEWriter:
                self.data_writer = self.writer_helper(
                    data_dir=self._output_folder,
                    num_worker_threads=self._num_worker_threads,
                    num_frames=self.train_size,
                    max_queue_size=self.max_queue_size,
                    output_folder=self.output_folder,
                    use_s3=self.use_s3,
                    endpoint_url=self.endpoint,
                    bucket_name=self.output_folder,
                )
            elif self.writer_helper == YCBVideoWriter:
                self.data_writer = self.writer_helper(
                    self._output_folder, self._num_worker_threads, self.train_size, self.max_queue_size
                )

            self.data_writer.start_threads()

        image = self._capture_viewport()
        self.cur_idx += 1
        return image


dataset = RandomScenario(
    max_queue_size=args.max_queue_size,
    num_mesh=args.num_mesh,
    num_dome=args.num_dome,
    output_folder=args.output_folder,
    use_s3=args.use_s3,
    endpoint=args.endpoint,
    writer=args.writer.lower(),
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

    # wait until done
    dataset.data_writer.stop_threads()

    # Stop the simulation
    world.stop()

    print("end:", datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    print("Total time taken: ", str(datetime.datetime.now() - start_time).split(".")[0])

# cleanup
kit.close()
