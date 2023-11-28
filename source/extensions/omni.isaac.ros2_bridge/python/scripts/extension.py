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
import sys

import carb
import omni
import omni.ext
import omni.replicator.core as rep
import omni.syntheticdata
import omni.syntheticdata._syntheticdata as sd

BRIDGE_NAME = "omni.isaac.ros2_bridge"
BRIDGE_PREFIX = "ROS2"


class ROS2BridgeExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        self._ros2bridge = None
        self.registered_template = []
        self._module = None

        # WAR for incorrect extension trying to be started
        ext_manager = omni.kit.app.get_app().get_extension_manager()

        self._extension_path = ext_manager.get_extension_path(ext_id)
        for b in ["omni.isaac.ros_bridge", "omni.isaac.ros2_bridge"]:
            if b != BRIDGE_NAME and ext_manager.is_extension_enabled(b):
                carb.log_error(f"{BRIDGE_PREFIX} bridge extension cannot be enabled if {b} is enabled")
                ext_manager.set_extension_enabled(BRIDGE_NAME, False)

                return

        backup_ros_distro = carb.settings.get_settings().get_as_string("/exts/omni.isaac.ros2_bridge/ros_distro")
        ros_distro = os.environ.get("ROS_DISTRO")
        if ros_distro is None:
            carb.log_warn(
                "ROS_DISTRO env var not found, Please source ROS2 Foxy, or Humble, before enabling this extension"
            )
            omni.kit.app.get_app().print_and_log(f"Using backup internal ROS2 {backup_ros_distro} distro")
            ros_distro = backup_ros_distro
            os.environ["ROS_DISTRO"] = ros_distro
            # os.environ["RMW_IMPLEMENTATION"] = "rmw_fastrtps_cpp"

        if ros_distro not in ["humble", "foxy"]:
            carb.log_error(f"ROS_DISTRO of {ros_distro} is currently not supported")
            ext_manager.set_extension_enabled("omni.isaac.ros2_bridge", False)
            return

        if sys.platform == "win32":
            if os.environ.get("PATH"):
                os.environ["PATH"] = os.environ.get("PATH") + ";" + self._extension_path + "/bin"
                # WAR: sys.path on windows is missing PYTHONPATH variables, causing rclpy to not be found
                if os.environ.get("PYTHONPATH") is not None:
                    sys.path.extend(os.environ.get("PYTHONPATH").split(";"))
            else:
                os.environ["PATH"] = self._extension_path + "/bin"

        carb.get_framework().load_plugins(
            loaded_file_wildcards=["omni.isaac.ros2_bridge.plugin"],
            search_paths=[os.path.abspath(os.path.join(self._extension_path, "bin"))],
        )
        from omni.isaac.ros2_bridge import _ros2_bridge

        self._module = _ros2_bridge
        self._ros2bridge = self._module.acquire_ros2_bridge_interface()
        if self._ros2bridge.get_startup_status() is False:
            if sys.platform == "linux":
                omni.kit.app.get_app().print_and_log(
                    f"To use the internal libraries included with the extension please set: \nRMW_IMPLEMENTATION=rmw_fastrtps_cpp\nLD_LIBRARY_PATH=$LD_LIBRARY_PATH:{self._extension_path}/{ros_distro}/lib\nBefore starting Isaac Sim"
                )
            else:
                omni.kit.app.get_app().print_and_log(
                    f"To use the internal libraries included with the extension please set: \nRMW_IMPLEMENTATION=rmw_fastrtps_cpp\nPATH=%PATH%;{self._extension_path}/{ros_distro}/lib\nBefore starting Isaac Sim"
                )
            carb.log_error(f"ROS2 Bridge startup failed")
            ext_manager.set_extension_enabled("omni.isaac.ros2_bridge", False)
        self.register_nodes()

    def on_shutdown(self):
        async def safe_shutdown(module, bridge):
            omni.timeline.get_timeline_interface().stop()
            await omni.kit.app.get_app().next_update_async()
            if bridge is not None:
                module.release_ros2_bridge_interface(bridge)

        asyncio.ensure_future(safe_shutdown(self._module, self._ros2bridge))
        self.unregister_nodes()

    def register_nodes(self):
        ##### Publish RGB
        rv = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(sd.SensorType.Rgb.name)

        rep.writers.register_node_writer(
            name=f"{rv}{BRIDGE_PREFIX}PublishImage",
            node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishImage",
            annotators=[
                f"{rv}IsaacConvertRGBAToRGB",
                omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                    "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                ),
                f"{rv}IsaacSimulationGate",
            ],
            category=BRIDGE_NAME,
        )
        ##### Publish Depth
        rv = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(sd.SensorType.DistanceToImagePlane.name)
        rep.writers.register_node_writer(
            name=f"{rv}{BRIDGE_PREFIX}PublishImage",
            node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishImage",
            annotators=[
                omni.syntheticdata.SyntheticData.NodeConnectionTemplate(rv + "ExportRawArray"),
                omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                    "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                ),
                f"{rv}IsaacSimulationGate",
            ],
            encoding="32FC1",
            category=BRIDGE_NAME,
        )

        # publish depth pcl
        rep.writers.register_node_writer(
            name=f"{rv}{BRIDGE_PREFIX}PublishPointCloud",
            node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishPointCloud",
            annotators=[
                f"{rv}IsaacConvertDepthToPointCloud",
                omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                    "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                ),
            ],
            category=BRIDGE_NAME,
        )
        # instance
        rep.writers.register_node_writer(
            name=f"{BRIDGE_PREFIX}PublishInstanceSegmentation",
            node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishImage",
            annotators=[
                "instance_segmentation",
                f'{omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar("InstanceSegmentation")}IsaacSimulationGate',
                omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                    "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                ),
            ],
            encoding="32SC1",
            category=BRIDGE_NAME,
        )
        # Semantic
        rep.writers.register_node_writer(
            name=f"{BRIDGE_PREFIX}PublishSemanticSegmentation",
            node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishImage",
            annotators=[
                "semantic_segmentation",
                f'{omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar("SemanticSegmentation")}IsaacSimulationGate',
                omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                    "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                ),
            ],
            encoding="32SC1",
            category=BRIDGE_NAME,
        )
        # Bbox2d tight
        rep.writers.register_node_writer(
            name=f"{BRIDGE_PREFIX}PublishBoundingBox2DTight",
            node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishBbox2D",
            annotators=[
                omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                    "bounding_box_2d_tight", attributes_mapping={"input:semanticTypes": ["class"]}
                ),
                f'{omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar("BoundingBox2DTight")}IsaacSimulationGate',
                omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                    "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                ),
            ],
            category=BRIDGE_NAME,
        )

        # bbox2d Loose
        rep.writers.register_node_writer(
            name=f"{BRIDGE_PREFIX}PublishBoundingBox2DLoose",
            node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishBbox2D",
            annotators=[
                omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                    "bounding_box_2d_loose",
                    attributes_mapping={"input:semanticTypes": ["class"], "outputs:data": "inputs:data"},
                ),
                f'{omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar("BoundingBox2DLoose")}IsaacSimulationGate',
                omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                    "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                ),
            ],
            category=BRIDGE_NAME,
        )
        # bbox3d Loose
        rep.writers.register_node_writer(
            name=f"{BRIDGE_PREFIX}PublishBoundingBox3D",
            node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishBbox3D",
            annotators=[
                omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                    "bounding_box_3d",
                    attributes_mapping={"input:semanticTypes": ["class"], "outputs:data": "inputs:data"},
                ),
                f'{omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar("BoundingBox3D")}IsaacSimulationGate',
                omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                    "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                ),
            ],
            category=BRIDGE_NAME,
        )
        # camera info
        rep.writers.register_node_writer(
            name=f"{BRIDGE_PREFIX}PublishCameraInfo",
            node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishCameraInfo",
            annotators=[
                "IsaacReadCameraInfo",
                "PostProcessDispatchIsaacSimulationGate",
                omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                    "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                ),
            ],
            category=BRIDGE_NAME,
        )
        # outputs that we can publish labels for
        label_names = {
            "instance_segmentation": omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(
                "InstanceSegmentation"
            ),
            "semantic_segmentation": omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(
                "SemanticSegmentation"
            ),
            "bounding_box_2d_tight": omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(
                "BoundingBox2DTight"
            ),
            "bounding_box_2d_loose": omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(
                "BoundingBox2DLoose"
            ),
            "bounding_box_3d": omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar("BoundingBox3D"),
        }
        for annotator, annotator_name in label_names.items():
            rep.writers.register_node_writer(
                name=f"{annotator_name}{BRIDGE_PREFIX}PublishSemanticLabels",
                node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishSemanticLabels",
                annotators=[
                    annotator,
                    f"{annotator_name}IsaacSimulationGate",
                    omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                        "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                    ),
                ],
                category=BRIDGE_NAME,
            )

        # RTX lidar PCL publisher
        rep.writers.register_node_writer(
            name=f"RtxLidar{BRIDGE_PREFIX}PublishPointCloud",
            node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishPointCloud",
            annotators=[
                "RtxSensorCpu" + "IsaacComputeRTXLidarPointCloud",
                "PostProcessDispatchIsaacSimulationGate",
                omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                    "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                ),
            ],
            category=BRIDGE_NAME,
        )
        rep.writers.register_node_writer(
            name=f"RtxLidar{BRIDGE_PREFIX}PublishPointCloudBuffer",
            node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishPointCloud",
            annotators=[
                "RtxSensorCpu" + "IsaacCreateRTXLidarScanBuffer",
                "PostProcessDispatchIsaacSimulationGate",
                omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                    "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                ),
            ],
            category=BRIDGE_NAME,
        )

        # RTX Radar PCL publisher
        rep.writers.register_node_writer(
            name=f"RtxRadar{BRIDGE_PREFIX}PublishPointCloud",
            node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishPointCloud",
            annotators=[
                "RtxSensorCpu" + "IsaacComputeRTXRadarPointCloud",
                "PostProcessDispatchIsaacSimulationGate",
                omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                    "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                ),
            ],
            category=BRIDGE_NAME,
        )

        # RTX lidar LaserScan publisher
        rep.writers.register_node_writer(
            name=f"RtxLidar{BRIDGE_PREFIX}PublishLaserScan",
            node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishLaserScan",
            annotators=[
                "RtxSensorCpu" + "IsaacComputeRTXLidarFlatScan",
                "PostProcessDispatchIsaacSimulationGate",
                omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                    "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                ),
            ],
            category=BRIDGE_NAME,
        )

    def unregister_nodes(self):
        for writer in rep.WriterRegistry.get_writers(category=BRIDGE_NAME):
            rep.writers.unregister_writer(writer)
