__copyright__ = "Copyright (c) 2018-2022, NVIDIA CORPORATION. All rights reserved."
__license__ = """
NVIDIA CORPORATION and its licensors retain all intellectual property
and proprietary rights in and to this software, related documentation
and any modifications thereto. Any use, reproduction, disclosure or
distribution of this software and related documentation without an express
license agreement from NVIDIA CORPORATION is strictly prohibited.
"""

import os
import omni.ext
import carb
import omni
from .. import _ros2_bridge
import omni.syntheticdata._syntheticdata as sd
import omni.syntheticdata
from omni.syntheticdata import sensors
import asyncio


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id):
        self._ros2bridge = None
        self.registered_template = []
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        if ext_manager.is_extension_enabled("omni.isaac.ros_bridge"):
            carb.log_error("ROS 2 Bridge extension cannot be enabled if ROS Bridge is enabled")
            ext_manager.set_extension_enabled("omni.isaac.ros2_bridge", False)
            return

        # ROS2 uses LD_LIBRARY_PATH to load libraries at runtime so set it here before the plugin loads.
        self._extension_path = ext_manager.get_extension_path(ext_id)

        if os.environ.get("LD_LIBRARY_PATH"):
            os.environ["LD_LIBRARY_PATH"] = os.environ.get("LD_LIBRARY_PATH") + ":" + self._extension_path + "/bin"
        else:
            os.environ["LD_LIBRARY_PATH"] = self._extension_path + "/bin"

        self._ros2bridge = _ros2_bridge.acquire_ros2_bridge_interface()

        self.register_nodes()

    def on_shutdown(self):
        async def safe_shutdown(bridge):
            omni.timeline.get_timeline_interface().stop()
            await omni.kit.app.get_app().next_update_async()
            if bridge is not None:
                _ros2_bridge.release_ros2_bridge_interface(bridge)

        asyncio.ensure_future(safe_shutdown(self._ros2bridge))
        self.unregister_nodes()

    def register_nodes(self):
        ##### Publish RGB
        rv = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(sd.SensorType.Rgb.name)
        template_name = rv + "ROS2PublishImage"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,  # node template stage
                    "omni.isaac.ros2_bridge.ROS2PublishImage",  # node template type
                    [
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            rv + "IsaacConvertRGBAToRGB",
                            attributes_mapping={
                                "outputs:execOut": "inputs:execIn",
                                "outputs:data": "inputs:data",
                                "outputs:width": "inputs:width",
                                "outputs:height": "inputs:height",
                                "outputs:encoding": "inputs:encoding",
                            },
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                        ),
                    ],
                ),
                template_name=template_name,
            )

            self.registered_template.append(template)
        ##### Publish Depth
        rv = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(sd.SensorType.DistanceToImagePlane.name)
        template_name = rv + "ROS2PublishImage"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,  # node template stage
                    "omni.isaac.ros2_bridge.ROS2PublishImage",  # node template type
                    [
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            rv + "ExportRawArray",
                            attributes_mapping={
                                "outputs:data": "inputs:data",
                                "outputs:width": "inputs:width",
                                "outputs:height": "inputs:height",
                            },
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            rv + "IsaacSimulationGate", attributes_mapping={"outputs:execOut": "inputs:execIn"}
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                        ),
                    ],
                    attributes={"inputs:encoding": "32FC1"},
                ),
                template_name=template_name,
            )

            self.registered_template.append(template)

        # publish depth pcl
        template_name = rv + "ROS2PublishPointCloud"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,  # node template stage
                    "omni.isaac.ros2_bridge.ROS2PublishPointCloud",  # node template type
                    [
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            rv + "IsaacConvertDepthToPointCloud",
                            attributes_mapping={
                                "outputs:pointCloudData": "inputs:pointCloudData",
                                "outputs:execOut": "inputs:execIn",
                            },
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                        ),
                    ],
                ),
                template_name=template_name,
            )

            self.registered_template.append(template)
        # instance
        template_name = "ROS2PublishInstanceSegmentation"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,  # node template stage
                    "omni.isaac.ros2_bridge.ROS2PublishImage",  # node template type
                    [
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "instance_segmentation",
                            attributes_mapping={
                                "outputs:data": "inputs:data",
                                "outputs:width": "inputs:width",
                                "outputs:height": "inputs:height",
                            },
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "InstanceSegmentationIsaacSimulationGate",
                            attributes_mapping={"outputs:execOut": "inputs:execIn"},
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                        ),
                    ],
                    attributes={"inputs:encoding": "32SC1"},
                ),
                template_name=template_name,
            )

            self.registered_template.append(template)
        # Semantic
        template_name = "ROS2PublishSemanticSegmentation"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,  # node template stage
                    "omni.isaac.ros2_bridge.ROS2PublishImage",  # node template type
                    [
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "semantic_segmentation",
                            attributes_mapping={
                                # "input:semanticTypes": ["class"],
                                "outputs:data": "inputs:data",
                                "outputs:width": "inputs:width",
                                "outputs:height": "inputs:height",
                            },
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "SemanticSegmentationIsaacSimulationGate",
                            attributes_mapping={"outputs:execOut": "inputs:execIn"},
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                        ),
                    ],
                    attributes={"inputs:encoding": "32SC1"},
                ),
                template_name=template_name,
            )

            self.registered_template.append(template)
        # Bbox2d tight
        template_name = "ROS2PublishBoundingBox2DTight"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,  # node template stage
                    "omni.isaac.ros2_bridge.ROS2PublishBbox2D",  # node template type
                    [
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "bounding_box_2d_tight",
                            attributes_mapping={"input:semanticTypes": ["class"], "outputs:data": "inputs:data"},
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "BoundingBox2DTightIsaacSimulationGate",
                            attributes_mapping={"outputs:execOut": "inputs:execIn"},
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                        ),
                    ],
                ),
                template_name=template_name,
            )

            self.registered_template.append(template)
        # bbox2d Loose
        template_name = "ROS2PublishBoundingBox2DLoose"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,  # node template stage
                    "omni.isaac.ros2_bridge.ROS2PublishBbox2D",  # node template type
                    [
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "bounding_box_2d_loose",
                            attributes_mapping={"input:semanticTypes": ["class"], "outputs:data": "inputs:data"},
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "BoundingBox2DLooseIsaacSimulationGate",
                            attributes_mapping={"outputs:execOut": "inputs:execIn"},
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                        ),
                    ],
                ),
                template_name=template_name,
            )

            self.registered_template.append(template)
        # bbox3d Loose
        template_name = "ROS2PublishBoundingBox3D"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,  # node template stage
                    "omni.isaac.ros2_bridge.ROS2PublishBbox3D",  # node template type
                    [
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "bounding_box_3d",
                            attributes_mapping={"input:semanticTypes": ["class"], "outputs:data": "inputs:data"},
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "BoundingBox3DIsaacSimulationGate", attributes_mapping={"outputs:execOut": "inputs:execIn"}
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                        ),
                    ],
                ),
                template_name=template_name,
            )

            self.registered_template.append(template)
        # camera info
        template_name = "ROS2PublishCameraInfo"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,  # node template stage
                    "omni.isaac.ros2_bridge.ROS2PublishCameraInfo",  # node template type
                    [
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "IsaacReadCameraInfo",
                            attributes_mapping={
                                "outputs:width": "inputs:width",
                                "outputs:height": "inputs:height",
                                "outputs:focalLength": "inputs:focalLength",
                                "outputs:horizontalAperture": "inputs:horizontalAperture",
                                "outputs:verticalAperture": "inputs:verticalAperture",
                                "outputs:horizontalOffset": "inputs:horizontalOffset",
                                "outputs:verticalOffset": "inputs:verticalOffset",
                                "outputs:projectionType": "inputs:projectionType",
                            },
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "PostProcessDispatchIsaacSimulationGate",
                            attributes_mapping={"outputs:execOut": "inputs:execIn"},
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                        ),
                    ],
                ),
                template_name=template_name,
            )

            self.registered_template.append(template)
        # outputs that we can publish labels for
        label_names = {
            "instance_segmentation": "InstanceSegmentation",
            "semantic_segmentation": "SemanticSegmentation",
            "bounding_box_2d_tight": "BoundingBox2DTight",
            "bounding_box_2d_loose": "BoundingBox2DLoose",
            "bounding_box_3d": "BoundingBox3D",
        }
        for name in label_names.items():
            template_name = name[1] + "ROS2PublishSemanticLabels"
            if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
                template = sensors.get_synthetic_data().register_node_template(
                    omni.syntheticdata.SyntheticData.NodeTemplate(
                        omni.syntheticdata.SyntheticDataStage.ON_DEMAND,
                        "omni.isaac.ros2_bridge.ROS2PublishSemanticLabels",
                        [
                            omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                                name[0], attributes_mapping={"outputs:idToLabels": "inputs:idToLabels"}
                            ),
                            omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                                name[1] + "IsaacSimulationGate", attributes_mapping={"outputs:execOut": "inputs:execIn"}
                            ),
                            omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                                "IsaacReadSimulationTime",
                                attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"},
                            ),
                        ],
                    ),
                    template_name=template_name,
                )
                self.registered_template.append(template)

        # RTX lidar PCL publisher
        template_name = "RtxLidar" + "ROS2PublishPointCloud"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,
                    "omni.isaac.ros2_bridge.ROS2PublishPointCloud",
                    [
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "RtxSensorCpu" + "IsaacComputeRTXLidarPointCloud",
                            attributes_mapping={
                                "outputs:pointCloudData": "inputs:pointCloudData",
                                "outputs:execOut": "inputs:execIn",
                            },
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                        ),
                    ],
                ),
                template_name=template_name,
            )
            self.registered_template.append(template)

        # RTX Radar PCL publisher
        template_name = "RtxRadar" + "ROS2PublishPointCloud"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,
                    "omni.isaac.ros2_bridge.ROS2PublishPointCloud",
                    [
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "RtxSensorCpu" + "IsaacComputeRTXRadarPointCloud",
                            attributes_mapping={
                                "outputs:pointCloudData": "inputs:pointCloudData",
                                "outputs:execOut": "inputs:execIn",
                            },
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                        ),
                    ],
                ),
                template_name=template_name,
            )
            self.registered_template.append(template)

        # RTX lidar LaserScan publisher
        template_name = "RtxSensorCpu" + "ROS2PublishLaserScan"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,
                    "omni.isaac.ros2_bridge.ROS2PublishLaserScan",
                    [
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "RtxSensorCpu" + "IsaacComputeRTXLidarFlatScan",
                            attributes_mapping={
                                "outputs:execOut": "inputs:execIn",
                                "outputs:horizontalFov": "inputs:horizontalFov",
                                "outputs:horizontalResolution": "inputs:horizontalResolution",
                                "outputs:depthRange": "inputs:depthRange",
                                "outputs:rotationRate": "inputs:rotationRate",
                                "outputs:linearDepthData": "inputs:linearDepthData",
                                "outputs:intensitiesData": "inputs:intensitiesData",
                                "outputs:numRows": "inputs:numRows",
                                "outputs:numCols": "inputs:numCols",
                                "outputs:azimuthRange": "inputs:azimuthRange",
                            },
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                        ),
                    ],
                ),
                template_name=template_name,
            )
            self.registered_template.append(template)

    def unregister_nodes(self):
        for template in self.registered_template:
            sensors.get_synthetic_data().unregister_node_template(template)
