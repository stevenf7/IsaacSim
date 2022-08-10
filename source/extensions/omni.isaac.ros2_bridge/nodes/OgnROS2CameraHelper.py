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
from omni.isaac.ros2_bridge.ogn.OgnROS2CameraHelperDatabase import OgnROS2CameraHelperDatabase
from omni.isaac.core_nodes.scripts.utils import submit_node_template_activation
from omni.replicator.core import AnnotatorRegistry
import traceback


class OgnROS2CameraHelper:
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
        return OgnROS2CameraHelper.State()

    @staticmethod
    def compute(db) -> bool:
        sensor_type = db.inputs.type
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
                    carb.log_warn("viewport name {db.inputs.viewport} not found")
                    db.internal_state.initialized = False
                    return False

                viewport = db.internal_state.viewport
                render_product_prefix = viewport.get_render_product_path().split("/")[-1] + "_"
                try:
                    if sensor_type == "rgb":

                        rv = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(sd.SensorType.Rgb.name)
                        submit_node_template_activation(
                            rv + "ROS2PublishImage",
                            0,
                            [viewport.get_render_product_path()],
                            attributes={
                                "inputs:frameId": db.inputs.frameId,
                                "inputs:nodeNamespace": db.inputs.nodeNamespace,
                                "inputs:queueSize": db.inputs.queueSize,
                                "inputs:topicName": db.inputs.topicName,
                                "inputs:context": db.inputs.context,
                            },
                        )
                    elif sensor_type == "depth":
                        rv = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(
                            sd.SensorType.DistanceToImagePlane.name
                        )
                        submit_node_template_activation(
                            rv + "ROS2PublishImage",
                            0,
                            [viewport.get_render_product_path()],
                            attributes={
                                "inputs:frameId": db.inputs.frameId,
                                "inputs:nodeNamespace": db.inputs.nodeNamespace,
                                "inputs:queueSize": db.inputs.queueSize,
                                "inputs:topicName": db.inputs.topicName,
                                "inputs:context": db.inputs.context,
                            },
                        )
                    elif sensor_type == "depth_pcl":

                        rv = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(
                            sd.SensorType.DistanceToImagePlane.name
                        )
                        submit_node_template_activation(
                            "IsaacReadCameraInfo",
                            0,
                            [viewport.get_render_product_path()],
                            attributes={"inputs:viewport": db.internal_state.viewport_name},
                        )
                        submit_node_template_activation(
                            rv + "ROS2PublishPointCloud",
                            0,
                            [viewport.get_render_product_path()],
                            attributes={
                                "inputs:frameId": db.inputs.frameId,
                                "inputs:nodeNamespace": db.inputs.nodeNamespace,
                                "inputs:queueSize": db.inputs.queueSize,
                                "inputs:topicName": db.inputs.topicName,
                                "inputs:context": db.inputs.context,
                            },
                        )

                    elif sensor_type == "instance_segmentation":

                        submit_node_template_activation(
                            "ROS2PublishInstanceSegmentation",
                            0,
                            [viewport.get_render_product_path()],
                            attributes={
                                "inputs:frameId": db.inputs.frameId,
                                "inputs:nodeNamespace": db.inputs.nodeNamespace,
                                "inputs:queueSize": db.inputs.queueSize,
                                "inputs:topicName": db.inputs.topicName,
                                "inputs:context": db.inputs.context,
                            },
                        )

                    elif sensor_type == "semantic_segmentation":

                        submit_node_template_activation(
                            "ROS2PublishSemanticSegmentation",
                            0,
                            [viewport.get_render_product_path()],
                            attributes={
                                "inputs:frameId": db.inputs.frameId,
                                "inputs:nodeNamespace": db.inputs.nodeNamespace,
                                "inputs:queueSize": db.inputs.queueSize,
                                "inputs:topicName": db.inputs.topicName,
                                "inputs:context": db.inputs.context,
                            },
                        )

                    elif sensor_type == "bbox_2d_tight":

                        submit_node_template_activation(
                            "ROS2PublishBoundingBox2DTight",
                            0,
                            [viewport.get_render_product_path()],
                            attributes={
                                "inputs:frameId": db.inputs.frameId,
                                "inputs:nodeNamespace": db.inputs.nodeNamespace,
                                "inputs:queueSize": db.inputs.queueSize,
                                "inputs:topicName": db.inputs.topicName,
                                "inputs:context": db.inputs.context,
                            },
                        )
                    elif sensor_type == "bbox_2d_loose":

                        submit_node_template_activation(
                            "ROS2PublishBoundingBox2DTight",
                            0,
                            [viewport.get_render_product_path()],
                            attributes={
                                "inputs:frameId": db.inputs.frameId,
                                "inputs:nodeNamespace": db.inputs.nodeNamespace,
                                "inputs:queueSize": db.inputs.queueSize,
                                "inputs:topicName": db.inputs.topicName,
                                "inputs:context": db.inputs.context,
                            },
                        )
                    elif sensor_type == "bbox_3d":

                        submit_node_template_activation(
                            "ROS2PublishBoundingBox3D",
                            0,
                            [viewport.get_render_product_path()],
                            attributes={
                                "inputs:frameId": db.inputs.frameId,
                                "inputs:nodeNamespace": db.inputs.nodeNamespace,
                                "inputs:queueSize": db.inputs.queueSize,
                                "inputs:topicName": db.inputs.topicName,
                                "inputs:context": db.inputs.context,
                            },
                        )
                    elif sensor_type == "camera_info":
                        submit_node_template_activation(
                            "IsaacReadCameraInfo",
                            0,
                            [viewport.get_render_product_path()],
                            attributes={"inputs:viewport": db.internal_state.viewport_name},
                        )
                        submit_node_template_activation(
                            "ROS2PublishCameraInfo",
                            0,
                            [viewport.get_render_product_path()],
                            attributes={
                                "inputs:frameId": db.inputs.frameId,
                                "inputs:nodeNamespace": db.inputs.nodeNamespace,
                                "inputs:queueSize": db.inputs.queueSize,
                                "inputs:topicName": db.inputs.topicName,
                                "inputs:stereoOffset": db.inputs.stereoOffset,
                                "inputs:context": db.inputs.context,
                            },
                        )

                    else:
                        carb.log_error("type is not supported")
                        db.internal_state.initialized = False
                        return False

                    type_dict = {
                        "instance_segmentation": "InstanceSegmentation",
                        "semantic_segmentation": "SemanticSegmentation",
                        "bbox_2d_tight": "BoundingBox2DTight",
                        "bbox_2d_loose": "BoundingBox2DLoose",
                        "bbox_3d": "BoundingBox3D",
                    }
                    if sensor_type in type_dict:
                        if db.inputs.enableSemanticLabels:
                            submit_node_template_activation(
                                type_dict[sensor_type] + "ROS2PublishSemanticLabels",
                                0,
                                [viewport.get_render_product_path()],
                                attributes={
                                    "inputs:nodeNamespace": db.inputs.nodeNamespace,
                                    "inputs:queueSize": db.inputs.queueSize,
                                    "inputs:topicName": db.inputs.semanticLabelsTopicName,
                                    "inputs:context": db.inputs.context,
                                },
                            )

                except Exception as e:
                    print(traceback.format_exc())
                    pass
        else:
            if db.internal_state.graph:
                pass
            return True

    @staticmethod
    def release(node):
        pass
        # # handle deletion of created nodes here
        # try:
        #     state = OgnROS2CameraHelperDatabase.per_node_internal_state(node)
        # except Exception as e:
        #     state = None
        #     pass

        # keys = og.Controller.Keys
        # if state is not None and state.graph is not None and state.nodes is not None:
        #     stage = omni.usd.get_context().get_stage()
        #     with Usd.EditContext(stage, stage.GetSessionLayer()):
        #         try:
        #             og.Controller.edit(state.graph, {keys.DELETE_NODES: state.nodes})
        #         except Exception as e:
        #             print(e)
        #             pass
