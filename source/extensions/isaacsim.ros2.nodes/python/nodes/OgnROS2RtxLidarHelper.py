# SPDX-FileCopyrightText: Copyright (c) 2022-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import traceback

import carb
import omni
import omni.isaac.IsaacSensorSchema as IsaacSensorSchema
import omni.replicator.core as rep
import omni.syntheticdata
from isaacsim.core.nodes import BaseWriterNode
from isaacsim.core.utils.carb import get_carb_setting
from isaacsim.core.utils.render_product import get_camera_prim_path
from isaacsim.ros2.core import collect_namespace
from isaacsim.ros2.nodes import build_rtx_sensor_pointcloud_writer
from isaacsim.ros2.nodes.impl.ros2_common import (
    SRTX_SENSOR_SET,
    USE_SRTX_SETTING,
    _start_or_extend_continuous_capture,
    cleanup_srtx_state,
    ensure_render_var_on_product,
)
from pxr import Usd, UsdGeom

LIDAR_AOV = "GenericModelOutput"


class OgnROS2RtxLidarHelperInternalState(BaseWriterNode):
    """Internal state for the ROS2RtxLidarHelper OmniGraph node."""

    def __init__(self) -> None:
        self.viewport = None
        self.viewport_name = ""
        self.resetSimulationTimeOnStop = False
        self.publishStepSize = 1
        self._srtx_callback_handle = None
        self._srtx_capsule = None
        self._srtx_sensor_set = None
        self._srtx_output_path = None
        super().__init__(initialize=False)

    def custom_reset(self) -> None:
        cleanup_srtx_state(self)
        super().custom_reset()

    def post_attach(self, writer, render_product) -> None:
        try:
            omni.syntheticdata.SyntheticData.Get().set_node_attributes(
                "PostProcessDispatch" + "IsaacSimulationGate", {"inputs:step": self.publishStepSize}, render_product
            )
            omni.syntheticdata.SyntheticData.Get().set_node_attributes(
                "IsaacReadSimulationTime", {"inputs:resetOnStop": self.resetSimulationTimeOnStop}, render_product
            )
        except Exception:
            pass


class OgnROS2RtxLidarHelper:
    """OmniGraph node that sets up ROS 2 RTX lidar publishers."""

    @staticmethod
    def internal_state() -> OgnROS2RtxLidarHelperInternalState:
        return OgnROS2RtxLidarHelperInternalState()

    @staticmethod
    def _read_laser_scan_metadata(prim) -> dict | None:
        """Read scan configuration from the lidar prim for LaserScan publishing.

        Args:
            prim: The lidar USD prim (OmniLidar or Camera).

        Returns:
            A dict with keys: azimuth_range_start, azimuth_range_end,
            depth_range_min, depth_range_max, rotation_rate,
            horizontal_resolution, horizontal_fov.
            Returns None on failure.
        """
        if prim.IsA(UsdGeom.Camera):
            carb.log_warn(
                "RTX sensors as camera prims are deprecated as of Isaac Sim 5.0. "
                "Please use an OmniLidar prim with the OmniSensorGenericLidarCoreAPI schema."
            )
            return None

        rotation_rate = float(prim.GetAttribute("omni:sensor:Core:scanRateBaseHz").Get() or 0)
        near_range = float(prim.GetAttribute("omni:sensor:Core:nearRangeM").Get() or 0)
        far_range = float(prim.GetAttribute("omni:sensor:Core:farRangeM").Get() or 0)

        scan_type = str(prim.GetAttribute("omni:sensor:Core:scanType").Get() or "")
        if scan_type == "SOLID_STATE":
            azimuth_deg = prim.GetAttribute("omni:sensor:Core:emitterState:s001:azimuthDeg").Get()
            if not azimuth_deg or len(azimuth_deg) == 0:
                carb.log_error("LaserScan SRTX: Could not read azimuthDeg from lidar prim")
                return None
            az_start = float(min(azimuth_deg))
            az_end = float(max(azimuth_deg))
            h_fov = az_end - az_start
            h_res = h_fov / float(len(azimuth_deg))
            if az_end > 180.0:
                az_start -= 180.0
                az_end -= 180.0
        else:
            firing_rate = float(prim.GetAttribute("omni:sensor:Core:patternFiringRateHz").Get() or 0)
            if rotation_rate <= 0 or firing_rate <= 0:
                carb.log_error("LaserScan SRTX: scanRateBaseHz or patternFiringRateHz is 0")
                return None
            h_res = 360.0 * rotation_rate / firing_rate
            az_start = -180.0
            az_end = 180.0
            h_fov = 360.0

        return dict(
            azimuth_range_start=az_start,
            azimuth_range_end=az_end,
            depth_range_min=near_range,
            depth_range_max=far_range,
            rotation_rate=rotation_rate,
            horizontal_resolution=h_res,
            horizontal_fov=h_fov,
        )

    @staticmethod
    def _setup_srtx(init_params, render_product_path, state, sensor_type, compression_type) -> bool:
        from omni.replicator.srtx import SrtxCore

        stage = omni.usd.get_context().get_stage()
        usd_scene = str(stage.GetRootLayer().identifier) if stage else ""
        srtx_instance = SrtxCore.get_instance(usd_scene)
        if srtx_instance is None:
            carb.log_error(f"No SRTX instance for stage '{usd_scene}'")
            return False

        sensor_set_name = SRTX_SENSOR_SET
        sensor_name = render_product_path.rsplit("/", 1)[-1]
        srtx_instance.add_sensor(sensor_set_name, sensor_name, render_product_path)

        common_params = dict(
            topic_name=init_params["topicName"],
            frame_id=init_params["frameId"],
            node_namespace=init_params["nodeNamespace"],
            queue_size=init_params["queueSize"],
            qos_profile=init_params["qosProfile"],
        )

        if sensor_type == "laser_scan":
            from isaacsim.ros2.nodes.bindings._ros2_nodes import create_laser_scan_publisher_capsule

            prim = stage.GetPrimAtPath(get_camera_prim_path(render_product_path))
            scan_meta = OgnROS2RtxLidarHelper._read_laser_scan_metadata(prim)
            if scan_meta is None:
                carb.log_error("Failed to read laser scan metadata from lidar prim")
                return False
            capsule = create_laser_scan_publisher_capsule(**common_params, **scan_meta)
        else:
            from isaacsim.ros2.nodes.bindings._ros2_nodes import create_lidar_publisher_capsule

            capsule = create_lidar_publisher_capsule(**common_params)

        success, rendervar_path = ensure_render_var_on_product(stage, render_product_path, LIDAR_AOV)
        if not success:
            state.initialized = False
            carb.log_error(f"Failed to create RenderVar at {render_product_path}/{LIDAR_AOV}")
            return False

        handle = srtx_instance.register_frame_callback(sensor_set_name, rendervar_path, capsule)
        if handle == 0:
            carb.log_error(f"Failed to register SRTX frame callback for {rendervar_path}")
            state.initialized = False
            return False

        _start_or_extend_continuous_capture(srtx_instance, sensor_set_name, rendervar_path)

        state._srtx_callback_handle = handle
        state._srtx_capsule = capsule
        state._srtx_sensor_set = sensor_set_name
        state._srtx_output_path = rendervar_path
        return True

    @staticmethod
    def compute(db) -> bool:
        state = db.per_instance_state
        if not db.inputs.enabled:
            if state.initialized:
                # Camera helper was disabled, reset the state
                state.custom_reset()
            return True

        if state.initialized:
            # Lidar helper was already initialized, nothing to do
            return True

        stage = omni.usd.get_context().get_stage()
        render_product_path = db.inputs.renderProductPath
        if not render_product_path:
            carb.log_warn(f"Render product '{render_product_path}' not valid")
            return False
        if stage.GetPrimAtPath(render_product_path) is None:
            # Invalid Render Product Path
            carb.log_warn(f"Render product '{render_product_path}' not created yet, retrying on next call")
            return False
        prim = stage.GetPrimAtPath(get_camera_prim_path(render_product_path))
        if not (prim.IsA(UsdGeom.Camera) and prim.HasAPI(IsaacSensorSchema.IsaacRtxLidarSensorAPI)) and not (
            prim.GetTypeName() == "OmniLidar" and prim.HasAPI("OmniSensorGenericLidarCoreAPI")
        ):
            carb.log_warn(
                f"Render product '{render_product_path}' not attached to RTX Lidar (Camera or OmniLidar prims are required)."
            )
            return False

        state.render_product_path = render_product_path
        sensor_type = db.inputs.type
        state.resetSimulationTimeOnStop = db.inputs.resetSimulationTimeOnStop
        state.publishStepSize = db.inputs.frameSkipCount + 1

        writer = None

        time_type = ""
        if db.inputs.useSystemTime:
            time_type = "SystemTime"
            if db.inputs.resetSimulationTimeOnStop:
                carb.log_warn("System timestamp is being used. Ignoring resetSimulationTimeOnStop input")

        init_params = dict(
            frameId=db.inputs.frameId,
            nodeNamespace=collect_namespace(db.inputs.nodeNamespace, render_product_path),
            queueSize=db.inputs.queueSize,
            topicName=db.inputs.topicName,
            context=db.inputs.context,
            qosProfile=db.inputs.qosProfile,
        )

        use_srtx = carb.settings.get_settings().get_as_bool(USE_SRTX_SETTING)
        if use_srtx:
            if not OgnROS2RtxLidarHelper._setup_srtx(init_params, render_product_path, state, sensor_type, None):
                db.log_error("Failed to setup SRTX for lidar helper")
                return False
            state.initialized = True
            return True

        try:
            with Usd.EditContext(stage, stage.GetSessionLayer()):
                # OG path: create writer, initialize, attach.
                if sensor_type == "laser_scan":
                    if db.inputs.fullScan:
                        carb.log_warn("Full scan does not have an effect with the laser_scan setting")
                    writer = rep.writers.get("RtxLidar" + f"ROS2{time_type}PublishLaserScan")

                elif sensor_type == "point_cloud":
                    writer = build_rtx_sensor_pointcloud_writer(
                        metadata=db.inputs.selectedMetadata,
                        enable_full_scan=db.inputs.fullScan,
                        use_system_time=db.inputs.useSystemTime,
                    )

                    if db.inputs.enableObjectIdMap:
                        if "ObjectId" not in db.inputs.selectedMetadata:
                            carb.log_warn(
                                "enableObjectIdMap is True, but 'ObjectId' is not in the selected metadata. Disabling object ID map output."
                            )
                        elif not get_carb_setting(carb.settings.get_settings(), "/rtx-transient/stableIds/enabled"):
                            carb.log_warn(
                                "enableObjectIdMap is True, but --/rtx-transient/stableIds/enabled is either unset or False. Disabling object ID map output."
                            )
                        else:
                            object_id_map_writer = rep.writers.get(f"ROS2{time_type}PublishObjectIdMap")
                            object_id_map_writer.initialize(
                                nodeNamespace=init_params["nodeNamespace"],
                                queueSize=init_params["queueSize"],
                                topicName=db.inputs.objectIdMapTopicName,
                            )
                            state.append_writer(object_id_map_writer)

                else:
                    carb.log_error(f"Sensor type '{sensor_type}' is not supported")
                    return False
                if writer is not None:
                    writer.initialize(**init_params)
                    state.append_writer(writer)
                    if db.inputs.showDebugView:
                        doTransform = not (
                            prim.GetTypeName() == "OmniLidar"
                            and prim.HasAttribute("omni:sensor:Core:outputFrameOfReference")
                            and prim.GetAttribute("omni:sensor:Core:outputFrameOfReference").Get() == "WORLD"
                        )
                        writer = rep.writers.get(
                            "RtxLidarDebugDrawPointCloud" + ("Buffer" if db.inputs.fullScan else "")
                        )
                        writer.initialize(doTransform=doTransform)
                        state.append_writer(writer)
                state.attach_writers(render_product_path)
        except Exception:
            carb.log_error(f"Failed to initialize lidar helper writer: {traceback.format_exc()}")
            return False

        state.initialized = True
        return True

    @staticmethod
    def release_instance(node, graph_instance_id) -> None:
        try:
            state = OgnROS2RtxLidarHelperInternalState.per_instance_internal_state(node)
        except Exception:
            state = None

        if state is not None:
            cleanup_srtx_state(state)
            state.reset()
