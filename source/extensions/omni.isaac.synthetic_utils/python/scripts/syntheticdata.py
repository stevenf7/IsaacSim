# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


"""Helper class for obtaining groundtruth data from OmniKit.

Support provided for RGB, Depth, Bounding Box (2D Tight, 2D Loose, 3D),
segmentation (instance and semantic), and camera parameters.

    Typical usage example:

    kit = OmniKitHelper()   # Start omniverse kit
    sd_helper = SyntheticDataHelper()
    gt = sd_helper.get_groundtruth(('rgb', 'depth', 'boundingBox2DTight'))

"""

import math
import carb
import omni
import time
from pxr import UsdGeom, Semantics, Gf

import numpy as np


class SyntheticDataHelper:
    def __init__(self):
        self.app = omni.kit.app.get_app_interface()
        ext_manager = self.app.get_extension_manager()
        ext_manager.set_extension_enabled("omni.syntheticdata", True)

        from omni.syntheticdata import sensors, helpers
        import omni.syntheticdata._syntheticdata as sd  # Must be imported after getting app interface

        self.sd = sd

        self.sd_interface = self.sd.acquire_syntheticdata_interface()
        self.viewport = omni.kit.viewport.get_viewport_interface()
        self.carb_settings = carb.settings.acquire_settings_interface()
        self.sensor_helper_lib = sensors
        self.generic_helper_lib = helpers

        mode = "numpy"

        self.sensor_helpers = {
            "rgb": sensors.get_rgb,
            "depth": sensors.get_depth,
            "depthLinear": sensors.get_depth_linear,
            "instanceSegmentation": sensors.get_instance_segmentation,
            "semanticSegmentation": sensors.get_semantic_segmentation,
            "boundingBox2DTight": sensors.get_bounding_box_2d_tight,
            "boundingBox2DLoose": sensors.get_bounding_box_2d_loose,
            "boundingBox3D": sensors.get_bounding_box_3d,
            "camera": self.get_camera_params,
            "pose": self.get_pose,
        }

        self.sensor_types = {
            "rgb": self.sd.SensorType.Rgb,
            "depth": self.sd.SensorType.Depth,
            "depthLinear": self.sd.SensorType.DepthLinear,
            "instanceSegmentation": self.sd.SensorType.InstanceSegmentation,
            "semanticSegmentation": self.sd.SensorType.SemanticSegmentation,
            "boundingBox2DTight": self.sd.SensorType.BoundingBox2DTight,
            "boundingBox2DLoose": self.sd.SensorType.BoundingBox2DLoose,
            "boundingBox3D": self.sd.SensorType.BoundingBox3D,
        }

        self.sensor_state = {s: False for s in list(self.sensor_helpers.keys())}

    def get_camera_params(self, viewport):
        """Get active camera intrinsic and extrinsic parameters.

        Returns:
            A dict of the active camera's parameters.

            pose (numpy.ndarray): camera position in world coordinates,
            fov (float): horizontal field of view in radians
            focal_length (float)
            horizontal_aperture (float)
            view_projection_matrix (numpy.ndarray(dtype=float64, shape=(4, 4)))
            resolution (dict): resolution as a dict with 'width' and 'height'.
            clipping_range (tuple(float, float)): Near and Far clipping values.
        """
        stage = omni.usd.get_context().get_stage()
        prim = stage.GetPrimAtPath(viewport.get_active_camera())
        prim_tf = omni.usd.get_world_transform_matrix(prim)
        focal_length = prim.GetAttribute("focalLength").Get()
        horiz_aperture = prim.GetAttribute("horizontalAperture").Get()
        fov = 2 * math.atan(horiz_aperture / (2 * focal_length))
        width, height = viewport.get_texture_resolution()
        aspect_ratio = width / height
        near, far = prim.GetAttribute("clippingRange").Get()
        view_proj_mat = self.generic_helper_lib.get_view_proj_mat(prim, aspect_ratio, near, far)

        return {
            "pose": np.array(prim_tf),
            "fov": fov,
            "focal_length": focal_length,
            "horizontal_aperture": horiz_aperture,
            "view_projection_matrix": view_proj_mat,
            "resolution": {"width": width, "height": height},
            "clipping_range": (near, far),
        }

    def get_pose(self):
        """Get pose of all objects with a semantic label.
        """
        stage = omni.usd.get_context().get_stage()
        mappings = self.generic_helper_lib.get_instance_mappings()
        pose = []
        for m in mappings:
            prim_path = m[1]
            prim = stage.GetPrimAtPath(prim_path)
            prim_tf = omni.usd.get_world_transform_matrix(prim)
            pose.append((str(prim_path), m[2], str(m[3]), np.array(prim_tf)))
        return pose

    def initialize(self, viewport, sensor_names, timeout=100):
        """ Initialize sensors in the list provided.


        Args:
            viewport (omni.kit.viewport._viewport.IViewportWindow): Viewport from which to retrieve/create sensor.
            sensor_types (list of omni.syntheticdata._syntheticdata.SensorType): List of sensor types to initialize.
            timeout (int): Maximum time in seconds to attempt to initialize sensors.
        """
        start = time.time()
        is_initialized = False
        while not is_initialized and time.time() < (start + timeout):
            sensors = []
            for sensor_name in sensor_names:
                if sensor_name != "camera" and sensor_name != "pose":
                    sensors.append(
                        self.sensor_helper_lib.create_or_retrieve_sensor(viewport, self.sensor_types[sensor_name])
                    )
            self.app.update()
            is_initialized = not any([not self.sd_interface.is_sensor_initialized(s) for s in sensors])
        if not is_initialized:
            unititialized = [s for s in sensors if not self.sd_interface.is_sensor_initialized(s)]
            raise TimeoutError(f"Unable to initialized sensors: [{unititialized}] within {timeout} seconds.")

        self.app.update()  # Extra frame required to prevent access violation error

    def get_groundtruth(self, gt_sensors, viewport, verify_sensor_init=True):
        """Get groundtruth from specified gt_sensors.

        Args:
            gt_sensors (list): List of strings of sensor names. Valid sensors names: rgb, depth,
                instanceSegmentation, semanticSegmentation, boundingBox2DTight,
                boundingBox2DLoose, boundingBox3D, camera
            viewport (omni.kit.viewport._viewport.IViewportWindow): Viewport from which to retrieve/create sensor.
            verify_sensor_init (bool): Additional check to verify creation and initialization of sensors.

        Returns:
            Dict of sensor outputs
        """
        if isinstance(gt_sensors, str):
            gt_sensors = (gt_sensors,)

        # Create and initialize sensors
        if verify_sensor_init:
            self.initialize(viewport, gt_sensors)

        gt = {}
        sensor_state = {}
        # Process non-RT-only sensors
        for sensor in gt_sensors:
            if sensor not in ["camera", "pose"]:
                if sensor == "instanceSegmentation":
                    gt[sensor] = self.sensor_helpers[sensor](viewport, parsed=True, return_mapping=True)
                elif sensor == "boundingBox3D":
                    gt[sensor] = self.sensor_helpers[sensor](viewport, parsed=True, return_corners=True)
                else:
                    gt[sensor] = self.sensor_helpers[sensor](viewport)
                current_sensor = self.sensor_helper_lib.create_or_retrieve_sensor(viewport, self.sensor_types[sensor])
                current_sensor_state = self.sd_interface.is_sensor_initialized(current_sensor)
                sensor_state[sensor] = current_sensor_state
            elif sensor == "pose":
                gt[sensor] = self.sensor_helpers[sensor]()
            else:
                gt[sensor] = self.sensor_helpers[sensor](viewport)
        gt["state"] = sensor_state

        return gt
