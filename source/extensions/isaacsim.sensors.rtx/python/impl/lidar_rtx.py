# SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

from typing import Optional, Tuple

import carb
import numpy as np
import omni
import omni.graph.core as og
import omni.replicator.core as rep
from isaacsim.core.api.sensors.base_sensor import BaseSensor
from isaacsim.core.nodes.bindings import _isaacsim_core_nodes
from isaacsim.core.utils.prims import get_prim_at_path, get_prim_type_name, is_prim_path_valid
from omni.syntheticdata import sensors


class LidarRtx(BaseSensor):
    def __init__(
        self,
        prim_path: str,
        name: str = "lidar_rtx",
        position: Optional[np.ndarray] = None,
        translation: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        config_file_name: Optional[str] = None,
        asset_path: Optional[str] = None,
        **kwargs,
    ) -> None:
        DEPRECATED_ARGS = [
            "firing_frequency",
            "firing_dt",
            "rotation_frequency",
            "rotation_dt",
            "valid_range",
            "scan_type",
            "elevation_range",
            "range_resolution",
            "range_accuracy",
            "avg_power",
            "wave_length",
            "pulse_time",
        ]
        for arg in DEPRECATED_ARGS:
            if arg in kwargs:
                carb.log_warn(
                    f"Argument {arg} is deprecated as of Isaac Sim 5.0 and will be removed in a future release."
                )

        if is_prim_path_valid(prim_path):
            if get_prim_type_name(prim_path) == "Camera":
                carb.log_warn(
                    "Support for creating RTXLidar from Camera prims is deprecated as of Isaac Sim 5.0 and will be removed in a future release. Use OmniLidar prim instead."
                )
            elif get_prim_type_name(prim_path) != "OmniLidar":
                raise Exception(f"Prim at {prim_path} is not an OmniLidar.")
            elif not get_prim_at_path(prim_path).HasAPI("OmniSensorGenericLidarCoreAPI"):
                raise Exception(f"Prim at {prim_path} does not have the OmniSensorGenericLidarCoreAPI schema.")
            carb.log_warn("Using existing RTX Lidar prim at path {}".format(prim_path))
        else:
            _, sensor = omni.kit.commands.execute(
                "IsaacSensorCreateRtxLidar", path=prim_path, parent=None, config=config_file_name, asset_path=asset_path
            )

        self._render_product = rep.create.render_product(prim_path, resolution=(1, 1))
        self._render_product_path = self._render_product.path
        self._point_cloud_node_path = None
        self._flat_scan_node_path = None
        self._create_point_cloud_graph_node()
        self._create_flat_scan_graph_node()
        self._debug_draw_node_path = None
        self._core_nodes_interface = _isaacsim_core_nodes.acquire_interface()
        BaseSensor.__init__(
            self, prim_path=prim_path, name=name, translation=translation, position=position, orientation=orientation
        )
        if position is not None and orientation is not None:
            self.set_world_pose(position=position, orientation=orientation)
        elif translation is not None and orientation is not None:
            self.set_local_pose(translation=translation, orientation=orientation)
        elif orientation is not None:
            self.set_local_pose(orientation=orientation)
        self._current_frame = dict()
        self._current_frame["rendering_time"] = 0
        self._current_frame["rendering_frame"] = 0
        self._writer = None

        self._attribute_map = {
            "point_cloud_data": "data",
            "range": "range",
            "azimuth": "azimuth",
            "elevation": "elevation",
            "linear_depth_data": "linearDepthData",
            "intensities_data": "intensitiesData",
            "azimuth_range": "azimuthRange",
            "horizontal_resolution": "horizontalResolution",
        }
        return

    def __del__(self):
        if self._render_product:
            self._render_product.destroy()

    def get_render_product_path(self) -> str:
        """
        Returns:
            string: gets the path to the render product used by the lidar
        """
        return self._render_product_path

    def get_current_frame(self) -> dict:
        return self._current_frame

    def _create_point_cloud_graph_node(self):
        self._point_cloud_annotator = rep.AnnotatorRegistry.get_annotator(
            "RtxSensorCpu" + "IsaacComputeRTXLidarPointCloud"
        )
        self._point_cloud_annotator.attach([self._render_product_path])
        self._point_cloud_node_path = self._point_cloud_annotator.get_node().get_prim_path()
        return

    def _create_flat_scan_graph_node(self):
        self._flat_scan_annotator = rep.AnnotatorRegistry.get_annotator(
            "RtxSensorCpu" + "IsaacComputeRTXLidarFlatScan" + "SimulationTime"
        )
        self._flat_scan_annotator.attach([self._render_product_path])
        self._flat_scan_node_path = self._flat_scan_annotator.get_node().get_prim_path()
        return

    def initialize(self, physics_sim_view=None) -> None:
        BaseSensor.initialize(self, physics_sim_view=physics_sim_view)
        self._acquisition_callback = carb.eventdispatcher.get_eventdispatcher().observe_event(
            event_name=omni.kit.app.GLOBAL_EVENT_UPDATE,
            on_event=self._data_acquisition_callback,
            observer_name="isaacsim.sensors.rtx.LidarRtx.initialize._data_acquisition_callback",
        )
        # self._acquisition_callback = (
        #     omni.kit.app.get_app_interface()
        #     .get_update_event_stream()
        #     .create_subscription_to_pop(self._data_acquisition_callback)
        # )
        self._stage_open_callback = (
            omni.usd.get_context()
            .get_stage_event_stream()
            .create_subscription_to_pop_by_type(int(omni.usd.StageEventType.OPENED), self._stage_open_callback_fn)
        )
        timeline = omni.timeline.get_timeline_interface()
        self._timer_reset_callback = timeline.get_timeline_event_stream().create_subscription_to_pop(
            self._timeline_timer_callback_fn
        )
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

    def post_reset(self) -> None:
        BaseSensor.post_reset(self)
        return

    def resume(self) -> None:
        self._acquisition_callback = carb.eventdispatcher.get_eventdispatcher().observe_event(
            event_name=omni.kit.app.GLOBAL_EVENT_UPDATE,
            on_event=self._data_acquisition_callback,
            observer_name="isaacsim.sensors.rtx.LidarRtx.resume._data_acquisition_callback",
        )
        # self._acquisition_callback = (
        #     omni.kit.app.get_app_interface()
        #     .get_update_event_stream()
        #     .create_subscription_to_pop(self._data_acquisition_callback)
        # )
        return

    def pause(self) -> None:
        self._acquisition_callback = None
        return

    def is_paused(self) -> bool:
        return self._acquisition_callback is None

    def _data_acquisition_callback(self, event: carb.events.IEvent):
        self._current_frame["rendering_frame"] = (
            og.Controller()
            .node("/Render/PostProcess/SDGPipeline/PostProcessDispatcher")
            .get_attribute("outputs:referenceTimeNumerator")
            .get()
        )

        self._current_frame["rendering_time"] = self._core_nodes_interface.get_sim_time_at_swh_frame(
            self._current_frame["rendering_frame"]
        )
        for key in self._current_frame:
            attribute_name = "".join([word[0].upper() + word[1:] for word in key.split("_")])
            attribute_name = attribute_name[0].lower() + attribute_name[1:]
            if key not in ["rendering_time", "rendering_frame"]:
                if key in ["point_cloud_data", "range", "azimuth", "elevation"]:
                    data = self._point_cloud_annotator.get_data()
                    if key == "point_cloud_data":
                        self._current_frame[key] = data[self._attribute_map[key]]
                    else:
                        self._current_frame[key] = data["info"][self._attribute_map[key]]
                elif key in ["linear_depth_data", "intensities_data", "azimuth_range", "horizontal_resolution"]:
                    data = self._flat_scan_annotator.get_data()
                    self._current_frame[key] = data[self._attribute_map[key]]
        return

    def add_point_cloud_data_to_frame(self):
        self._current_frame["point_cloud_data"] = []
        return

    def remove_point_cloud_data_from_frame(self):
        del self._current_frame["point_cloud_data"]
        return

    def add_linear_depth_data_to_frame(self):
        self._current_frame["linear_depth_data"] = []
        return

    def remove_linear_depth_data_from_frame(self):
        del self._current_frame["linear_depth_data"]
        return

    def add_intensities_data_to_frame(self):
        self._current_frame["intensities_data"] = []
        return

    def remove_intensities_data_from_frame(self):
        del self._current_frame["intensities_data"]
        return

    def add_azimuth_range_to_frame(self):
        self._current_frame["azimuth_range"] = []
        return

    def remove_azimuth_range_from_frame(self):
        del self._current_frame["azimuth_range"]
        return

    def add_horizontal_resolution_to_frame(self):
        self._current_frame["horizontal_resolution"] = []
        return

    def remove_horizontal_resolution_from_frame(self):
        del self._current_frame["horizontal_resolution"]
        return

    def add_range_data_to_frame(self):
        self._current_frame["range"] = []
        return

    def remove_range_data_from_frame(self):
        del self._current_frame["range"]
        return

    def add_azimuth_data_to_frame(self):
        self._current_frame["azimuth"] = []
        return

    def remove_azimuth_data_from_frame(self):
        del self._current_frame["azimuth"]
        return

    def add_elevation_data_to_frame(self):
        self._current_frame["elevation"] = []
        return

    def remove_elevation_data_from_frame(self):
        del self._current_frame["elevation"]
        return

    def get_horizontal_resolution(self) -> float:
        return og.Controller().node(self._flat_scan_node_path).get_attribute("outputs:horizontalResolution").get()

    def get_horizontal_fov(self) -> float:
        return og.Controller().node(self._flat_scan_node_path).get_attribute("outputs:horizontalFov").get()

    def get_num_rows(self) -> int:
        return og.Controller().node(self._flat_scan_node_path).get_attribute("outputs:numRows").get()

    def get_num_cols(self) -> int:
        return og.Controller().node(self._flat_scan_node_path).get_attribute("outputs:numCols").get()

    def get_rotation_frequency(self) -> float:
        return og.Controller().node(self._flat_scan_node_path).get_attribute("outputs:rotationRate").get()

    def get_depth_range(self) -> Tuple[float, float]:
        result = og.Controller().node(self._flat_scan_node_path).get_attribute("outputs:depthRange").get()
        return result[0], result[1]

    def get_azimuth_range(self) -> Tuple[float, float]:
        result = og.Controller().node(self._flat_scan_node_path).get_attribute("outputs:azimuthRange").get()
        return result[0], result[1]

    def enable_visualization(self):
        self._writer = rep.writers.get("RtxLidar" + "DebugDrawPointCloud")
        self._writer.initialize()
        self._writer.attach([self._render_product_path])

        return

    def disable_visualization(self):
        if self._writer:
            self._writer.detach()
        self._writer = None
        return
