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
from omni.replicator.core import AnnotatorRegistry


class OgnROS1CameraHelper:
    @dataclass
    class State:
        initialized: bool = False
        graph = None
        viewport = None
        viewport_name = ""
        nodes = []
        publisher = None

    @staticmethod
    def initialize(graph_context, node):
        pass

    @staticmethod
    def internal_state() -> State:
        return OgnROS1CameraHelper.State()

    @staticmethod
    def enable_sensor(viewport, sensor_type):
        sensors.enable_sensors(viewport, [sensor_type])
        graph = omni.syntheticdata.SyntheticData._get_graph_path(
            omni.syntheticdata.SyntheticDataStage.ON_DEMAND, viewport.get_render_product_path()
        )
        rendervar = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(sensor_type.name)

        rawarray = omni.syntheticdata.SyntheticData._get_node_path(
            rendervar + "ExportRawArray", viewport.get_render_product_path()
        )

        return graph, rendervar, rawarray

    # @staticmethod
    # def get_names(viewport, sensor_type, names):
    #     rendervar = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(sensor_type.name)
    #     output = []
    #     for n in names:
    #         output.append(rendervar + n + sensor_type.name + viewport.get_render_product_path())
    #     return output

    @staticmethod
    def compute(db) -> bool:
        if db.internal_state.initialized is False:
            db.internal_state.initialized = True
            stage = omni.usd.get_context().get_stage()
            keys = og.Controller.Keys
            with Usd.EditContext(stage, stage.GetSessionLayer()):
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

                sensor_type = db.inputs.type
                viewport = db.internal_state.viewport
                render_product_prefix = viewport.get_render_product_path().split("/")[-1] + "_"
                try:
                    if sensor_type == "rgb":

                        db.internal_state.graph, rendervar_name, raw_array_path = OgnROS1CameraHelper.enable_sensor(
                            viewport, sd.SensorType.Rgb
                        )
                        publish_name = render_product_prefix + rendervar_name + "PublishRGB"
                        time_name = render_product_prefix + rendervar_name + "SimTimeRGB"
                        rgba_to_rgb_name = render_product_prefix + rendervar_name + "RGBAToRGB"
                        db.internal_state.publisher = publish_name
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
                    elif sensor_type == "depth":
                        db.internal_state.graph, rendervar_name, raw_array_path = OgnROS1CameraHelper.enable_sensor(
                            viewport, sd.SensorType.DistanceToImagePlane
                        )

                        publish_name = render_product_prefix + rendervar_name + "PublishDepth"
                        time_name = render_product_prefix + rendervar_name + "SimTimeDepth"
                        db.internal_state.publisher = publish_name
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
                    elif sensor_type == "depth_pcl":
                        db.internal_state.graph, rendervar_name, raw_array_path = OgnROS1CameraHelper.enable_sensor(
                            viewport, sd.SensorType.DistanceToImagePlane
                        )

                        publish_name = render_product_prefix + rendervar_name + "PublishDepthPcl"
                        convert_name = render_product_prefix + rendervar_name + "ConvertDepthPCL"
                        camerainfo_name = render_product_prefix + rendervar_name + "CameraInfoDepthPcl"
                        time_name = render_product_prefix + rendervar_name + "SimTimeDepthPcl"
                        db.internal_state.publisher = publish_name
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
                                    (camerainfo_name + ".inputs:viewport", db.internal_state.viewport_name),
                                    (publish_name + ".inputs:frameId", db.inputs.frameId),
                                    (publish_name + ".inputs:nodeNamespace", db.inputs.nodeNamespace),
                                    (publish_name + ".inputs:queueSize", db.inputs.queueSize),
                                    (publish_name + ".inputs:topicName", db.inputs.topicName),
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
                    elif sensor_type == "instance_segmentation":

                        annotator = AnnotatorRegistry.get_annotator("instance_segmentation")
                        annotator.attach([viewport.get_render_product_path()])
                        instance_path = og.ObjectLookup.node_path(annotator.get_node())
                        rendervar_name = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(
                            sd.SensorType.InstanceSegmentation.name
                        )
                        publish_name = render_product_prefix + rendervar_name + "PublishInstance"
                        db.internal_state.graph, _ = og.ObjectLookup.split_graph_from_node_path(instance_path)

                        time_name = render_product_prefix + rendervar_name + "SimTimeInstance"
                        db.internal_state.publisher = publish_name
                        (_, db.internal_state.nodes, _, _) = og.Controller.edit(
                            db.internal_state.graph,
                            {
                                keys.CREATE_NODES: [
                                    (publish_name, "omni.isaac.ros_bridge.ROS1PublishImage"),
                                    (time_name, "omni.isaac.core_nodes.IsaacReadSimulationTime"),
                                ],
                                keys.SET_VALUES: [
                                    (publish_name + ".inputs:encoding", "32SC1"),
                                    (publish_name + ".inputs:frameId", db.inputs.frameId),
                                    (publish_name + ".inputs:nodeNamespace", db.inputs.nodeNamespace),
                                    (publish_name + ".inputs:queueSize", db.inputs.queueSize),
                                    (publish_name + ".inputs:topicName", db.inputs.topicName),
                                ],
                                keys.CONNECT: [
                                    (instance_path + ".outputs:exec", publish_name + ".inputs:execIn"),
                                    (instance_path + ".outputs:data", publish_name + ".inputs:data"),
                                    (instance_path + ".outputs:height", publish_name + ".inputs:height"),
                                    (instance_path + ".outputs:width", publish_name + ".inputs:width"),
                                    (instance_path + ".outputs:swhFrameNumber", time_name + ".inputs:swhFrameNumber"),
                                    (time_name + ".outputs:simulationTime", publish_name + ".inputs:timeStamp"),
                                ],
                            },
                        )
                    elif sensor_type == "semantic_segmentation":
                        annotator = AnnotatorRegistry.get_annotator(
                            "semantic_segmentation", init_params={"semanticTypes": ["class"]}
                        )
                        annotator.attach([viewport.get_render_product_path()])
                        semantic_path = og.ObjectLookup.node_path(annotator.get_node())
                        rendervar_name = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(
                            sd.SensorType.SemanticSegmentation.name
                        )
                        publish_name = render_product_prefix + rendervar_name + "PublishSemantic"
                        db.internal_state.graph, _ = og.ObjectLookup.split_graph_from_node_path(semantic_path)

                        time_name = render_product_prefix + rendervar_name + "SimTimeSemantic"
                        db.internal_state.publisher = publish_name
                        (_, db.internal_state.nodes, _, _) = og.Controller.edit(
                            db.internal_state.graph,
                            {
                                keys.CREATE_NODES: [
                                    (publish_name, "omni.isaac.ros_bridge.ROS1PublishImage"),
                                    (time_name, "omni.isaac.core_nodes.IsaacReadSimulationTime"),
                                ],
                                keys.SET_VALUES: [
                                    (publish_name + ".inputs:encoding", "32SC1"),
                                    (publish_name + ".inputs:frameId", db.inputs.frameId),
                                    (publish_name + ".inputs:nodeNamespace", db.inputs.nodeNamespace),
                                    (publish_name + ".inputs:queueSize", db.inputs.queueSize),
                                    (publish_name + ".inputs:topicName", db.inputs.topicName),
                                ],
                                keys.CONNECT: [
                                    (semantic_path + ".outputs:exec", publish_name + ".inputs:execIn"),
                                    (semantic_path + ".outputs:data", publish_name + ".inputs:data"),
                                    (semantic_path + ".outputs:height", publish_name + ".inputs:height"),
                                    (semantic_path + ".outputs:width", publish_name + ".inputs:width"),
                                    (semantic_path + ".outputs:swhFrameNumber", time_name + ".inputs:swhFrameNumber"),
                                    (time_name + ".outputs:simulationTime", publish_name + ".inputs:timeStamp"),
                                ],
                            },
                        )
                    elif sensor_type == "bbox_2d_tight":

                        annotator = AnnotatorRegistry.get_annotator(
                            "bounding_box_2d_tight", init_params={"semanticTypes": ["class"]}
                        )
                        annotator.attach([viewport.get_render_product_path()])
                        bbox_path = og.ObjectLookup.node_path(annotator.get_node())
                        rendervar_name = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(
                            sd.SensorType.BoundingBox2DTight.name
                        )
                        publish_name = render_product_prefix + rendervar_name + "PublishBbox2DTight"
                        db.internal_state.graph, _ = og.ObjectLookup.split_graph_from_node_path(bbox_path)

                        time_name = render_product_prefix + rendervar_name + "SimTimeBbox2DTight"
                        db.internal_state.publisher = publish_name
                        (_, db.internal_state.nodes, _, _) = og.Controller.edit(
                            db.internal_state.graph,
                            {
                                keys.CREATE_NODES: [
                                    (publish_name, "omni.isaac.ros_bridge.ROS1PublishBbox2D"),
                                    (time_name, "omni.isaac.core_nodes.IsaacReadSimulationTime"),
                                ],
                                keys.SET_VALUES: [
                                    (publish_name + ".inputs:frameId", db.inputs.frameId),
                                    (publish_name + ".inputs:nodeNamespace", db.inputs.nodeNamespace),
                                    (publish_name + ".inputs:queueSize", db.inputs.queueSize),
                                    (publish_name + ".inputs:topicName", db.inputs.topicName),
                                ],
                                keys.CONNECT: [
                                    (bbox_path + ".outputs:exec", publish_name + ".inputs:execIn"),
                                    (bbox_path + ".outputs:data", publish_name + ".inputs:data"),
                                    (bbox_path + ".outputs:swhFrameNumber", time_name + ".inputs:swhFrameNumber"),
                                    (time_name + ".outputs:simulationTime", publish_name + ".inputs:timeStamp"),
                                ],
                            },
                        )

                        # pass
                    elif sensor_type == "bbox_2d_loose":
                        annotator = AnnotatorRegistry.get_annotator(
                            "bounding_box_2d_loose", init_params={"semanticTypes": ["class"]}
                        )
                        annotator.attach([viewport.get_render_product_path()])
                        bbox_path = og.ObjectLookup.node_path(annotator.get_node())
                        rendervar_name = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(
                            sd.SensorType.BoundingBox2DLoose.name
                        )
                        publish_name = render_product_prefix + rendervar_name + "PublishBbox2DLoose"
                        db.internal_state.graph, _ = og.ObjectLookup.split_graph_from_node_path(bbox_path)

                        time_name = render_product_prefix + rendervar_name + "SimTimeBbox2DLoose"
                        db.internal_state.publisher = publish_name
                        (_, db.internal_state.nodes, _, _) = og.Controller.edit(
                            db.internal_state.graph,
                            {
                                keys.CREATE_NODES: [
                                    (publish_name, "omni.isaac.ros_bridge.ROS1PublishBbox2D"),
                                    (time_name, "omni.isaac.core_nodes.IsaacReadSimulationTime"),
                                ],
                                keys.SET_VALUES: [
                                    (publish_name + ".inputs:frameId", db.inputs.frameId),
                                    (publish_name + ".inputs:nodeNamespace", db.inputs.nodeNamespace),
                                    (publish_name + ".inputs:queueSize", db.inputs.queueSize),
                                    (publish_name + ".inputs:topicName", db.inputs.topicName),
                                ],
                                keys.CONNECT: [
                                    (bbox_path + ".outputs:exec", publish_name + ".inputs:execIn"),
                                    (bbox_path + ".outputs:data", publish_name + ".inputs:data"),
                                    (bbox_path + ".outputs:swhFrameNumber", time_name + ".inputs:swhFrameNumber"),
                                    (time_name + ".outputs:simulationTime", publish_name + ".inputs:timeStamp"),
                                ],
                            },
                        )
                    elif sensor_type == "bbox_3d":
                        annotator = AnnotatorRegistry.get_annotator(
                            "bounding_box_3d", init_params={"semanticTypes": ["class"]}
                        )
                        annotator.attach([viewport.get_render_product_path()])
                        bbox_path = og.ObjectLookup.node_path(annotator.get_node())
                        rendervar_name = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(
                            sd.SensorType.BoundingBox3D.name
                        )
                        publish_name = render_product_prefix + rendervar_name + "PublishBbox3D"
                        db.internal_state.graph, _ = og.ObjectLookup.split_graph_from_node_path(bbox_path)

                        time_name = render_product_prefix + rendervar_name + "SimTimeBbox3D"
                        db.internal_state.publisher = publish_name
                        (_, db.internal_state.nodes, _, _) = og.Controller.edit(
                            db.internal_state.graph,
                            {
                                keys.CREATE_NODES: [
                                    (publish_name, "omni.isaac.ros_bridge.ROS1PublishBbox3D"),
                                    (time_name, "omni.isaac.core_nodes.IsaacReadSimulationTime"),
                                ],
                                keys.SET_VALUES: [
                                    (publish_name + ".inputs:frameId", db.inputs.frameId),
                                    (publish_name + ".inputs:nodeNamespace", db.inputs.nodeNamespace),
                                    (publish_name + ".inputs:queueSize", db.inputs.queueSize),
                                    (publish_name + ".inputs:topicName", db.inputs.topicName),
                                ],
                                keys.CONNECT: [
                                    (bbox_path + ".outputs:exec", publish_name + ".inputs:execIn"),
                                    (bbox_path + ".outputs:data", publish_name + ".inputs:data"),
                                    (bbox_path + ".outputs:swhFrameNumber", time_name + ".inputs:swhFrameNumber"),
                                    (time_name + ".outputs:simulationTime", publish_name + ".inputs:timeStamp"),
                                ],
                            },
                        )
                    elif sensor_type == "camera_info":

                        # this created the basic on new frame event
                        sensors.get_synthetic_data().activate_node_template(
                            "PostProcessDispatch", 0, [viewport.get_render_product_path()]
                        )
                        db.internal_state.graph = omni.syntheticdata.SyntheticData._get_graph_path(
                            omni.syntheticdata.SyntheticDataStage.ON_DEMAND, viewport.get_render_product_path()
                        )
                        dispatch = omni.syntheticdata.SyntheticData._get_node_path(
                            "PostProcessDispatch", viewport.get_render_product_path()
                        )
                        publish_name = render_product_prefix + "PublishCameraInfo"
                        read_info = render_product_prefix + "ReadCameraInfo"
                        time_name = render_product_prefix + "SimTimeCameraInfo"
                        db.internal_state.publisher = publish_name
                        (_, db.internal_state.nodes, _, _) = og.Controller.edit(
                            db.internal_state.graph,
                            {
                                keys.CREATE_NODES: [
                                    (publish_name, "omni.isaac.ros_bridge.ROS1PublishCameraInfo"),
                                    (read_info, "omni.isaac.core_nodes.IsaacReadCameraInfo"),
                                    (time_name, "omni.isaac.core_nodes.IsaacReadSimulationTime"),
                                ],
                                keys.SET_VALUES: [
                                    (read_info + ".inputs:viewport", db.inputs.viewport),
                                    (publish_name + ".inputs:frameId", db.inputs.frameId),
                                    (publish_name + ".inputs:nodeNamespace", db.inputs.nodeNamespace),
                                    (publish_name + ".inputs:queueSize", db.inputs.queueSize),
                                    (publish_name + ".inputs:topicName", db.inputs.topicName),
                                ],
                                keys.CONNECT: [
                                    (dispatch + ".outputs:exec", publish_name + ".inputs:execIn"),
                                    (read_info + ".outputs:width", publish_name + ".inputs:width"),
                                    (read_info + ".outputs:height", publish_name + ".inputs:height"),
                                    (read_info + ".outputs:focalLength", publish_name + ".inputs:focalLength"),
                                    (
                                        read_info + ".outputs:horizontalAperture",
                                        publish_name + ".inputs:horizontalAperture",
                                    ),
                                    (
                                        read_info + ".outputs:verticalAperture",
                                        publish_name + ".inputs:verticalAperture",
                                    ),
                                    (
                                        read_info + ".outputs:horizontalOffset",
                                        publish_name + ".inputs:horizontalOffset",
                                    ),
                                    (read_info + ".outputs:verticalOffset", publish_name + ".inputs:verticalOffset"),
                                    (read_info + ".outputs:projectionType", publish_name + ".inputs:projectionType"),
                                    # TODO: stereo offset
                                    (dispatch + ".outputs:swhFrameNumber", time_name + ".inputs:swhFrameNumber"),
                                    (time_name + ".outputs:simulationTime", publish_name + ".inputs:timeStamp"),
                                ],
                            },
                        )
                    else:
                        carb.log_error("sensor type is not supported")
                        db.internal_state.initialized = False
                        return False

                    # Connect timestamp

                    # og.Controller.edit(
                    #     db.internal_state.graph,
                    #     {
                    #         keys.SET_VALUES: [
                    #             (publish_name+  ".inputs:frameId", db.inputs.frameId),
                    #             (publish_name+  ".inputs:nodeNamespace", db.inputs.nodeNamespace),
                    #             (publish_name+  ".inputs:queueSize", db.inputs.queueSize),
                    #             (publish_name+  ".inputs:topicName", db.inputs.topicName),
                    #         ],
                    #     },
                    # )
                except Exception as e:
                    print(e)
                    pass
        else:
            if db.internal_state.graph:
                pass
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
