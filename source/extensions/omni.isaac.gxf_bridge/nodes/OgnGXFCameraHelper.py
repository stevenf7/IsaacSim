# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import omni
import carb
from omni.kit.viewport.utility import get_viewport_from_window_name
from omni.syntheticdata import sensors, helpers
import omni.syntheticdata._syntheticdata as sd
import omni.syntheticdata
import omni.graph.core as og
from dataclasses import dataclass
from pxr import Usd
from omni.isaac.gxf_bridge.ogn.OgnGXFCameraHelperDatabase import OgnGXFCameraHelperDatabase
from omni.isaac.core_nodes.scripts.utils import submit_node_template_activation
from omni.replicator.core import AnnotatorRegistry
import traceback


class OgnGXFCameraHelper:
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
        return OgnGXFCameraHelper.State()

    @staticmethod
    def compute(db) -> bool:
        sensor_type = db.inputs.type
        if db.internal_state.initialized is False:
            db.internal_state.initialized = True
            stage = omni.usd.get_context().get_stage()
            keys = og.Controller.Keys
            with Usd.EditContext(stage, stage.GetSessionLayer()):
                if db.inputs.viewport:
                    db.log_warn(
                        "viewport input is deprecated, please use renderProductPath and the IsaacGetViewportRenderProduct to get a viewports render product path"
                    )
                    viewport_api = get_viewport_from_window_name(db.inputs.viewport)
                    if viewport_api:
                        db.internal_state.viewport = viewport_api
                        db.internal_state.viewport_name = db.inputs.viewport
                    if db.internal_state.viewport == None:
                        carb.log_warn("viewport name {db.inputs.viewport} not found")
                        db.internal_state.initialized = False
                        return False

                    viewport = db.internal_state.viewport
                    render_product_path = viewport.get_render_product_path()
                else:
                    render_product_path = db.inputs.renderProductPath
                    if stage.GetPrimAtPath(render_product_path) is None:
                        carb.log_warn("Render product no created yet, retrying on next call")
                        db.internal_state.initialized = False
                        return False

                try:
                    if sensor_type == "rgb":

                        rv = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(sd.SensorType.Rgb.name)
                        submit_node_template_activation(
                            rv + "GXFPublishImage",
                            0,
                            [render_product_path],
                            attributes={
                                "inputs:context": db.inputs.context,
                                "inputs:outputEntity": db.inputs.outputEntity,
                                "inputs:outputComponent": db.inputs.outputComponent,
                                "inputs:poseFrame": db.inputs.poseFrame,
                            },
                        )
                    elif sensor_type == "depth":
                        rv = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(
                            sd.SensorType.DistanceToImagePlane.name
                        )
                        submit_node_template_activation(
                            rv + "GXFPublishImage",
                            0,
                            [render_product_path],
                            attributes={
                                "inputs:context": db.inputs.context,
                                "inputs:outputEntity": db.inputs.outputEntity,
                                "inputs:outputComponent": db.inputs.outputComponent,
                                "inputs:poseFrame": db.inputs.poseFrame,
                            },
                        )

                    # elif sensor_type == "instance_segmentation":

                    #     submit_node_template_activation(
                    #         "GXFPublishInstanceSegmentation",
                    #         0,
                    #         [render_product_path],
                    #         attributes={
                    #             "inputs:frameId": db.inputs.frameId,
                    #             "inputs:nodeNamespace": db.inputs.nodeNamespace,
                    #             "inputs:queueSize": db.inputs.queueSize,
                    #             "inputs:topicName": db.inputs.topicName,
                    #         },
                    #     )

                    # elif sensor_type == "semantic_segmentation":

                    #     submit_node_template_activation(
                    #         "GXFPublishSemanticSegmentation",
                    #         0,
                    #         [render_product_path],
                    #         attributes={
                    #             "inputs:frameId": db.inputs.frameId,
                    #             "inputs:nodeNamespace": db.inputs.nodeNamespace,
                    #             "inputs:queueSize": db.inputs.queueSize,
                    #             "inputs:topicName": db.inputs.topicName,
                    #         },
                    #     )

                    # elif sensor_type == "bbox_2d_tight":

                    #     submit_node_template_activation(
                    #         "GXFPublishBoundingBox2DTight",
                    #         0,
                    #         [render_product_path],
                    #         attributes={
                    #             "inputs:frameId": db.inputs.frameId,
                    #             "inputs:nodeNamespace": db.inputs.nodeNamespace,
                    #             "inputs:queueSize": db.inputs.queueSize,
                    #             "inputs:topicName": db.inputs.topicName,
                    #         },
                    #     )
                    # elif sensor_type == "bbox_2d_loose":

                    #     submit_node_template_activation(
                    #         "GXFPublishBoundingBox2DTight",
                    #         0,
                    #         [render_product_path],
                    #         attributes={
                    #             "inputs:frameId": db.inputs.frameId,
                    #             "inputs:nodeNamespace": db.inputs.nodeNamespace,
                    #             "inputs:queueSize": db.inputs.queueSize,
                    #             "inputs:topicName": db.inputs.topicName,
                    #         },
                    #     )
                    # elif sensor_type == "bbox_3d":

                    #     submit_node_template_activation(
                    #         "GXFPublishBoundingBox3D",
                    #         0,
                    #         [render_product_path],
                    #         attributes={
                    #             "inputs:frameId": db.inputs.frameId,
                    #             "inputs:nodeNamespace": db.inputs.nodeNamespace,
                    #             "inputs:queueSize": db.inputs.queueSize,
                    #             "inputs:topicName": db.inputs.topicName,
                    #         },
                    #     )
                    # elif sensor_type == "camera_info":
                    #     submit_node_template_activation(
                    #         "IsaacReadCameraInfo",
                    #         0,
                    #         [render_product_path],
                    #         attributes={"inputs:viewport": db.internal_state.viewport_name},
                    #     )
                    #     submit_node_template_activation(
                    #         "GXFPublishCameraInfo",
                    #         0,
                    #         [render_product_path],
                    #         attributes={
                    #             "inputs:frameId": db.inputs.frameId,
                    #             "inputs:nodeNamespace": db.inputs.nodeNamespace,
                    #             "inputs:queueSize": db.inputs.queueSize,
                    #             "inputs:topicName": db.inputs.topicName,
                    #             "inputs:stereoOffset": db.inputs.stereoOffset,
                    #         },
                    #     )

                    else:
                        carb.log_error("type is not supported")
                        db.internal_state.initialized = False
                        return False

                    # type_dict = {
                    #     "instance_segmentation": "InstanceSegmentation",
                    #     "semantic_segmentation": "SemanticSegmentation",
                    #     "bbox_2d_tight": "BoundingBox2DTight",
                    #     "bbox_2d_loose": "BoundingBox2DLoose",
                    #     "bbox_3d": "BoundingBox3D",
                    # }
                    # if sensor_type in type_dict:
                    #     if db.inputs.enableSemanticLabels:
                    #         submit_node_template_activation(
                    #             type_dict[sensor_type] + "GXFPublishSemanticLabels",
                    #             0,
                    #             [render_product_path],
                    #             attributes={
                    #                 "inputs:nodeNamespace": db.inputs.nodeNamespace,
                    #                 "inputs:queueSize": db.inputs.queueSize,
                    #                 "inputs:topicName": db.inputs.semanticLabelsTopicName,
                    #             },
                    #         )

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
        #     state = OgnGXFCameraHelperDatabase.per_node_internal_state(node)
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
