# SPDX-FileCopyrightText: Copyright (c) 2018-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import json
import math
import time
from typing import List
from uuid import uuid4

import isaacsim.sensors.rtx.generic_model_output as gmo_utils
import numpy as np
import omni
import omni.graph.core as og
import omni.kit
import omni.kit.commands
import omni.kit.test
import omni.replicator.core as rep
import rclpy
from isaacsim.ros2.core.impl.ros2_test_case import ROS2TestCase
from isaacsim.sensors.rtx import get_gmo_data
from sensor_msgs.msg import LaserScan, PointCloud2
from std_msgs.msg import String

from .common import create_sarcophagus, get_qos_profile


class TestROS2SensorMsgRTX(ROS2TestCase):

    _ros_msg_type = None
    _helper_type = None

    async def setUp(self):
        await super().setUp()

        self._sensor = None
        self._sensor_prim_path = None
        self._render_product = None
        self._render_product_path = None
        self._annotator_rtx = None
        self._annotator_timestamp = None
        self._mapped_annotator_data = {}

        # Add cubes to the scene
        self._cubes = create_sarcophagus()

        # Configure the ROS2 subscriber to capture the messsge

        self._ros_topic = f"topic_{uuid4().hex}"
        self._ros_msg_data = None
        self._ros_node = self.create_node(f"subscriber_{self._ros_topic}")
        self._ros_msg_count = 0
        self._ros_msg_timestamp_prev = None
        self._is_full_scan = False

        def ros_callback(data):
            self._ros_msg_data = data
            self._ros_msg_count += 1

            # Validate the message timestamp
            if self._ros_msg_timestamp_prev is not None:
                current_timestamp = self._ros_msg_data.header.stamp.sec + self._ros_msg_data.header.stamp.nanosec / 1e9
                expected_diff = 1 / 10 if self._is_full_scan else 1 / 60
                self.assertAlmostEqual(current_timestamp, self._ros_msg_timestamp_prev + expected_diff)
                self._ros_msg_timestamp_prev = current_timestamp

        self._ros_sub = self.create_subscription(
            self._ros_node, self._ros_msg_type, self._ros_topic, ros_callback, get_qos_profile(depth=10)
        )

        # Configure the ROS2 subscriber to capture the Object-ID-to-prim-path map
        self._ros_object_id_map_topic = f"object_id_map_{uuid4().hex}"
        self._ros_object_id_map_data = None
        self._ros_object_id_map_node = self.create_node(f"subscriber_{self._ros_object_id_map_topic}")
        self._ros_object_id_map_count = 0
        self._ros_object_id_map_timestamp_prev = None

        def ros_callback_object_id_map(data):
            self._ros_object_id_map_data = data
            self._ros_object_id_map_count += 1
            prim_paths = json.loads(data.data)["id_to_labels"].values()
            for i in range(15):
                self.assertIn(f"/World/cube_{i}", prim_paths)

        self._ros_sub_object_id_map = self.create_subscription(
            self._ros_object_id_map_node,
            String,
            self._ros_object_id_map_topic,
            ros_callback_object_id_map,
            get_qos_profile(depth=10),
        )

    async def tearDown(self):
        if self._annotator_rtx is not None:
            self._annotator_rtx.detach()
        if self._annotator_timestamp is not None:
            self._annotator_timestamp.detach()
        await super().tearDown()

    async def _create_sensor(self, sensor_type: str, config: str = None, variant: str = None, **kwargs):
        # Create an RTX Sensor
        _, self._sensor = omni.kit.commands.execute(
            f"IsaacSensorCreateRtx{sensor_type.capitalize()}",
            path=f"/{sensor_type}",
            config=config,
            variant=variant,
            **kwargs,
        )
        self.assertEqual(
            self._sensor.GetTypeName(), f"Omni{sensor_type.capitalize()}", f"Failed to create {sensor_type}."
        )
        self._sensor_prim_path = self._sensor.GetPath()
        self._sensor_type = sensor_type
        self.assertFalse(self._sensor.GetAttribute("omni:sensor:Core:skipDroppingInvalidPoints").Get())
        self.assertTrue(self._sensor.GetAttribute("omni:sensor:Core:accumulateOutputs").Get())

        # Create a render product for the sensor
        self._render_product = rep.create.render_product(self._sensor_prim_path, resolution=(128, 128))
        self._render_product_path = self._render_product.path

    async def _create_omnigraph(
        self, enable_full_scan: bool = False, use_system_time: bool = False, metadata: List[str] = []
    ):
        # Create the basic Omnigraph for the sensor
        create_nodes = [
            ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
            ("PCLPublish", f"isaacsim.ros2.bridge.ROS2Rtx{self._sensor_type.capitalize()}Helper"),
        ]
        set_values = [
            ("PCLPublish.inputs:renderProductPath", self._render_product_path),
            ("PCLPublish.inputs:topicName", self._ros_topic),
            ("PCLPublish.inputs:resetSimulationTimeOnStop", True),
            ("PCLPublish.inputs:useSystemTime", use_system_time),
            ("PCLPublish.inputs:enableObjectIdMap", self._sensor_type == "lidar" and "objectId" in metadata),
            ("PCLPublish.inputs:objectIdMapTopicName", self._ros_object_id_map_topic),
        ]
        connections = [
            ("OnPlaybackTick.outputs:tick", "PCLPublish.inputs:execIn"),
        ]

        # Specify metadata based on sensor type
        if self._sensor_type == "lidar":
            # Use OgnROS2RtxLidarPointCloudConfig to specify metadata for Lidar
            create_nodes.append(("PCLLidarConfig", "isaacsim.ros2.bridge.ROS2RtxLidarPointCloudConfig"))
            set_values.append(("PCLPublish.inputs:type", self._helper_type))
            set_values.append(("PCLPublish.inputs:fullScan", enable_full_scan))
            for metadata_item in metadata:
                set_values.append((f"PCLLidarConfig.inputs:output{metadata_item[0].upper()}{metadata_item[1:]}", True))
            connections.append(("PCLLidarConfig.outputs:selectedMetadata", "PCLPublish.inputs:selectedMetadata"))
        elif self._sensor_type == "radar":
            # Enable metadata directly on OgnROS2RtxRadarHelper
            for metadata_item in metadata:
                set_values.append((f"PCLPublish.inputs:output{metadata_item[0].upper()}{metadata_item[1:]}", True))

        try:
            og.Controller.edit(
                {"graph_path": "/ActionGraph", "evaluator_name": "execution"},
                {
                    og.Controller.Keys.CREATE_NODES: create_nodes,
                    og.Controller.Keys.SET_VALUES: set_values,
                    og.Controller.Keys.CONNECT: connections,
                },
            )
        except Exception as e:
            self.fail(f"Failed to create OmniGraph for {self._sensor_type}: {e}")

    def _get_annotator_name(self, full_scan: bool = False, metadata: List[str] = []):
        return "GenericModelOutput"

    def _get_expected_message_count(self, full_scan: bool = False, test_duration_s: float = 1.5):
        if self._sensor_type == "lidar":
            return test_duration_s * 10 * (1 if full_scan else 6) - 1
        elif self._sensor_type == "radar":
            # The first 4 frames are warmup frames, so we don't get messages from them
            return test_duration_s * 60 - 4

    def _get_closest_timestamp(self, message_timestamp):
        closest_key = min(self._mapped_annotator_data.keys(), key=lambda key: abs(key - message_timestamp))
        return self._mapped_annotator_data[closest_key]

    async def _test_message_data(self, full_scan: bool = False, test_duration_s: float = 1.5, metadata: List[str] = []):
        raise NotImplementedError("Subclasses must implement this method.")

    async def _test_sensor(
        self,
        sensor_type: str,
        full_scan: bool = False,
        use_system_time: bool = False,
        metadata: List[str] = [],
        test_duration_s: float = 1.5,
        **kwargs,
    ):

        self._is_full_scan = full_scan
        await self._create_sensor(sensor_type, **kwargs)
        await self._create_omnigraph(enable_full_scan=full_scan, use_system_time=use_system_time, metadata=metadata)

        # Start the timeline and advance by 1 frame to create the post-process graph
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        # Retrieve the annotator and attach it to the render product
        annotator_name = self._get_annotator_name(full_scan=full_scan, metadata=metadata)
        self._annotator_rtx = rep.AnnotatorRegistry.get_annotator(annotator_name)
        self.assertIsNotNone(
            self._annotator_rtx,
            f"Failed to retrieve annotator {annotator_name} for {self._sensor_type}.",
        )
        self._annotator_rtx.attach([self._render_product_path])

        # Retrieve the timestamp annotator and attach it to the render product
        annotator_timestamp_name = "IsaacRead" + ("SystemTime" if use_system_time else "SimulationTime")
        self._annotator_timestamp = rep.AnnotatorRegistry.get_annotator(annotator_timestamp_name)
        self.assertIsNotNone(
            self._annotator_timestamp,
            f"Failed to retrieve {annotator_timestamp_name} annotator for {self._sensor_type}.",
        )
        self._annotator_timestamp.attach([self._render_product_path])

        # Define the callback function for the simulation
        timestamp_output = "systemTime" if use_system_time else "simulationTime"

        # Auxiliary fields available at each GMO aux level (cumulative).
        _AUX_FIELDS = {
            gmo_utils.AuxType.BASIC: [
                ("emitterId", "emitterId"),
                ("channelId", "channelId"),
                ("tickId", "tickId"),
                ("echoId", "echoId"),
                ("tickStates", "tickStates"),
            ],
            gmo_utils.AuxType.EXTRA: [("matId", "matId"), ("objId", "objId")],
            gmo_utils.AuxType.FULL: [("hitNormals", "hitNormals"), ("velocities", "velocities")],
        }

        def _aux_fields_for_level(aux_type):
            """Return the list of (snapshot_key, gmo_attr) pairs available at *aux_type*."""
            fields = []
            for level in (gmo_utils.AuxType.BASIC, gmo_utils.AuxType.EXTRA, gmo_utils.AuxType.FULL):
                if aux_type == gmo_utils.AuxType.NONE:
                    break
                fields += _AUX_FIELDS[level]
                if aux_type == level:
                    break
            return fields

        def spin():
            # Keep ROS communications responsive while the timeline is running.
            rclpy.spin_once(self._ros_node, timeout_sec=0.01)
            rclpy.spin_once(self._ros_object_id_map_node, timeout_sec=0.01)

            # Get the latest GMO annotator data and map it to the message timestamp.
            # Copy all arrays eagerly since the GMO struct holds pointers into the
            # raw buffer which may be overwritten on the next frame.
            raw_data = self._annotator_rtx.get_data(do_array_copy=True)
            timestamp_data = self._annotator_timestamp.get_data()
            timestamp = timestamp_data.get(timestamp_output) if timestamp_data is not None else None
            if timestamp is not None and raw_data is not None and raw_data.size > 0:
                gmo = get_gmo_data(raw_data)
                if gmo.magicNumber == gmo_utils.getMagicNumberGMO() and gmo.numElements > 0:
                    snapshot = {
                        "x": gmo.x.copy(),
                        "y": gmo.y.copy(),
                        "z": gmo.z.copy(),
                        "scalar": gmo.scalar.copy(),
                        "numElements": gmo.numElements,
                        "elementsCoordsType": gmo.elementsCoordsType,
                        "timestampNs": gmo.timestampNs,
                        "timeOffsetNs": gmo.timeOffsetNs.copy(),
                    }
                    # Copy auxiliary fields based on the GMO aux level.
                    # Accessing fields beyond the reported auxType causes a
                    # segfault in the C++ GMO extension (null auxiliaryData pointer).
                    for field, attr in _aux_fields_for_level(gmo.auxType):
                        arr = getattr(gmo, attr)
                        if arr is not None and hasattr(arr, "copy"):
                            snapshot[field] = arr.copy()
                    self._mapped_annotator_data[timestamp] = snapshot

        system_time_start = time.time() if use_system_time else None

        def message_ready():
            if self._ros_msg_data is None:
                return False

            stamp = self._ros_msg_data.header.stamp.sec + self._ros_msg_data.header.stamp.nanosec / 1e9
            if stamp < 0.2:
                return False
            if system_time_start is not None and stamp < system_time_start:
                return False

            # For LaserScan we must also wait past warm-up frames where some fields may be unset (e.g. inf).
            # Otherwise assertions in TestROS2LaserScanRTX can run on an invalid scan.
            if isinstance(self._ros_msg_data, LaserScan):
                if not math.isfinite(self._ros_msg_data.scan_time) or self._ros_msg_data.scan_time <= 0.0:
                    return False
                if not math.isfinite(self._ros_msg_data.time_increment) or self._ros_msg_data.time_increment <= 0.0:
                    return False
                if self._ros_msg_data.ranges is None or len(self._ros_msg_data.ranges) == 0:
                    return False
                # At least one range sample should be finite.
                if not any(math.isfinite(r) for r in self._ros_msg_data.ranges):
                    return False

            # Ensure annotator data is available for lookup in _get_closest_timestamp().
            if not self._mapped_annotator_data:
                return False

            # If object-id map publishing is enabled, wait until we receive it too.
            if self._sensor_type == "lidar" and "objectId" in metadata and self._ros_object_id_map_data is None:
                return False

            return True

        condition_met = await self.simulate_until_condition(
            message_ready,
            max_frames=600,
            per_frame_callback=spin,
        )
        self.assertTrue(
            condition_met,
            f"No valid message received for {self._sensor_type} after {test_duration_s} simulated seconds.",
        )

        # self.assertEqual(
        #     self._ros_msg_count,
        #     expected_message_count,
        #     f"Expected {expected_message_count} messages, but received {self._ros_msg_count}.",
        # )

        # Get the annotator data for the latest received message

        await self._test_message_data(full_scan=full_scan, test_duration_s=test_duration_s, metadata=metadata)


class TestROS2PointCloudRTX(TestROS2SensorMsgRTX):
    _ros_msg_type = PointCloud2
    _helper_type = "point_cloud"

    @staticmethod
    def _snapshot_to_cartesian(snapshot):
        """Convert a GMO snapshot dict to Cartesian xyz, handling both coordinate types."""
        x_data = snapshot["x"]
        y_data = snapshot["y"]
        z_data = snapshot["z"]
        if snapshot["elementsCoordsType"] == gmo_utils.CoordsType.CARTESIAN:
            return np.stack([x_data, y_data, z_data], axis=1)
        # Spherical to Cartesian
        az = np.radians(x_data)
        el = np.radians(y_data)
        r = z_data
        rxy = r * np.cos(el)
        cart_x = rxy * np.cos(az)
        cart_y = rxy * np.sin(az)
        cart_z = r * np.sin(el)
        mask = r < 1e-6
        cart_x[mask] = 0.0
        cart_y[mask] = 0.0
        cart_z[mask] = 0.0
        return np.stack([cart_x, cart_y, cart_z], axis=1)

    async def _test_message_data(self, full_scan: bool = False, test_duration_s: float = 1.5, metadata: List[str] = []):
        self.assertIsNotNone(self._ros_msg_data)
        message_timestamp = self._ros_msg_data.header.stamp.sec + self._ros_msg_data.header.stamp.nanosec / 1e9
        snap = self._get_closest_timestamp(message_timestamp)

        self.assertGreater(
            self._ros_msg_count,
            0,
            f"No message received for {self._sensor_type} after {test_duration_s} simulated seconds.",
        )

        from sensor_msgs_py.point_cloud2 import read_points

        msg_points = read_points(self._ros_msg_data)

        def test_match(
            message_data: List[np.ndarray],
            annotator_data: np.ndarray,
            field_name: str = None,
        ):
            message_data = np.concatenate([m[..., None] for m in message_data], axis=1)
            if len(annotator_data.shape) == 1:
                annotator_data = annotator_data[..., None]
            self.assertGreater(message_data.shape[0], 0, f"Empty message data for {field_name}")
            self.assertGreater(annotator_data.shape[0], 0, f"Empty annotator data for {field_name}")
            self.assertEqual(message_data.shape, annotator_data.shape, f"Shape mismatch for {field_name}")
            self.assertEqual(message_data.size, annotator_data.size, f"Size mismatch for {field_name}")
            self.assertTrue(
                np.allclose(message_data, annotator_data, atol=1e-6),
                f"Data mismatch for {field_name}: {message_data} != {annotator_data}",
            )

        # Test point cloud position data
        cartesian = self._snapshot_to_cartesian(snap)
        test_match([msg_points["x"], msg_points["y"], msg_points["z"]], cartesian, "position")

        if "intensity" in metadata:
            test_match([msg_points["intensity"]], snap["scalar"], "intensity")
        if "timestamp" in metadata:
            msg_timestamp = (
                np.left_shift(msg_points["timestamp_1"].astype(np.uint64), 32)[..., None]
                + msg_points["timestamp_0"].astype(np.uint64)[..., None]
            ).squeeze(axis=1)
            expected_ts = snap["timeOffsetNs"].astype(np.uint64) + snap["timestampNs"]
            test_match([msg_timestamp], expected_ts, "timestamp")
        if "emitterId" in metadata:
            test_match([msg_points["emitter_id"]], snap["emitterId"], "emitterId")
        if "channelId" in metadata:
            test_match([msg_points["channel_id"]], snap["channelId"], "channelId")
        if "materialId" in metadata:
            test_match([msg_points["material_id"]], snap["matId"], "materialId")
        if "tickId" in metadata:
            test_match([msg_points["tick_id"]], snap["tickId"], "tickId")
        if "hitNormal" in metadata:
            test_match(
                [msg_points["nx"], msg_points["ny"], msg_points["nz"]],
                snap["hitNormals"].reshape(-1, 3),
                "hitNormal",
            )
        if "velocity" in metadata:
            test_match(
                [msg_points["vx"], msg_points["vy"], msg_points["vz"]],
                snap["velocities"].reshape(-1, 3),
                "velocity",
            )
        if "objectId" in metadata:
            msg_objectId = np.stack(
                [
                    msg_points["object_id_0"],
                    msg_points["object_id_1"],
                    msg_points["object_id_2"],
                    msg_points["object_id_3"],
                ],
                axis=1,
            ).flatten()
            annotator_objectId = snap["objId"].view(np.uint32)
            test_match([msg_objectId], annotator_objectId, "objectId")
        if "echoId" in metadata:
            test_match([msg_points["echo_id"]], snap["echoId"], "echoId")
        if "tickState" in metadata:
            test_match([msg_points["tick_state"]], snap["tickStates"], "tickState")
        if "radialVelocityMS" in metadata:
            self.fail("Radial velocity MS is not supported for Lidar")

    async def test_rtx_lidar_full_scan_simulation_time_no_metadata(self):
        await self._test_sensor(
            sensor_type="lidar", full_scan=True, use_system_time=False, metadata=[], test_duration_s=0.5
        )

    async def test_rtx_lidar_full_scan_simulation_time_partial_metadata(self):
        kwargs = {"omni:sensor:Core:auxOutputType": "BASIC"}
        await self._test_sensor(
            sensor_type="lidar",
            full_scan=True,
            use_system_time=False,
            metadata=["echoId"],
            test_duration_s=0.5,
            **kwargs,
        )

    async def test_rtx_lidar_full_scan_simulation_time_full_metadata(self):
        kwargs = {"omni:sensor:Core:auxOutputType": "FULL"}
        await self._test_sensor(
            sensor_type="lidar",
            full_scan=True,
            use_system_time=False,
            metadata=[
                "intensity",
                "timestamp",
                "emitterId",
                "channelId",
                "materialId",
                "tickId",
                "hitNormal",
                "velocity",
                "objectId",
                "echoId",
                "tickState",
            ],
            test_duration_s=0.5,
            **kwargs,
        )

    async def test_rtx_lidar_full_scan_system_time_full_metadata(self):
        kwargs = {"omni:sensor:Core:auxOutputType": "FULL"}
        await self._test_sensor(
            sensor_type="lidar",
            full_scan=True,
            use_system_time=True,
            metadata=[
                "intensity",
                "timestamp",
                "emitterId",
                "channelId",
                "materialId",
                "tickId",
                "hitNormal",
                "velocity",
                "objectId",
                "echoId",
                "tickState",
            ],
            test_duration_s=0.5,
            **kwargs,
        )


class TestROS2LaserScanRTX(TestROS2SensorMsgRTX):
    _ros_msg_type = LaserScan
    _helper_type = "laser_scan"

    async def _test_message_data(self, full_scan: bool = False, test_duration_s: float = 1.5, metadata: List[str] = []):
        if self._sensor_type == "radar":
            self.assertIsNone(self._ros_msg_data)
            return

        self.assertIsNotNone(self._ros_msg_data)
        message_timestamp = self._ros_msg_data.header.stamp.sec + self._ros_msg_data.header.stamp.nanosec / 1e9
        snap = self._get_closest_timestamp(message_timestamp)

        self.assertGreater(
            self._ros_msg_count,
            0,
            f"No message received for {self._sensor_type} after {test_duration_s} simulated seconds.",
        )

        # Compute azimuth and distance from snapshot, handling both coordinate types
        if snap["elementsCoordsType"] == gmo_utils.CoordsType.CARTESIAN:
            x_data = snap["x"]
            y_data = snap["y"]
            z_data = snap["z"]
            azimuth_data = np.degrees(np.arctan2(y_data, x_data))
            distance_data = np.sqrt(x_data**2 + y_data**2 + z_data**2)
        else:
            azimuth_data = snap["x"]
            distance_data = snap["z"]
        intensity_data = (snap["scalar"] * 255.0).astype(np.uint8)

        # Reconstruct the flat scan from GMO data using the ROS message parameters
        h_res = np.degrees(self._ros_msg_data.angle_increment)
        az_start = np.degrees(self._ros_msg_data.angle_min)
        num_output = len(self._ros_msg_data.ranges)

        expected_ranges = np.full(num_output, -1.0, dtype=np.float32)
        expected_intensities = np.zeros(num_output, dtype=np.float32)
        for i in range(snap["numElements"]):
            out_idx = int((azimuth_data[i] - az_start) / h_res)
            if out_idx >= num_output:
                out_idx = num_output - 1
            expected_ranges[out_idx] = distance_data[i]
            expected_intensities[out_idx] = float(intensity_data[i])

        ros_ranges = np.array(self._ros_msg_data.ranges, dtype=np.float32)
        ros_intensities = np.array(self._ros_msg_data.intensities, dtype=np.float32)
        self.assertTrue(
            np.allclose(expected_ranges, ros_ranges, atol=1e-5),
            "Range data mismatch between GMO-derived flat scan and ROS LaserScan message.",
        )
        self.assertTrue(
            np.allclose(expected_intensities, ros_intensities, atol=1e-5),
            "Intensity data mismatch between GMO-derived flat scan and ROS LaserScan message.",
        )

    async def test_rtx_lidar_full_scan_simulation_time(self):
        await self._test_sensor(
            sensor_type="lidar", use_system_time=False, test_duration_s=0.5, config="SICK_nanoScan3"
        )

    async def test_rtx_lidar_full_scan_system_time(self):
        await self._test_sensor(sensor_type="lidar", use_system_time=True, test_duration_s=0.5, config="SICK_nanoScan3")
