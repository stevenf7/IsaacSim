# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import traceback
from dataclasses import dataclass

import carb
import omni
import omni.graph.core as og
import omni.replicator.core as rep
import omni.syntheticdata
import omni.syntheticdata._syntheticdata as sd
from omni.isaac.core_nodes import BaseWriterNode
from omni.kit.viewport.utility import get_viewport_from_window_name
from pxr import Usd


class OgnGXFCameraHelperInternalState(BaseWriterNode):
    def __init__(self):
        self.viewport = None
        self.viewport_name = ""
        self.resetSimulationTimeOnStop = False
        super().__init__(initialize=False)

    def post_attach(self, writer, render_product):
        try:
            omni.syntheticdata.SyntheticData.Get().set_node_attributes(
                "IsaacReadSimulationTime", {"inputs:resetOnStop": self.resetSimulationTimeOnStop}, render_product
            )
        except:
            pass


class OgnGXFCameraHelper:
    @staticmethod
    def internal_state():
        return OgnGXFCameraHelperInternalState()

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
                    if not render_product_path or stage.GetPrimAtPath(render_product_path) is None:
                        carb.log_warn("Render product no created yet, retrying on next call")
                        db.internal_state.initialized = False
                        return False
                db.internal_state.resetSimulationTimeOnStop = db.inputs.resetSimulationTimeOnStop
                writer = None
                try:
                    if sensor_type == "rgb":
                        rv = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(sd.SensorType.Rgb.name)
                        writer = rep.writers.get(rv + "GXFPublishImage")
                        writer.initialize(
                            context=db.inputs.context,
                            outputEntity=db.inputs.outputEntity,
                            outputComponent=db.inputs.outputComponent,
                            poseFrame=db.inputs.poseFrame,
                            stereoOffset=db.inputs.stereoOffset,
                        )
                    elif sensor_type == "depth":
                        rv = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(
                            sd.SensorType.DistanceToImagePlane.name
                        )
                        writer = rep.writers.get(rv + "GXFPublishImage")
                        writer.initialize(
                            context=db.inputs.context,
                            outputEntity=db.inputs.outputEntity,
                            outputComponent=db.inputs.outputComponent,
                            poseFrame=db.inputs.poseFrame,
                            stereoOffset=db.inputs.stereoOffset,
                        )

                    else:
                        carb.log_error("type is not supported")
                        db.internal_state.initialized = False
                        return False

                    if writer is not None:
                        db.internal_state.append_writer(writer)

                    db.internal_state.attach_writers(render_product_path)
                    return True
                except Exception as e:
                    print(traceback.format_exc())
                    pass
        else:
            if db.internal_state.graph:
                pass
            return True

    @staticmethod
    def release(node):
        try:
            state = OgnGXFCameraHelperInternalState.per_node_internal_state(node)
        except Exception:
            state = None
            pass

        if state is not None:
            state.reset()
