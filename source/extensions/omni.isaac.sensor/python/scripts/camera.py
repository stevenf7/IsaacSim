# Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import copy
import math
from typing import List, Optional, Sequence, Tuple

import carb
import numpy as np
import omni
import omni.graph.core as og
import omni.replicator.core as rep
from omni.isaac.core.prims.base_sensor import BaseSensor
from omni.isaac.core.utils.carb import get_carb_setting
from omni.isaac.core.utils.prims import (
    define_prim,
    get_all_matching_child_prims,
    get_prim_at_path,
    get_prim_path,
    get_prim_type_name,
    is_prim_path_valid,
)
from omni.isaac.core.utils.render_product import get_resolution, set_camera_prim_path, set_resolution
from omni.isaac.core_nodes.bindings import _omni_isaac_core_nodes
from pxr import Sdf, Usd, UsdGeom, Vt

# transforms are read from right to left
# U_R_TRANSFORM means transformation matrix from R frame to U frame
# R indicates the ROS camera convention (computer vision community)
# U indicates the USD camera convention (computer graphics community)
# W indicates the World camera convention (robotics community)

# from ROS camera convention to USD camera convention
U_R_TRANSFORM = np.array([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])

# from USD camera convention to ROS camera convention
R_U_TRANSFORM = np.array([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])

# from USD camera convention to World camera convention
W_U_TRANSFORM = np.array([[0, 0, -1, 0], [-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]])

# from World camera convention to USD camera convention
U_W_TRANSFORM = np.array([[0, -1, 0, 0], [0, 0, 1, 0], [-1, 0, 0, 0], [0, 0, 0, 1]])


class Camera(BaseSensor):
    """Provides high level functions to deal with a camera prim and its attributes/ properties.
    If there is a camera prim present at the path, it will use it. Otherwise, a new Camera prim at
    the specified prim path will be created.

    Args:
        prim_path (str): prim path of the Camera Prim to encapsulate or create.
        name (str, optional): shortname to be used as a key by Scene class.
                                Note: needs to be unique if the object is added to the Scene.
                                Defaults to "camera".
        frequency (Optional[int], optional): Frequency of the sensor (i.e: how often is the data frame updated).
                                             Defaults to None.
        dt (Optional[str], optional): dt of the sensor (i.e: period at which a the data frame updated). Defaults to None.
        resolution (Optional[Tuple[int, int]], optional): resolution of the camera (width, height). Defaults to None.
        position (Optional[Sequence[float]], optional): position in the world frame of the prim. shape is (3, ).
                                                    Defaults to None, which means left unchanged.
        translation (Optional[Sequence[float]], optional): translation in the local frame of the prim
                                                        (with respect to its parent prim). shape is (3, ).
                                                        Defaults to None, which means left unchanged.
        orientation (Optional[Sequence[float]], optional): quaternion orientation in the world/ local frame of the prim
                                                        (depends if translation or position is specified).
                                                        quaternion is scalar-first (w, x, y, z). shape is (4, ).
                                                        Defaults to None, which means left unchanged.
        render_product_path (str): path to an existing render product, will be used instead of creating a new render product
                                   the resolution and camera attached to this render product will be set based on the input arguments.
                                   Note: Using same render product path on two Camera objects with different camera prims, resolutions is not supported
                                   Defaults to None

    """

    def __init__(
        self,
        prim_path: str,
        name: str = "camera",
        frequency: Optional[int] = None,
        dt: Optional[str] = None,
        resolution: Optional[Tuple[int, int]] = None,
        position: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        translation: Optional[np.ndarray] = None,
        render_product_path: str = None,
    ) -> None:
        frequency = frequency
        dt = dt
        self._frequency = -1  # default to processing all frames
        self._render_product = None
        if frequency is not None and dt is not None:
            raise Exception("Frequency and dt can't be both specified.")
        if dt is not None:
            frequency = int(1 / dt)

        if frequency is not None:
            self.set_frequency(frequency)
        else:
            current_rendering_frequency = get_carb_setting(
                carb.settings.get_settings(), "/app/runLoops/main/rateLimitFrequency"
            )
            if current_rendering_frequency is not None:
                self.set_frequency(current_rendering_frequency)

        if resolution is None:
            resolution = (128, 128)
        if is_prim_path_valid(prim_path):
            self._camera_prim = get_prim_at_path(prim_path)
            if get_prim_type_name(prim_path) != "Camera":
                raise Exception("prim path does not correspond to a Camera prim.")
        else:
            # create a camera prim
            carb.log_info("Creating a new Camera prim at path {}".format(prim_path))
            self._camera_prim = UsdGeom.Camera(define_prim(prim_path=prim_path, prim_type="Camera"))
            if orientation is None:
                orientation = [1, 0, 0, 0]
        if render_product_path:
            self._render_product_path = render_product_path
            self.set_resolution(resolution)
            set_camera_prim_path(self._render_product_path, prim_path)
        else:
            self._render_product = rep.create.render_product(prim_path, resolution=resolution)
            self._render_product_path = self._render_product.path
        self._rgb_annotator = rep.AnnotatorRegistry.get_annotator("rgb")
        self._rgb_annotator.attach([self._render_product_path])
        self._supported_annotators = [
            "normals",
            "motion_vectors",
            "occlusion",
            "distance_to_image_plane",
            "distance_to_camera",
            "bounding_box_2d_tight",
            "bounding_box_2d_loose",
            "bounding_box_3d",
            "semantic_segmentation",
            "instance_id_segmentation",
            "instance_segmentation",
            "pointcloud",
        ]
        self._custom_annotators = dict()
        for annotator in self._supported_annotators:
            self._custom_annotators[annotator] = None
        BaseSensor.__init__(
            self, prim_path=prim_path, name=name, position=position, translation=translation, orientation=orientation
        )
        if position is not None and orientation is not None:
            self.set_world_pose(position=position, orientation=orientation)
        elif translation is not None and orientation is not None:
            self.set_local_pose(translation=translation, orientation=orientation)
        elif orientation is not None:
            self.set_local_pose(orientation=orientation)
        if self.prim.GetAttribute("cameraProjectionType").Get() is None:
            self.prim.CreateAttribute("cameraProjectionType", Sdf.ValueTypeNames.Token)
        properties = [
            "fthetaPolyA",
            "fthetaPolyB",
            "fthetaPolyC",
            "fthetaPolyD",
            "fthetaPolyE",
            "fthetaCx",
            "fthetaCy",
            "fthetaWidth",
            "fthetaHeight",
            "fthetaMaxFov",
        ]
        for property_name in properties:
            if self.prim.GetAttribute(property_name).Get() is None:
                self.prim.CreateAttribute(property_name, Sdf.ValueTypeNames.Float)
        self._current_frame = dict()
        self._current_frame["rgba"] = self._backend_utils.create_zeros_tensor(
            shape=[resolution[0], resolution[1], 4], dtype="int32", device=self._device
        )
        self._pause = False
        self._current_frame = dict()
        self._current_frame["rendering_time"] = 0
        self._current_frame["rendering_frame"] = 0
        self._core_nodes_interface = _omni_isaac_core_nodes.acquire_interface()

        self._elapsed_time = 0
        self._previous_time = None
        return

    def __del__(self):
        """detach annotators on destroy and destroy the internal render product if it exists"""
        for annotator in self.supported_annotators:
            getattr(self, "remove_{}_from_frame".format(annotator))()
        if self._render_product is not None:
            self._render_product.destroy()

    @property
    def supported_annotators(self) -> List[str]:
        """
        Returns:
            List[str]: annotators supported by the camera
        """
        return self._supported_annotators

    def get_render_product_path(self) -> str:
        """
        Returns:
            string: gets the path to the render product attached to this camera
        """
        return self._render_product_path

    def set_frequency(self, value: int) -> None:
        """
        Args:
            value (int): sets the frequency to acquire new data frames
        """
        current_rendering_frequency = get_carb_setting(
            carb.settings.get_settings(), "/app/runLoops/main/rateLimitFrequency"
        )
        if current_rendering_frequency is None:
            # Target rendering frequency is not known, processing all frames
            self._frequency = -1
        else:
            if current_rendering_frequency % value != 0:
                raise Exception("frequency of the camera sensor needs to be a divisible by the rendering frequency.")
            self._frequency = value
        return

    def get_frequency(self) -> float:
        """
        Returns:
            float: gets the frequency to acquire new data frames
        """
        return self._frequency

    def set_dt(self, value: float) -> None:
        """
        Args:
            value (float):  sets the dt to acquire new data frames

        """
        current_rendering_frequency = get_carb_setting(
            carb.settings.get_settings(), "/app/runLoops/main/rateLimitFrequency"
        )
        if current_rendering_frequency is None:
            # Target rendering frequency is not known, processing all frames
            self._frequency = -1
        else:
            if value % (1.0 / current_rendering_frequency) != 0:
                raise Exception("dt of the contact sensor needs to be a multiple of the physics frequency.")
            self._frequency = 1.0 / value
        return

    def get_dt(self) -> float:
        """
        Returns:
            float:  gets the dt to acquire new data frames
        """
        return 1.0 / self._frequency

    def get_current_frame(self, clone=False) -> dict:
        """
        Args:
            clone (bool, optional): if True, returns a deepcopy of the current frame. Defaults to False.
        Returns:
            dict: returns the current frame of data
        """
        if clone:
            return copy.deepcopy(self._current_frame)
        else:
            return self._current_frame

    def initialize(self, physics_sim_view=None) -> None:
        """To be called before using this class after a reset of the world

        Args:
            physics_sim_view (_type_, optional): _description_. Defaults to None.
        """
        BaseSensor.initialize(self, physics_sim_view=physics_sim_view)
        self._acquisition_callback = (
            omni.kit.app.get_app_interface()
            .get_update_event_stream()
            .create_subscription_to_pop(self._data_acquisition_callback)
        )
        width, height = self.get_resolution()
        self._current_frame["rgba"] = self._backend_utils.create_zeros_tensor(
            shape=[width, height, 4], dtype="int32", device=self._device
        )
        self._stage_open_callback = (
            omni.usd.get_context()
            .get_stage_event_stream()
            .create_subscription_to_pop_by_type(int(omni.usd.StageEventType.OPENED), self._stage_open_callback_fn)
        )
        timeline = omni.timeline.get_timeline_interface()
        self._timer_reset_callback = timeline.get_timeline_event_stream().create_subscription_to_pop(
            self._timeline_timer_callback_fn
        )
        self._current_frame["rendering_frame"] = 0
        self._current_frame["rendering_time"] = 0
        return

    def post_reset(self) -> None:
        BaseSensor.post_reset(self)
        self._elapsed_time = 0
        self._previous_time = None
        return

    def _stage_open_callback_fn(self, event):
        self._acquisition_callback = None
        self._stage_open_callback = None
        self._timer_reset_callback = None
        return

    def _timeline_timer_callback_fn(self, event):
        if event.type == int(omni.timeline.TimelineEventType.STOP):
            self.pause()
        elif event.type == int(omni.timeline.TimelineEventType.PLAY):
            self.resume()
        return

    def resume(self) -> None:
        """resumes data collection and updating the data frame"""
        self._acquisition_callback = (
            omni.kit.app.get_app_interface()
            .get_update_event_stream()
            .create_subscription_to_pop(self._data_acquisition_callback)
        )
        return

    def pause(self) -> None:
        """pauses data collection and updating the data frame"""
        self._acquisition_callback = None
        return

    def is_paused(self) -> bool:
        """
        Returns:
            bool: is data collection paused.
        """
        return self._acquisition_callback is None

    # TODO105 : ASYNCRENDERING VALIDATION
    def _data_acquisition_callback(self, event: carb.events.IEvent):
        frame_number = (
            og.Controller()
            .node("/Render/PostProcess/SDGPipeline/PostProcessDispatcher")
            .get_attribute("outputs:referenceTimeNumerator")
            .get()
        )
        current_time = self._core_nodes_interface.get_sim_time_at_swh_frame(frame_number)
        if self._previous_time is not None:
            # print("current time, previous time:",current_time, self._previous_time)
            self._elapsed_time += current_time - self._previous_time

        if self._frequency < 0 or self._elapsed_time >= self.get_dt():
            # print("leftover time, elapsed:", current_time % self.get_dt(), self._elapsed_time)
            self._elapsed_time = 0
            self._current_frame["rendering_frame"] = frame_number
            self._current_frame["rgba"] = self._rgb_annotator.get_data()
            self._current_frame["rendering_time"] = current_time
            for key in self._current_frame:
                if key not in ["rgba", "rendering_time", "rendering_frame"]:
                    # to be added: conversion to each backend
                    self._current_frame[key] = self._custom_annotators[key].get_data()
        self._previous_time = current_time
        return

    def set_resolution(self, value: Tuple[int, int]) -> None:
        """

        Args:
            value (Tuple[int, int]): width and height respectively.

        """
        set_resolution(self._render_product_path, value)
        return

    def get_resolution(self) -> Tuple[int, int]:
        """
        Returns:
            Tuple[int, int]: width and height respectively.
        """
        return get_resolution(self._render_product_path)

    def get_aspect_ratio(self) -> float:
        """
        Returns:
            float: ratio between width and height
        """
        width, height = self.get_resolution()
        return width / float(height)

    def get_world_pose(self, camera_axes: str = "world") -> Tuple[np.ndarray, np.ndarray]:
        """Gets prim's pose with respect to the world's frame (always at [0, 0, 0] and unity quaternion not to be confused with /World Prim)

        Args:
            camera_axes (str, optional): camera axes, world is (+Z up, +X forward), ros is (+Y up, +Z forward) and usd is (+Y up and -Z forward). Defaults to "world".

        Returns:
            Tuple[np.ndarray, np.ndarray]: first index is position in the world frame of the prim. shape is (3, ).
                                           second index is quaternion orientation in the world frame of the prim.
                                           quaternion is scalar-first (w, x, y, z). shape is (4, ).
        """
        if camera_axes not in ["world", "ros", "usd"]:
            raise Exception(
                "camera axes passed {} is not supported: accepted values are ["
                "world"
                ", "
                "ros"
                ", "
                "usd"
                "] only".format(camera_axes)
            )
        position, orientation = BaseSensor.get_world_pose(self)
        if camera_axes == "world":
            world_w_cam_u_R = self._backend_utils.quats_to_rot_matrices(orientation)
            u_w_R = self._backend_utils.create_tensor_from_list(
                U_W_TRANSFORM[:3, :3].tolist(), dtype="float32", device=self._device
            )
            orientation = self._backend_utils.rot_matrices_to_quats(self._backend_utils.matmul(world_w_cam_u_R, u_w_R))
        elif camera_axes == "ros":
            world_w_cam_u_R = self._backend_utils.quats_to_rot_matrices(orientation)
            u_r_R = self._backend_utils.create_tensor_from_list(
                U_R_TRANSFORM[:3, :3].tolist(), dtype="float32", device=self._device
            )
            orientation = self._backend_utils.rot_matrices_to_quats(self._backend_utils.matmul(world_w_cam_u_R, u_r_R))
        return position, orientation

    def set_world_pose(
        self,
        position: Optional[Sequence[float]] = None,
        orientation: Optional[Sequence[float]] = None,
        camera_axes: str = "world",
    ) -> None:
        """Sets prim's pose with respect to the world's frame (always at [0, 0, 0] and unity quaternion not to be confused with /World Prim).

        Args:
            position (Optional[Sequence[float]], optional): position in the world frame of the prim. shape is (3, ).
                                                       Defaults to None, which means left unchanged.
            orientation (Optional[Sequence[float]], optional): quaternion orientation in the world frame of the prim.
                                                          quaternion is scalar-first (w, x, y, z). shape is (4, ).
                                                          Defaults to None, which means left unchanged.
            camera_axes (str, optional): camera axes, world is (+Z up, +X forward), ros is (+Y up, +Z forward) and usd is (+Y up and -Z forward). Defaults to "world".
        """
        if camera_axes not in ["world", "ros", "usd"]:
            raise Exception(
                "camera axes passed {} is not supported: accepted values are ["
                "world"
                ", "
                "ros"
                ", "
                "usd"
                "] only".format(camera_axes)
            )
        if orientation is not None:
            if camera_axes == "world":
                orientation = self._backend_utils.convert(orientation, device=self._device)
                world_w_cam_w_R = self._backend_utils.quats_to_rot_matrices(orientation)
                w_u_R = self._backend_utils.create_tensor_from_list(
                    W_U_TRANSFORM[:3, :3].tolist(), dtype="float32", device=self._device
                )
                orientation = self._backend_utils.rot_matrices_to_quats(
                    self._backend_utils.matmul(world_w_cam_w_R, w_u_R)
                )
            elif camera_axes == "ros":
                orientation = self._backend_utils.convert(orientation, device=self._device)
                world_w_cam_r_R = self._backend_utils.quats_to_rot_matrices(orientation)
                r_u_R = self._backend_utils.create_tensor_from_list(
                    R_U_TRANSFORM[:3, :3].tolist(), dtype="float32", device=self._device
                )
                orientation = self._backend_utils.rot_matrices_to_quats(
                    self._backend_utils.matmul(world_w_cam_r_R, r_u_R)
                )
        return BaseSensor.set_world_pose(self, position, orientation)

    def get_local_pose(self, camera_axes: str = "world") -> None:
        """Gets prim's pose with respect to the local frame (the prim's parent frame in the world axes).

        Args:
            camera_axes (str, optional): camera axes, world is (+Z up, +X forward), ros is (+Y up, +Z forward) and usd is (+Y up and -Z forward). Defaults to "world".

        Returns:
            Tuple[np.ndarray, np.ndarray]: first index is position in the local frame of the prim. shape is (3, ).
                                           second index is quaternion orientation in the local frame of the prim.
                                           quaternion is scalar-first (w, x, y, z). shape is (4, ).
        """
        if camera_axes not in ["world", "ros", "usd"]:
            raise Exception(
                "camera axes passed {} is not supported: accepted values are ["
                "world"
                ", "
                "ros"
                ", "
                "usd"
                "] only".format(camera_axes)
            )
        translation, orientation = BaseSensor.get_local_pose(self)
        if camera_axes == "world":
            parent_w_cam_u_R = self._backend_utils.quats_to_rot_matrices(orientation)
            u_w_R = self._backend_utils.create_tensor_from_list(
                U_W_TRANSFORM[:3, :3].tolist(), dtype="float32", device=self._device
            )
            orientation = self._backend_utils.rot_matrices_to_quats(self._backend_utils.matmul(parent_w_cam_u_R, u_w_R))
        elif camera_axes == "ros":
            parent_w_cam_u_R = self._backend_utils.quats_to_rot_matrices(orientation)
            u_r_R = self._backend_utils.create_tensor_from_list(
                U_R_TRANSFORM[:3, :3].tolist(), dtype="float32", device=self._device
            )
            orientation = self._backend_utils.rot_matrices_to_quats(self._backend_utils.matmul(parent_w_cam_u_R, u_r_R))
        return translation, orientation

    def set_local_pose(
        self,
        translation: Optional[Sequence[float]] = None,
        orientation: Optional[Sequence[float]] = None,
        camera_axes: str = "world",
    ) -> None:
        """Sets prim's pose with respect to the local frame (the prim's parent frame in the world axes).

        Args:
            translation (Optional[Sequence[float]], optional): translation in the local frame of the prim
                                                          (with respect to its parent prim). shape is (3, ).
                                                          Defaults to None, which means left unchanged.
            orientation (Optional[Sequence[float]], optional): quaternion orientation in the local frame of the prim.
                                                          quaternion is scalar-first (w, x, y, z). shape is (4, ).
                                                          Defaults to None, which means left unchanged.
            camera_axes (str, optional): camera axes, world is (+Z up, +X forward), ros is (+Y up, +Z forward) and usd is (+Y up and -Z forward). Defaults to "world".
        """
        if camera_axes not in ["world", "ros", "usd"]:
            raise Exception(
                "camera axes passed {} is not supported: accepted values are ["
                "world"
                ", "
                "ros"
                ", "
                "usd"
                "] only".format(camera_axes)
            )
        if orientation is not None:
            if camera_axes == "world":
                orientation = self._backend_utils.convert(orientation, device=self._device)
                parent_w_cam_w_R = self._backend_utils.quats_to_rot_matrices(orientation)
                w_u_R = self._backend_utils.create_tensor_from_list(
                    W_U_TRANSFORM[:3, :3].tolist(), dtype="float32", device=self._device
                )
                orientation = self._backend_utils.rot_matrices_to_quats(
                    self._backend_utils.matmul(parent_w_cam_w_R, w_u_R)
                )
            elif camera_axes == "ros":
                orientation = self._backend_utils.convert(orientation, device=self._device)
                parent_w_cam_r_R = self._backend_utils.quats_to_rot_matrices(orientation)
                r_u_R = self._backend_utils.create_tensor_from_list(
                    R_U_TRANSFORM[:3, :3].tolist(), dtype="float32", device=self._device
                )
                orientation = self._backend_utils.rot_matrices_to_quats(
                    self._backend_utils.matmul(parent_w_cam_r_R, r_u_R)
                )
        return BaseSensor.set_local_pose(self, translation, orientation)

    def add_normals_to_frame(self) -> None:
        """Attach the normals annotator to this camera.
        The normals annotator returns:
            np.array
            shape: (width, height, 4)
            dtype: np.float32
        See more details: https://docs.omniverse.nvidia.com/extensions/latest/ext_replicator/annotators_details.html#normals
        """
        if self._custom_annotators["normals"] is None:
            self._custom_annotators["normals"] = rep.AnnotatorRegistry.get_annotator("normals")
            self._custom_annotators["normals"].attach([self._render_product_path])
        self._current_frame["normals"] = None
        return

    def remove_normals_from_frame(self) -> None:
        if self._custom_annotators["normals"] is not None:
            self._custom_annotators["normals"].detach([self._render_product_path])
            self._custom_annotators["normals"] = None
        self._current_frame.pop("normals", None)

    def add_motion_vectors_to_frame(self) -> None:
        """Attach the motion vectors annotator to this camera.
        The motion vectors annotator returns:
            np.array
            shape: (width, height, 4)
            dtype: np.float32
        See more details: https://docs.omniverse.nvidia.com/extensions/latest/ext_replicator/annotators_details.html#motion-vectors
        """
        if self._custom_annotators["motion_vectors"] is None:
            self._custom_annotators["motion_vectors"] = rep.AnnotatorRegistry.get_annotator("motion_vectors")
            self._custom_annotators["motion_vectors"].attach([self._render_product_path])
        self._current_frame["motion_vectors"] = None
        return

    def remove_motion_vectors_from_frame(self) -> None:
        if self._custom_annotators["motion_vectors"] is not None:
            self._custom_annotators["motion_vectors"].detach([self._render_product_path])
            self._custom_annotators["motion_vectors"] = None
        self._current_frame.pop("motion_vectors", None)

    def add_occlusion_to_frame(self) -> None:
        """Attach the occlusion annotator to this camera.
        The occlusion annotator returns:
            np.array
            shape: (num_objects, 1)
            dtype: np.dtype([("instanceId", "<u4"), ("semanticId", "<u4"), ("occlusionRatio", "<f4")])
        """
        if self._custom_annotators["occlusion"] is None:
            self._custom_annotators["occlusion"] = rep.AnnotatorRegistry.get_annotator("occlusion")
            self._custom_annotators["occlusion"].attach([self._render_product_path])
        self._current_frame["occlusion"] = None
        return

    def remove_occlusion_from_frame(self) -> None:
        if self._custom_annotators["occlusion"] is not None:
            self._custom_annotators["occlusion"].detach([self._render_product_path])
            self._custom_annotators["occlusion"] = None
        self._current_frame.pop("occlusion", None)

    def add_distance_to_image_plane_to_frame(self) -> None:
        """Attach the distance_to_image_plane annotator to this camera.
        The distance_to_image_plane annotator returns:
            np.array
            shape: (width, height, 1)
            dtype: np.float32
        See more details: https://docs.omniverse.nvidia.com/extensions/latest/ext_replicator/annotators_details.html#distance-to-image-plane
        """
        if self._custom_annotators["distance_to_image_plane"] is None:
            self._custom_annotators["distance_to_image_plane"] = rep.AnnotatorRegistry.get_annotator(
                "distance_to_image_plane"
            )
            self._custom_annotators["distance_to_image_plane"].attach([self._render_product_path])
        self._current_frame["distance_to_image_plane"] = None
        return

    def remove_distance_to_image_plane_from_frame(self) -> None:
        if self._custom_annotators["distance_to_image_plane"] is not None:
            self._custom_annotators["distance_to_image_plane"].detach([self._render_product_path])
            self._custom_annotators["distance_to_image_plane"] = None
        self._current_frame.pop("distance_to_image_plane", None)

    def add_distance_to_camera_to_frame(self) -> None:
        """Attach the distance_to_camera_to_frame annotator to this camera.
        The distance_to_camera_to_frame annotator returns:
            np.array
            shape: (width, height, 1)
            dtype: np.float32
        See more details: https://docs.omniverse.nvidia.com/extensions/latest/ext_replicator/annotators_details.html#distance-to-camera
        """
        if self._custom_annotators["distance_to_camera"] is None:
            self._custom_annotators["distance_to_camera"] = rep.AnnotatorRegistry.get_annotator("distance_to_camera")
            self._custom_annotators["distance_to_camera"].attach([self._render_product_path])
        self._current_frame["distance_to_camera"] = None
        return

    def remove_distance_to_camera_from_frame(self) -> None:
        if self._custom_annotators["distance_to_camera"] is not None:
            self._custom_annotators["distance_to_camera"].detach([self._render_product_path])
            self._custom_annotators["distance_to_camera"] = None
        self._current_frame.pop("distance_to_camera", None)

    def add_bounding_box_2d_tight_to_frame(self) -> None:
        """Attach the bounding_box_2d_tight annotator to this camera.
        The bounding_box_2d_tight annotator returns:
            np.array
            shape: (num_objects, 1)
            dtype: np.dtype([
                                ("semanticId", "<u4"),
                                ("x_min", "<i4"),
                                ("y_min", "<i4"),
                                ("x_max", "<i4"),
                                ("y_max", "<i4"),
                                ("occlusionRatio", "<f4"),
                            ])
        See more details: https://docs.omniverse.nvidia.com/extensions/latest/ext_replicator/annotators_details.html#bounding-box-2d-tight
        """

        if self._custom_annotators["bounding_box_2d_tight"] is None:
            self._custom_annotators["bounding_box_2d_tight"] = rep.AnnotatorRegistry.get_annotator(
                "bounding_box_2d_tight"
            )
            self._custom_annotators["bounding_box_2d_tight"].attach([self._render_product_path])
        self._current_frame["bounding_box_2d_tight"] = None
        return

    def remove_bounding_box_2d_tight_from_frame(self) -> None:
        if self._custom_annotators["bounding_box_2d_tight"] is not None:
            self._custom_annotators["bounding_box_2d_tight"].detach([self._render_product_path])
            self._custom_annotators["bounding_box_2d_tight"] = None
        self._current_frame.pop("bounding_box_2d_tight", None)

    def add_bounding_box_2d_loose_to_frame(self) -> None:
        """Attach the bounding_box_2d_loose annotator to this camera.
        The bounding_box_2d_loose annotator returns:
            np.array
            shape: (num_objects, 1)
            dtype: np.dtype([
                                ("semanticId", "<u4"),
                                ("x_min", "<i4"),
                                ("y_min", "<i4"),
                                ("x_max", "<i4"),
                                ("y_max", "<i4"),
                                ("occlusionRatio", "<f4"),
                            ])
        See more details: https://docs.omniverse.nvidia.com/extensions/latest/ext_replicator/annotators_details.html#bounding-box-2d-loose
        """
        if self._custom_annotators["bounding_box_2d_loose"] is None:
            self._custom_annotators["bounding_box_2d_loose"] = rep.AnnotatorRegistry.get_annotator(
                "bounding_box_2d_loose"
            )
            self._custom_annotators["bounding_box_2d_loose"].attach([self._render_product_path])
        self._current_frame["bounding_box_2d_loose"] = None
        return

    def remove_bounding_box_2d_loose_from_frame(self) -> None:
        if self._custom_annotators["bounding_box_2d_loose"] is not None:
            self._custom_annotators["bounding_box_2d_loose"].detach([self._render_product_path])
            self._custom_annotators["bounding_box_2d_loose"] = None
        self._current_frame.pop("bounding_box_2d_loose", None)

    def add_bounding_box_3d_to_frame(self) -> None:
        if self._custom_annotators["bounding_box_3d"] is None:
            self._custom_annotators["bounding_box_3d"] = rep.AnnotatorRegistry.get_annotator("bounding_box_3d")
            self._custom_annotators["bounding_box_3d"].attach([self._render_product_path])
        self._current_frame["bounding_box_3d"] = None
        return

    def remove_bounding_box_3d_from_frame(self) -> None:
        if self._custom_annotators["bounding_box_3d"] is not None:
            self._custom_annotators["bounding_box_3d"].detach([self._render_product_path])
            self._custom_annotators["bounding_box_3d"] = None
        self._current_frame.pop("bounding_box_3d", None)

    def add_semantic_segmentation_to_frame(self) -> None:
        """Attach the semantic_segmentation annotator to this camera.
        The semantic_segmentation annotator returns:
            np.array
            shape: (width, height, 1) or (width, height, 4) if `colorize` is set to true
            dtype: np.uint32 or np.uint8 if `colorize` is set to true
        See more details: https://docs.omniverse.nvidia.com/extensions/latest/ext_replicator/annotators_details.html#semantic-segmentation
        """
        if self._custom_annotators["semantic_segmentation"] is None:
            self._custom_annotators["semantic_segmentation"] = rep.AnnotatorRegistry.get_annotator(
                "semantic_segmentation"
            )
            self._custom_annotators["semantic_segmentation"].attach([self._render_product_path])
        self._current_frame["semantic_segmentation"] = None
        return

    def remove_semantic_segmentation_from_frame(self) -> None:
        if self._custom_annotators["semantic_segmentation"] is not None:
            self._custom_annotators["semantic_segmentation"].detach([self._render_product_path])
            self._custom_annotators["semantic_segmentation"] = None
        self._current_frame.pop("semantic_segmentation", None)

    def add_instance_id_segmentation_to_frame(self) -> None:
        """Attach the instance_id_segmentation annotator to this camera.
        The instance_id_segmentation annotator returns:
            np.array
            shape: (width, height, 1) or (width, height, 4) if `colorize` is set to true
            dtype: np.uint32 or np.uint8 if `colorize` is set to true
        See more details: https://docs.omniverse.nvidia.com/extensions/latest/ext_replicator/annotators_details.html#instance-id-segmentation
        """
        if self._custom_annotators["instance_id_segmentation"] is None:
            self._custom_annotators["instance_id_segmentation"] = rep.AnnotatorRegistry.get_annotator(
                "instance_id_segmentation"
            )
            self._custom_annotators["instance_id_segmentation"].attach([self._render_product_path])
        self._current_frame["instance_id_segmentation"] = None
        return

    def remove_instance_id_segmentation_from_frame(self) -> None:
        if self._custom_annotators["instance_id_segmentation"] is not None:
            self._custom_annotators["instance_id_segmentation"].detach([self._render_product_path])
            self._custom_annotators["instance_id_segmentation"] = None
        self._current_frame.pop("instance_id_segmentation", None)

    def add_instance_segmentation_to_frame(self) -> None:
        """Attach the instance_segmentation annotator to this camera.
        The main difference between instance id segmentation and instance segmentation are that instance segmentation annotator goes down the hierarchy to the lowest level prim which has semantic labels, which instance id segmentation always goes down to the leaf prim.
        The instance_segmentation annotator returns:
            np.array
            shape: (width, height, 1) or (width, height, 4) if `colorize` is set to true
            dtype: np.uint32 or np.uint8 if `colorize` is set to true
        See more details: https://docs.omniverse.nvidia.com/extensions/latest/ext_replicator/annotators_details.html#instance-segmentation
        """
        if self._custom_annotators["instance_segmentation"] is None:
            self._custom_annotators["instance_segmentation"] = rep.AnnotatorRegistry.get_annotator(
                "instance_segmentation"
            )
            self._custom_annotators["instance_segmentation"].attach([self._render_product_path])
        self._current_frame["instance_segmentation"] = None
        return

    def remove_instance_segmentation_from_frame(self) -> None:
        if self._custom_annotators["instance_segmentation"] is not None:
            self._custom_annotators["instance_segmentation"].detach([self._render_product_path])
            self._custom_annotators["instance_segmentation"] = None
        self._current_frame.pop("instance_segmentation", None)

    def add_pointcloud_to_frame(self, include_unlabelled: bool = False):
        """Attach the pointcloud annotator to this camera.
        The pointcloud annotator returns:
            np.array
            shape: (num_points, 3)
            dtype: np.float32
        See more details: https://docs.omniverse.nvidia.com/extensions/latest/ext_replicator/annotators_details.html#point-cloud
        """
        if self._custom_annotators["pointcloud"] is None:
            self._custom_annotators["pointcloud"] = rep.AnnotatorRegistry.get_annotator(
                "pointcloud", init_params={"includeUnlabelled": include_unlabelled}
            )
            self._custom_annotators["pointcloud"].attach([self._render_product_path])
        self._current_frame["pointcloud"] = None
        return

    def remove_pointcloud_from_frame(self) -> None:
        if self._custom_annotators["pointcloud"] is not None:
            self._custom_annotators["pointcloud"].detach([self._render_product_path])
            self._custom_annotators["pointcloud"] = None
        self._current_frame.pop("pointcloud", None)

    def get_rgba(self) -> np.ndarray:
        """
        Returns:
            rgba (np.ndarray): (N x 4) RGBa color data for each point.
        """
        return self._rgb_annotator.get_data()

    def get_rgb(self) -> np.ndarray:
        """
        Returns:
            rgb (np.ndarray): (N x 3) RGB color data for each point.
        """

        data = self._rgb_annotator.get_data()
        return data[..., :3]

    def get_depth(self) -> np.ndarray:
        """
        Returns:
            depth (np.ndarray): (n x m x 1) depth data for each point.
        """

        data = self.get_current_frame()
        if "distance_to_image_plane" not in data.keys():
            carb.log_warn(
                f"[get_depth][{self.prim_path}] WARNING: Annotator 'distance_to_image_plane' not found. Available annotators: {data.keys()}. Returning None"
            )
            return None

        depth = data["distance_to_image_plane"]
        if depth is None:
            carb.log_warn(
                f"[get_depth][{self.prim_path}] WARNING: Annotator 'distance_to_image_plane' contains no data. Returning None"
            )
            return None
        return depth

    def get_pointcloud(self) -> np.ndarray:
        """
        Returns:
            pointcloud (np.ndarray):  (N x 3) 3d points (X, Y, Z) in camera frame. Shape is (N x 3) where N is the number of points.
        Note:
            This currently uses the depth annotator to generate the pointcloud. In the future, this will be switched to use
            the pointcloud annotator.
        """

        depth = self.get_depth()
        if depth is None:
            carb.log_warn(f"[get_pointcloud][{self.prim_path}] WARNING: Unable to get depth. Returning None")
            return None

        # First, generate a grid of the mesh.
        im_height, im_width = depth.shape[0], depth.shape[1]

        ww = np.linspace(0, im_width - 1, im_width)
        hh = np.linspace(0, im_height - 1, im_height)
        xmap, ymap = np.meshgrid(ww, hh)

        points_2d = np.column_stack((xmap.ravel(), ymap.ravel()))

        # Directly use this function from the camera class to do this.
        pointcloud = self.get_world_points_from_image_coords(points_2d, depth.flatten())

        return pointcloud

    def get_focal_length(self) -> float:
        """
        Returns:
            float: Longer Lens Lengths Narrower FOV, Shorter Lens Lengths Wider FOV
        """
        return self.prim.GetAttribute("focalLength").Get() / 10.0

    def set_focal_length(self, value: float):
        """
        Args:
            value (float): Longer Lens Lengths Narrower FOV, Shorter Lens Lengths Wider FOV
        """
        self.prim.GetAttribute("focalLength").Set(value * 10.0)
        return

    def get_focus_distance(self) -> float:
        """
        Returns:
            float: Distance from the camera to the focus plane (in stage units).
        """
        return self.prim.GetAttribute("focusDistance").Get()

    def set_focus_distance(self, value: float):
        """The distance at which perfect sharpness is achieved.

        Args:
            value (float): Distance from the camera to the focus plane (in stage units).
        """
        self.prim.GetAttribute("focusDistance").Set(value)
        return

    def get_lens_aperture(self) -> float:
        """
        Returns:
            float: controls lens aperture (i.e focusing). 0 turns off focusing.
        """
        return self.prim.GetAttribute("fStop").Get()

    def set_lens_aperture(self, value: float):
        """Controls Distance Blurring. Lower Numbers decrease focus range, larger
            numbers increase it.

        Args:
            value (float): controls lens aperture (i.e focusing). 0 turns off focusing.
        """
        self.prim.GetAttribute("fStop").Set(value)
        return

    def get_horizontal_aperture(self) -> float:
        """_
        Returns:
            float:  Emulates sensor/film width on a camera
        """
        aperture = self.prim.GetAttribute("horizontalAperture").Get() / 10.0
        return aperture

    def set_horizontal_aperture(self, value: float) -> None:
        """
        Args:
            value (Optional[float], optional): Emulates sensor/film width on a camera. Defaults to None.
        """
        self.prim.GetAttribute("horizontalAperture").Set(value * 10.0)
        (width, height) = self.get_resolution()
        self.prim.GetAttribute("verticalAperture").Set((value * 10.0) * (float(height) / width))
        return

    def get_vertical_aperture(self) -> float:
        """
        Returns:
            float: Emulates sensor/film height on a camera.
        """
        aperture = self.prim.GetAttribute("verticalAperture").Get() / 10.0
        return aperture

    def set_vertical_aperture(self, value: float) -> None:
        """
        Args:
            value (Optional[float], optional): Emulates sensor/film height on a camera. Defaults to None.
        """
        self.prim.GetAttribute("verticalAperture").Set(value * 10.0)
        (width, height) = self.get_resolution()
        self.prim.GetAttribute("horizontalAperture").Set((value * 10.0) * (float(width) / height))
        return

    def get_clipping_range(self) -> Tuple[float, float]:
        """
        Returns:
            Tuple[float, float]: near_distance and far_distance respectively.
        """
        near, far = self.prim.GetAttribute("clippingRange").Get()
        return near, far

    def set_clipping_range(self, near_distance: Optional[float] = None, far_distance: Optional[float] = None) -> None:
        """Clips the view outside of both near and far range values.

        Args:
            near_distance (Optional[float], optional): value to be used for near clipping. Defaults to None.
            far_distance (Optional[float], optional): value to be used for far clipping. Defaults to None.
        """
        near, far = self.prim.GetAttribute("clippingRange").Get()
        if near_distance:
            near = near_distance
        if far_distance:
            far = far_distance
        self.prim.GetAttribute("clippingRange").Set((near, far))
        return

    def get_projection_type(self) -> str:
        """
        Returns:
            str: pinhole, fisheyeOrthographic, fisheyeEquidistant, fisheyeEquisolid, fisheyePolynomial or fisheyeSpherical
        """
        projection_type = self.prim.GetAttribute("cameraProjectionType").Get()
        if projection_type is None:
            projection_type = "pinhole"
        return projection_type

    def set_projection_type(self, value: str) -> None:
        """
        Args:
            value (str): pinhole: Standard Camera Projection (Disable Fisheye)
                         fisheyeOrthographic: Full Frame using Orthographic Correction
                         fisheyeEquidistant: Full Frame using Equidistant Correction
                         fisheyeEquisolid: Full Frame using Equisolid Correction
                         fisheyePolynomial: 360 Degree Spherical Projection
                         fisheyeSpherical: 360 Degree Full Frame Projection
        """
        self.prim.GetAttribute("cameraProjectionType").Set(Vt.Token(value))
        return

    def get_projection_mode(self) -> str:
        """
        Returns:
            str: perspective or orthographic.
        """
        return self.prim.GetAttribute("projection").Get()

    def set_projection_mode(self, value: str) -> None:
        """Sets camera to perspective or orthographic mode.

        Args:
            value (str): perspective or orthographic.

        """
        self.prim.GetAttribute("projection").Set(value)
        return

    def get_stereo_role(self) -> str:
        """
        Returns:
            str: mono, left or right.
        """
        return self.prim.GetAttribute("stereoRole").Get()

    def set_stereo_role(self, value: str) -> None:
        """
        Args:
            value (str): mono, left or right.
        """
        self.prim.GetAttribute("stereoRole").Set(value)
        return

    def set_fisheye_polynomial_properties(
        self,
        nominal_width: Optional[float],
        nominal_height: Optional[float],
        optical_centre_x: Optional[float],
        optical_centre_y: Optional[float],
        max_fov: Optional[float],
        polynomial: Optional[Sequence[float]],
    ) -> None:
        """
        Args:
            nominal_width (Optional[float]): Rendered Width (pixels)
            nominal_height (Optional[float]): Rendered Height (pixels)
            optical_centre_x (Optional[float]): Horizontal Render Position (pixels)
            optical_centre_y (Optional[float]): Vertical Render Position (pixels)
            max_fov (Optional[float]): maximum field of view (pixels)
            polynomial (Optional[Sequence[float]]): polynomial equation coefficients
                                                    (sequence of 5 numbers) starting from A0, A1, A2, A3, A4
        """
        if "fisheye" not in self.get_projection_type():
            raise Exception(
                "fisheye projection type is not set to be able to use set_fisheye_polynomial_properties method."
            )
        if nominal_width:
            self.prim.GetAttribute("fthetaWidth").Set(nominal_width)
        if nominal_height:
            self.prim.GetAttribute("fthetaHeight").Set(nominal_height)
        if optical_centre_x:
            self.prim.GetAttribute("fthetaCx").Set(optical_centre_x)
        if optical_centre_y:
            self.prim.GetAttribute("fthetaCy").Set(optical_centre_y)
        if max_fov:
            self.prim.GetAttribute("fthetaMaxFov").Set(max_fov)
        if polynomial is not None:
            for i in range(5):
                if polynomial[i]:
                    self.prim.GetAttribute("fthetaPoly" + (chr(ord("A") + i))).Set(float(polynomial[i]))
        return

    def get_fisheye_polynomial_properties(self) -> Tuple[float, float, float, float, float, List]:
        """
        Returns:
            Tuple[float, float, float, float, float, List]: nominal_width, nominal_height, optical_centre_x,
                                                           optical_centre_y, max_fov and polynomial respectively.
        """
        if "fisheye" not in self.get_projection_type():
            raise Exception(
                "fisheye projection type is not set to be able to use get_fisheye_polynomial_properties method."
            )
        nominal_width = self.prim.GetAttribute("fthetaWidth").Get()
        nominal_height = self.prim.GetAttribute("fthetaHeight").Get()
        optical_centre_x = self.prim.GetAttribute("fthetaCx").Get()
        optical_centre_y = self.prim.GetAttribute("fthetaCy").Get()
        max_fov = self.prim.GetAttribute("fthetaMaxFov").Get()
        polynomial = [None] * 5
        for i in range(5):
            polynomial[i] = self.prim.GetAttribute("fthetaPoly" + (chr(ord("A") + i))).Get()
        return nominal_width, nominal_height, optical_centre_x, optical_centre_y, max_fov, polynomial

    def set_shutter_properties(self, delay_open: Optional[float] = None, delay_close: Optional[float] = None) -> None:
        """
        Args:
            delay_open (Optional[float], optional): Used with Motion Blur to control blur amount,
                                                    increased values delay shutter opening. Defaults to None.
            delay_close (Optional[float], optional): Used with Motion Blur to control blur amount,
                                                    increased values forward the shutter close. Defaults to None.
        """
        if delay_open:
            self.prim.GetAttribute("shutter:open").Set(delay_open)
        if delay_close:
            self.prim.GetAttribute("shutter:close").Set(delay_close)
        return

    def get_shutter_properties(self) -> Tuple[float, float]:
        """
        Returns:
            Tuple[float, float]: delay_open and delay close respectively.
        """
        return self.prim.GetAttribute("shutter:open").Get(), self.prim.GetAttribute("shutter:close").Get()

    def get_view_matrix_ros(self):
        """3D points in World Frame -> 3D points in Camera Ros Frame

        Returns:
            np.ndarray: the view matrix that transforms 3d points in the world frame to 3d points in the camera axes
                        with ros camera convention.
        """
        world_w_cam_u_T = self._backend_utils.transpose_2d(
            UsdGeom.Imageable(self.prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
        )
        return self._backend_utils.matmul(R_U_TRANSFORM, self._backend_utils.inverse(world_w_cam_u_T))

    def get_intrinsics_matrix(self) -> np.ndarray:
        """
        Returns:
            np.ndarray: the intrinsics of the camera (used for calibration)
        """
        if "pinhole" not in self.get_projection_type():
            raise Exception("pinhole projection type is not set to be able to use get_intrinsics_matrix method.")
        focal_length = self.get_focal_length()
        horizontal_aperture = self.get_horizontal_aperture()
        vertical_aperture = self.get_horizontal_aperture()
        (width, height) = self.get_resolution()
        fx = width * focal_length / horizontal_aperture
        fy = height * focal_length / vertical_aperture
        cx = width * 0.5
        cy = height * 0.5
        return self._backend_utils.create_tensor_from_list(
            [[fx, 0.0, cx], [0.0, fy, cy], [0.0, 0.0, 1.0]], dtype="float32", device=self._device
        )

    def get_image_coords_from_world_points(self, points_3d: np.ndarray) -> np.ndarray:
        """Using pinhole perspective projection, this method projects 3d points in the world frame to the image
           plane giving the pixel coordinates [[0, width], [0, height]]

        Args:
            points_3d (np.ndarray): 3d points (X, Y, Z) in world frame. shape is (n, 3) where n is the number of points.

        Returns:
            np.ndarray: 2d points (u, v) corresponds to the pixel coordinates. shape is (n, 2) where n is the number of points.
        """
        if "pinhole" not in self.get_projection_type():
            raise Exception(
                "pinhole projection type is not set to be able to use get_image_coords_from_world_points method which use pinhole prespective projection."
            )
        homogenous = self._backend_utils.pad(points_3d, ((0, 0), (0, 1)), value=1.0)
        projection_matrix = self._backend_utils.matmul(self.get_intrinsics_matrix(), self.get_view_matrix_ros()[:3, :])
        points = self._backend_utils.matmul(projection_matrix, self._backend_utils.transpose_2d(homogenous))
        points[:2, :] /= points[2, :]  # normalize
        return self._backend_utils.transpose_2d(points[:2, :])

    def get_world_points_from_image_coords(self, points_2d: np.ndarray, depth: np.ndarray):
        """Using pinhole perspective projection, this method does the inverse projection given the depth of the
           pixels

        Args:
            points_2d (np.ndarray): 2d points (u, v) corresponds to the pixel coordinates. shape is (n, 2) where n is the number of points.
            depth (np.ndarray): depth corresponds to each of the pixel coords. shape is (n,)

        Returns:
            np.ndarray: (n, 3) 3d points (X, Y, Z) in world frame. shape is (n, 3) where n is the number of points.
        """
        if "pinhole" not in self.get_projection_type():
            raise Exception(
                "pinhole projection type is not set to be able to use get_world_points_from_image_coords method which use pinhole prespective projection."
            )
        homogenous = self._backend_utils.pad(points_2d, ((0, 0), (0, 1)), value=1.0)
        points_in_camera_axes = self._backend_utils.matmul(
            self._backend_utils.inverse(self.get_intrinsics_matrix()),
            self._backend_utils.transpose_2d(homogenous) * self._backend_utils.expand_dims(depth, 0),
        )
        points_in_camera_axes_homogenous = self._backend_utils.pad(points_in_camera_axes, ((0, 1), (0, 0)), value=1.0)
        points_in_world_frame_homogenous = self._backend_utils.matmul(
            self._backend_utils.inverse(self.get_view_matrix_ros()), points_in_camera_axes_homogenous
        )
        return self._backend_utils.transpose_2d(points_in_world_frame_homogenous[:3, :])

    def get_horizontal_fov(self) -> float:
        """
        Returns:
            float: horizontal field of view in pixels
        """
        return 2 * math.atan(self.get_horizontal_aperture() / (2 * self.get_focal_length()))

    def get_vertical_fov(self) -> float:
        """
        Returns:
            float: vertical field of view in pixels
        """
        width, height = self.get_resolution()
        return self.get_horizontal_fov() * (height / float(width))


def get_all_camera_objects(root_prim: str = "/World"):
    """Retrieve omni.isaac.sensor Camera objects for each camera in the scene.

    Args:
        root_prim (str): Root prim where the world exists.

    Returns:
        Camera[]: A list of omni.isaac.sensor Camera objects
    """

    # Get the paths of prims that are of type "Camera" from scene
    camera_prims = get_all_matching_child_prims(
        prim_path=root_prim, predicate=lambda prim: get_prim_type_name(prim) == "Camera"
    )

    # Create a "Camera" object for them
    camera_objects = []
    for prim in camera_prims:
        camera_path_split = get_prim_path(prim).split("/")
        camera = Camera(prim_path=get_prim_path(prim), name=camera_path_split[-1])
        camera_objects.append(camera)

    return camera_objects
