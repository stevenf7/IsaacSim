# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import asyncio
import os

import carb
import omni.ext
import omni.replicator.core as rep
import omni.syntheticdata
import omni.syntheticdata._syntheticdata as sd

from .. import _ros_bridge

BRIDGE_NAME = "omni.isaac.ros_bridge"
BRIDGE_PREFIX = "ROS1"


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._rosbridge = None
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        for b in ["omni.isaac.ros_bridge", "omni.isaac.ros2_bridge"]:
            if b != BRIDGE_NAME and ext_manager.is_extension_enabled(b):
                carb.log_error(f"{BRIDGE_PREFIX} bridge extension cannot be enabled if {b} is enabled")
                ext_manager.set_extension_enabled(BRIDGE_NAME, False)
                return

        if "ROS_MASTER_URI" in os.environ:
            master_uri = os.environ["ROS_MASTER_URI"]
            carb.log_info(f"Found ROS_MASTER_URI={master_uri}")
        else:
            os.environ["ROS_MASTER_URI"] = "http://localhost:11311"
            carb.log_warn("ROS_MASTER_URI not set, using default, ROS_MASTER_URI=http://localhost:11311")

        self._rosbridge = _ros_bridge.acquire_ros_bridge_interface()

        self.register_nodes()

    def on_shutdown(self):
        async def safe_shutdown(bridge):
            omni.timeline.get_timeline_interface().stop()
            await omni.kit.app.get_app().next_update_async()
            if bridge is not None:
                _ros_bridge.release_ros_bridge_interface(bridge)

        asyncio.ensure_future(safe_shutdown(self._rosbridge))
        self.unregister_nodes()

    def register_nodes(self):

        # For Simulation and System time. Removed first S char in keys to account for both upper and lower cases.
        TIME_TYPES = [("imulationTime", ""), ("ystemTime", "SystemTime")]

        for time_type in TIME_TYPES:
            ##### Publish RGB
            rv = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(sd.SensorType.Rgb.name)

            writer_name = f"{rv}{BRIDGE_PREFIX}{time_type[1]}PublishImage"
            rep.writers.register_node_writer(
                name=writer_name,
                node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishImage",
                annotators=[
                    f"{rv}IsaacConvertRGBAToRGB",
                    omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                        f"IsaacReadS{time_type[0]}", attributes_mapping={f"outputs:s{time_type[0]}": "inputs:timeStamp"}
                    ),
                ],
                category=BRIDGE_NAME,
            )
            # Register writer for Replicator telemetry tracking
            rep.WriterRegistry._default_writers.append(
                writer_name
            ) if writer_name not in rep.WriterRegistry._default_writers else None

            ##### Publish Depth
            rv = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(
                sd.SensorType.DistanceToImagePlane.name
            )
            writer_name = f"{rv}{BRIDGE_PREFIX}{time_type[1]}PublishImage"
            rep.writers.register_node_writer(
                name=writer_name,
                node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishImage",
                annotators=[
                    omni.syntheticdata.SyntheticData.NodeConnectionTemplate(rv + "ExportRawArray"),
                    omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                        f"IsaacReadS{time_type[0]}", attributes_mapping={f"outputs:s{time_type[0]}": "inputs:timeStamp"}
                    ),
                    f"{rv}IsaacSimulationGate",
                ],
                encoding="32FC1",
                category=BRIDGE_NAME,
            )
            # Register writer for Replicator telemetry tracking
            rep.WriterRegistry._default_writers.append(
                writer_name
            ) if writer_name not in rep.WriterRegistry._default_writers else None

            # publish depth pcl
            writer_name = f"{rv}{BRIDGE_PREFIX}{time_type[1]}PublishPointCloud"
            rep.writers.register_node_writer(
                name=writer_name,
                node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishPointCloud",
                annotators=[
                    f"{rv}IsaacConvertDepthToPointCloud",
                    omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                        f"IsaacReadS{time_type[0]}", attributes_mapping={f"outputs:s{time_type[0]}": "inputs:timeStamp"}
                    ),
                ],
                category=BRIDGE_NAME,
            )
            # Register writer for Replicator telemetry tracking
            rep.WriterRegistry._default_writers.append(
                writer_name
            ) if writer_name not in rep.WriterRegistry._default_writers else None

            # instance
            writer_name = f"{BRIDGE_PREFIX}{time_type[1]}PublishInstanceSegmentation"
            rep.writers.register_node_writer(
                name=writer_name,
                node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishImage",
                annotators=[
                    "instance_segmentation_fast",
                    f'{omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar("InstanceSegmentation")}IsaacSimulationGate',
                    omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                        f"IsaacReadS{time_type[0]}", attributes_mapping={f"outputs:s{time_type[0]}": "inputs:timeStamp"}
                    ),
                ],
                encoding="32SC1",
                category=BRIDGE_NAME,
            )
            # Register writer for Replicator telemetry tracking
            rep.WriterRegistry._default_writers.append(
                writer_name
            ) if writer_name not in rep.WriterRegistry._default_writers else None

            # Semantic
            writer_name = f"{BRIDGE_PREFIX}{time_type[1]}PublishSemanticSegmentation"
            rep.writers.register_node_writer(
                name=writer_name,
                node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishImage",
                annotators=[
                    "semantic_segmentation",
                    f'{omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar("SemanticSegmentation")}IsaacSimulationGate',
                    omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                        f"IsaacReadS{time_type[0]}", attributes_mapping={f"outputs:s{time_type[0]}": "inputs:timeStamp"}
                    ),
                ],
                encoding="32SC1",
                category=BRIDGE_NAME,
            )
            # Register writer for Replicator telemetry tracking
            rep.WriterRegistry._default_writers.append(
                writer_name
            ) if writer_name not in rep.WriterRegistry._default_writers else None

            # Bbox2d tight
            writer_name = f"{BRIDGE_PREFIX}{time_type[1]}PublishBoundingBox2DTight"
            rep.writers.register_node_writer(
                name=writer_name,
                node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishBbox2D",
                annotators=[
                    omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                        "bounding_box_2d_tight_fast", attributes_mapping={"input:semanticTypes": ["class"]}
                    ),
                    f'{omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar("BoundingBox2DTight")}IsaacSimulationGate',
                    omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                        f"IsaacReadS{time_type[0]}", attributes_mapping={f"outputs:s{time_type[0]}": "inputs:timeStamp"}
                    ),
                ],
                category=BRIDGE_NAME,
            )
            # Register writer for Replicator telemetry tracking
            rep.WriterRegistry._default_writers.append(
                writer_name
            ) if writer_name not in rep.WriterRegistry._default_writers else None

            # bbox2d Loose
            writer_name = f"{BRIDGE_PREFIX}{time_type[1]}PublishBoundingBox2DLoose"
            rep.writers.register_node_writer(
                name=writer_name,
                node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishBbox2D",
                annotators=[
                    omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                        "bounding_box_2d_loose_fast",
                        attributes_mapping={"input:semanticTypes": ["class"], "outputs:data": "inputs:data"},
                    ),
                    f'{omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar("BoundingBox2DLoose")}IsaacSimulationGate',
                    omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                        f"IsaacReadS{time_type[0]}", attributes_mapping={f"outputs:s{time_type[0]}": "inputs:timeStamp"}
                    ),
                ],
                category=BRIDGE_NAME,
            )
            # Register writer for Replicator telemetry tracking
            rep.WriterRegistry._default_writers.append(
                writer_name
            ) if writer_name not in rep.WriterRegistry._default_writers else None

            # bbox3d Loose
            writer_name = f"{BRIDGE_PREFIX}{time_type[1]}PublishBoundingBox3D"
            rep.writers.register_node_writer(
                name=writer_name,
                node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishBbox3D",
                annotators=[
                    omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                        "bounding_box_3d_fast",
                        attributes_mapping={"input:semanticTypes": ["class"], "outputs:data": "inputs:data"},
                    ),
                    f'{omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar("BoundingBox3D")}IsaacSimulationGate',
                    omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                        f"IsaacReadS{time_type[0]}", attributes_mapping={f"outputs:s{time_type[0]}": "inputs:timeStamp"}
                    ),
                ],
                category=BRIDGE_NAME,
            )
            # Register writer for Replicator telemetry tracking
            rep.WriterRegistry._default_writers.append(
                writer_name
            ) if writer_name not in rep.WriterRegistry._default_writers else None

            # camera info
            writer_name = f"{BRIDGE_PREFIX}{time_type[1]}PublishCameraInfo"
            rep.writers.register_node_writer(
                name=writer_name,
                node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishCameraInfo",
                annotators=[
                    "IsaacReadCameraInfo",
                    "PostProcessDispatchIsaacSimulationGate",
                    omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                        f"IsaacReadS{time_type[0]}", attributes_mapping={f"outputs:s{time_type[0]}": "inputs:timeStamp"}
                    ),
                ],
                category=BRIDGE_NAME,
            )
            # Register writer for Replicator telemetry tracking
            rep.WriterRegistry._default_writers.append(
                writer_name
            ) if writer_name not in rep.WriterRegistry._default_writers else None

            # outputs that we can publish labels for
            label_names = {
                "instance_segmentation_fast": omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(
                    "InstanceSegmentation"
                ),
                "semantic_segmentation": omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(
                    "SemanticSegmentation"
                ),
                "bounding_box_2d_tight_fast": omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(
                    "BoundingBox2DTight"
                ),
                "bounding_box_2d_loose_fast": omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(
                    "BoundingBox2DLoose"
                ),
                "bounding_box_3d_fast": omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(
                    "BoundingBox3D"
                ),
            }
            for annotator, annotator_name in label_names.items():
                node_writer_name = f"{annotator_name}{BRIDGE_PREFIX}{time_type[1]}PublishSemanticLabels"
                rep.writers.register_node_writer(
                    name=node_writer_name,
                    node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishSemanticLabels",
                    annotators=[
                        annotator,
                        f"{annotator_name}IsaacSimulationGate",
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            f"IsaacReadS{time_type[0]}",
                            attributes_mapping={f"outputs:s{time_type[0]}": "inputs:timeStamp"},
                        ),
                    ],
                    category=BRIDGE_NAME,
                )
                # Register writer for Replicator telemetry tracking
                rep.WriterRegistry._default_writers.append(
                    node_writer_name
                ) if node_writer_name not in rep.WriterRegistry._default_writers else None

            # RTX lidar PCL publisher
            writer_name = f"RtxLidar{BRIDGE_PREFIX}{time_type[1]}PublishPointCloud"
            rep.writers.register_node_writer(
                name=writer_name,
                node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishPointCloud",
                annotators=[
                    "RtxSensorCpu" + "IsaacComputeRTXLidarPointCloud",
                    "PostProcessDispatchIsaacSimulationGate",
                    omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                        f"IsaacReadS{time_type[0]}", attributes_mapping={f"outputs:s{time_type[0]}": "inputs:timeStamp"}
                    ),
                ],
                category=BRIDGE_NAME,
            )
            # Register writer for Replicator telemetry tracking
            rep.WriterRegistry._default_writers.append(
                writer_name
            ) if writer_name not in rep.WriterRegistry._default_writers else None

            writer_name = f"RtxLidar{BRIDGE_PREFIX}{time_type[1]}PublishPointCloudBuffer"
            rep.writers.register_node_writer(
                name=writer_name,
                node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishPointCloud",
                annotators=[
                    "RtxSensorCpu" + "IsaacCreateRTXLidarScanBuffer",
                    "PostProcessDispatchIsaacSimulationGate",
                    omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                        f"IsaacReadS{time_type[0]}", attributes_mapping={f"outputs:s{time_type[0]}": "inputs:timeStamp"}
                    ),
                ],
                category=BRIDGE_NAME,
            )
            # Register writer for Replicator telemetry tracking
            rep.WriterRegistry._default_writers.append(
                writer_name
            ) if writer_name not in rep.WriterRegistry._default_writers else None

            # RTX Radar PCL publisher
            writer_name = f"RtxRadar{BRIDGE_PREFIX}{time_type[1]}PublishPointCloud"
            rep.writers.register_node_writer(
                name=writer_name,
                node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishPointCloud",
                annotators=[
                    "RtxSensorCpu" + "IsaacComputeRTXRadarPointCloud",
                    "PostProcessDispatchIsaacSimulationGate",
                    omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                        f"IsaacReadS{time_type[0]}", attributes_mapping={f"outputs:s{time_type[0]}": "inputs:timeStamp"}
                    ),
                ],
                category=BRIDGE_NAME,
            )
            # Register writer for Replicator telemetry tracking
            rep.WriterRegistry._default_writers.append(
                writer_name
            ) if writer_name not in rep.WriterRegistry._default_writers else None

            # RTX lidar LaserScan publisher
            writer_name = f"RtxLidar{BRIDGE_PREFIX}{time_type[1]}PublishLaserScan"
            rep.writers.register_node_writer(
                name=writer_name,
                node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishLaserScan",
                annotators=[
                    "RtxSensorCpu" + "IsaacComputeRTXLidarFlatScan",
                    "PostProcessDispatchIsaacSimulationGate",
                    omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                        f"IsaacReadS{time_type[0]}", attributes_mapping={f"outputs:s{time_type[0]}": "inputs:timeStamp"}
                    ),
                ],
                category=BRIDGE_NAME,
            )
            # Register writer for Replicator telemetry tracking
            rep.WriterRegistry._default_writers.append(
                writer_name
            ) if writer_name not in rep.WriterRegistry._default_writers else None

    def unregister_nodes(self):
        for writer in rep.WriterRegistry.get_writers(category=BRIDGE_NAME):
            rep.writers.unregister_writer(writer)
