# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import omni
import carb
from omni.syntheticdata import sensors, helpers
import omni.syntheticdata._syntheticdata as sd
import omni.syntheticdata
import omni.graph.core as og
from dataclasses import dataclass
from pxr import Usd
from omni.isaac.ros_bridge.ogn.OgnROS1CameraHelperDatabase import OgnROS1CameraHelperDatabase


class OgnROS1CameraHelper:
    @dataclass
    class State:
        initialized: bool = False
        graph = None
        viewport = None
        viewport_name = ""
        nodes = []

    @staticmethod
    def initialize(graph_context, node):
        pass

    @staticmethod
    def internal_state() -> State:
        return OgnROS1CameraHelper.State()

    @staticmethod
    def compute(db) -> bool:
        if db.internal_state.initialized is False:
            db.internal_state.initialized = True
            stage = omni.usd.get_context().get_stage()
            keys = og.Controller.Keys

            vp = omni.kit.viewport_legacy.get_viewport_interface()
            for instance in vp.get_instance_list():
                if vp.get_viewport_window_name(instance) == db.inputs.viewport:
                    db.internal_state.viewport = vp.get_viewport_window(instance)
                    db.internal_state.viewport_name = vp.get_viewport_window_name(instance)
                    break
            if db.internal_state.viewport == None:
                carb.log_error("viewport name {db.inputs.viewport} not found")
                db.internal_state.initialized = False
                return False

            sensor_type = db.inputs.sensor

            if sensor_type == "rgb":
                sensors.enable_sensors(db.internal_state.viewport, [sd.SensorType.Rgb])

                db.internal_state.graph = omni.syntheticdata.SyntheticData._get_graph_path(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,
                    db.internal_state.viewport.get_render_product_path(),
                )
                rendervar_name = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(
                    sd.SensorType.Rgb.name
                )

                raw_array_path = omni.syntheticdata.SyntheticData._get_node_path(
                    rendervar_name + "ExportRawArray", db.internal_state.viewport.get_render_product_path()
                )
                rgba_to_rgb_name = rendervar_name + "RGBAToRGB" + db.internal_state.viewport.get_render_product_path()
                publish_name = rendervar_name + "PublishRGB" + db.internal_state.viewport.get_render_product_path()
                time_name = rendervar_name + "SimTimeRGB" + db.internal_state.viewport.get_render_product_path()
                try:
                    with Usd.EditContext(stage, stage.GetSessionLayer()):
                        (_, db.internal_state.nodes, _, _) = og.Controller.edit(
                            db.internal_state.graph,
                            {
                                keys.CREATE_NODES: [
                                    (rgba_to_rgb_name, "omni.isaac.core_nodes.IsaacConvertRGBAToRGB"),
                                    (publish_name, "omni.isaac.ros_bridge.ROS1PublishImage"),
                                    (time_name, "omni.isaac.core_nodes.IsaacReadSimulationTime"),
                                ],
                                keys.SET_VALUES: [
                                    (rgba_to_rgb_name + ".inputs:encoding", "rgba8"),
                                    (publish_name + ".inputs:frameId", db.inputs.frameId),
                                    (publish_name + ".inputs:nodeNamespace", db.inputs.nodeNamespace),
                                    (publish_name + ".inputs:queueSize", db.inputs.queueSize),
                                    (publish_name + ".inputs:topicName", db.inputs.topicName),
                                ],
                                keys.CONNECT: [
                                    (raw_array_path + ".outputs:exec", rgba_to_rgb_name + ".inputs:execIn"),
                                    (raw_array_path + ".outputs:data", rgba_to_rgb_name + ".inputs:data"),
                                    (raw_array_path + ".outputs:height", rgba_to_rgb_name + ".inputs:height"),
                                    (raw_array_path + ".outputs:width", rgba_to_rgb_name + ".inputs:width"),
                                    (raw_array_path + ".outputs:swhFrameNumber", time_name + ".inputs:swhFrameNumber"),
                                    (rgba_to_rgb_name + ".outputs:execOut", publish_name + ".inputs:execIn"),
                                    (rgba_to_rgb_name + ".outputs:data", publish_name + ".inputs:data"),
                                    (rgba_to_rgb_name + ".outputs:encoding", publish_name + ".inputs:encoding"),
                                    (rgba_to_rgb_name + ".outputs:height", publish_name + ".inputs:height"),
                                    (rgba_to_rgb_name + ".outputs:width", publish_name + ".inputs:width"),
                                    (time_name + ".outputs:simulationTime", publish_name + ".inputs:timeStamp"),
                                ],
                            },
                        )
                except Exception as e:
                    print(e)
                    pass
            elif sensor_type == "depth":
                sensors.enable_sensors(db.internal_state.viewport, [sd.SensorType.DistanceToImagePlane])

                db.internal_state.graph = omni.syntheticdata.SyntheticData._get_graph_path(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,
                    db.internal_state.viewport.get_render_product_path(),
                )
                rendervar_name = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(
                    sd.SensorType.DistanceToImagePlane.name
                )

                raw_array_path = omni.syntheticdata.SyntheticData._get_node_path(
                    rendervar_name + "ExportRawArray", db.internal_state.viewport.get_render_product_path()
                )
                publish_name = rendervar_name + "PublishDepth" + db.internal_state.viewport.get_render_product_path()
                time_name = rendervar_name + "SimTimeDepth" + db.internal_state.viewport.get_render_product_path()
                try:
                    with Usd.EditContext(stage, stage.GetSessionLayer()):
                        (_, db.internal_state.nodes, _, _) = og.Controller.edit(
                            db.internal_state.graph,
                            {
                                keys.CREATE_NODES: [
                                    (publish_name, "omni.isaac.ros_bridge.ROS1PublishImage"),
                                    (time_name, "omni.isaac.core_nodes.IsaacReadSimulationTime"),
                                ],
                                keys.SET_VALUES: [
                                    (publish_name + ".inputs:encoding", "32FC1"),
                                    (publish_name + ".inputs:frameId", db.inputs.frameId),
                                    (publish_name + ".inputs:nodeNamespace", db.inputs.nodeNamespace),
                                    (publish_name + ".inputs:queueSize", db.inputs.queueSize),
                                    (publish_name + ".inputs:topicName", db.inputs.topicName),
                                ],
                                keys.CONNECT: [
                                    (raw_array_path + ".outputs:exec", publish_name + ".inputs:execIn"),
                                    (raw_array_path + ".outputs:data", publish_name + ".inputs:data"),
                                    (raw_array_path + ".outputs:height", publish_name + ".inputs:height"),
                                    (raw_array_path + ".outputs:width", publish_name + ".inputs:width"),
                                    (raw_array_path + ".outputs:swhFrameNumber", time_name + ".inputs:swhFrameNumber"),
                                    (time_name + ".outputs:simulationTime", publish_name + ".inputs:timeStamp"),
                                ],
                            },
                        )
                except Exception as e:
                    print(e)
                    pass
            elif sensor_type == "depth_pcl":
                sensors.enable_sensors(db.internal_state.viewport, [sd.SensorType.DistanceToImagePlane])

                db.internal_state.graph = omni.syntheticdata.SyntheticData._get_graph_path(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,
                    db.internal_state.viewport.get_render_product_path(),
                )
                rendervar_name = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(
                    sd.SensorType.DistanceToImagePlane.name
                )

                raw_array_path = omni.syntheticdata.SyntheticData._get_node_path(
                    rendervar_name + "ExportRawArray", db.internal_state.viewport.get_render_product_path()
                )
                publish_name = rendervar_name + "PublishDepthPcl" + db.internal_state.viewport.get_render_product_path()
                convert_name = rendervar_name + "ConvertDepthPCL" + db.internal_state.viewport.get_render_product_path()
                camerainfo_name = (
                    rendervar_name + "CameraInfoDepth" + db.internal_state.viewport.get_render_product_path()
                )
                time_name = rendervar_name + "SimTimeDepth" + db.internal_state.viewport.get_render_product_path()
                try:
                    with Usd.EditContext(stage, stage.GetSessionLayer()):
                        (_, db.internal_state.nodes, _, _) = og.Controller.edit(
                            db.internal_state.graph,
                            {
                                keys.CREATE_NODES: [
                                    (publish_name, "omni.isaac.ros_bridge.ROS1PublishPointCloud"),
                                    (convert_name, "omni.isaac.core_nodes.IsaacConvertDepthToPointCloud"),
                                    (camerainfo_name, "omni.isaac.core_nodes.IsaacReadCameraInfo"),
                                    (time_name, "omni.isaac.core_nodes.IsaacReadSimulationTime"),
                                ],
                                keys.SET_VALUES: [
                                    (publish_name + ".inputs:frameId", db.inputs.frameId),
                                    (publish_name + ".inputs:nodeNamespace", db.inputs.nodeNamespace),
                                    (publish_name + ".inputs:queueSize", db.inputs.queueSize),
                                    (publish_name + ".inputs:topicName", db.inputs.topicName),
                                    (camerainfo_name + ".inputs:viewport", db.internal_state.viewport_name),
                                ],
                                keys.CONNECT: [
                                    (raw_array_path + ".outputs:exec", convert_name + ".inputs:execIn"),
                                    (raw_array_path + ".outputs:data", convert_name + ".inputs:data"),
                                    (raw_array_path + ".outputs:format", convert_name + ".inputs:format"),
                                    (raw_array_path + ".outputs:height", convert_name + ".inputs:height"),
                                    (raw_array_path + ".outputs:width", convert_name + ".inputs:width"),
                                    (camerainfo_name + ".outputs:focalLength", convert_name + ".inputs:focalLength"),
                                    (
                                        camerainfo_name + ".outputs:horizontalAperture",
                                        convert_name + ".inputs:horizontalAperture",
                                    ),
                                    (
                                        camerainfo_name + ".outputs:verticalAperture",
                                        convert_name + ".inputs:verticalAperture",
                                    ),
                                    (convert_name + ".outputs:execOut", publish_name + ".inputs:execIn"),
                                    (convert_name + ".outputs:pointCloudData", publish_name + ".inputs:pointCloudData"),
                                    (raw_array_path + ".outputs:swhFrameNumber", time_name + ".inputs:swhFrameNumber"),
                                    (time_name + ".outputs:simulationTime", publish_name + ".inputs:timeStamp"),
                                ],
                            },
                        )
                except Exception as e:
                    print(e)
                    pass
            elif sensor_type == "instance_segmentation":
                # TODO
                pass
            elif sensor_type == "semantic_segmentation":
                # TODO
                pass
            elif sensor_type == "bbox_2d_tight":
                # TODO
                pass
            elif sensor_type == "bbox_2d_loose":
                # TODO
                pass
            elif sensor_type == "bbox_3d":
                # TODO
                pass
            else:
                carb.log_error("sensor type is not supported")
                db.internal_state.initialized = False
                return False

        return True

    @staticmethod
    def release(node):
        # handle deletion of created nodes here
        try:
            state = OgnROS1CameraHelperDatabase.per_node_internal_state(node)
        except Exception as e:
            state = None
            pass

        keys = og.Controller.Keys
        if state is not None and state.graph is not None and state.nodes is not None:
            stage = omni.usd.get_context().get_stage()
            with Usd.EditContext(stage, stage.GetSessionLayer()):
                try:
                    og.Controller.edit(state.graph, {keys.DELETE_NODES: state.nodes})
                except Exception as e:
                    print(e)
                    pass
