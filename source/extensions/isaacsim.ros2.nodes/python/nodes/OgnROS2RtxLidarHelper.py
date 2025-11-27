# SPDX-FileCopyrightText: Copyright (c) 2022-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
import traceback

import carb
import numpy as np
import omni
import omni.graph.core as og
import omni.isaac.IsaacSensorSchema as IsaacSensorSchema
import omni.replicator.core as rep
import omni.syntheticdata
from isaacsim.core.nodes import BaseWriterNode
from isaacsim.core.nodes.scripts.utils import (
    register_annotator_from_node_with_telemetry,
    register_node_writer_with_telemetry,
)
from isaacsim.core.utils.render_product import get_camera_prim_path
from isaacsim.ros2.core import collect_namespace
from pxr import Usd, UsdGeom


class OgnROS2RtxLidarHelperInternalState(BaseWriterNode):
    def __init__(self):
        self.viewport = None
        self.viewport_name = ""
        self.resetSimulationTimeOnStop = False
        self.publishStepSize = 1
        super().__init__(initialize=False)

    def post_attach(self, writer, render_product):
        try:

            omni.syntheticdata.SyntheticData.Get().set_node_attributes(
                "PostProcessDispatch" + "IsaacSimulationGate", {"inputs:step": self.publishStepSize}, render_product
            )

            omni.syntheticdata.SyntheticData.Get().set_node_attributes(
                "IsaacReadSimulationTime", {"inputs:resetOnStop": self.resetSimulationTimeOnStop}, render_product
            )

        except:
            pass


class OgnROS2RtxLidarHelper:
    @staticmethod
    def internal_state():
        return OgnROS2RtxLidarHelperInternalState()

    @staticmethod
    def compute(db) -> bool:
        if db.inputs.enabled is False:
            if db.per_instance_state.initialized is False:
                return True
            else:
                db.per_instance_state.custom_reset()
                return True

        if db.per_instance_state.initialized is False:
            db.per_instance_state.initialized = True
            stage = omni.usd.get_context().get_stage()
            keys = og.Controller.Keys
            with Usd.EditContext(stage, stage.GetSessionLayer()):
                render_product_path = db.inputs.renderProductPath
                if not render_product_path:
                    carb.log_warn("Render product not valid")
                    db.per_instance_state.initialized = False
                    return False
                if stage.GetPrimAtPath(render_product_path) is None:
                    # Invalid Render Product Path
                    carb.log_warn("Render product not created yet, retrying on next call")
                    db.per_instance_state.initialized = False
                    return False
                prim = stage.GetPrimAtPath(get_camera_prim_path(render_product_path))
                if not (prim.IsA(UsdGeom.Camera) and prim.HasAPI(IsaacSensorSchema.IsaacRtxLidarSensorAPI)) and not (
                    prim.GetTypeName() == "OmniLidar" and prim.HasAPI("OmniSensorGenericLidarCoreAPI")
                ):
                    carb.log_warn("Render product not attached to RTX Lidar (Camera or OmniLidar prims are required).")
                    db.per_instance_state.initialized = False
                    return False

                db.per_instance_state.render_product_path = render_product_path
                sensor_type = db.inputs.type
                db.per_instance_state.resetSimulationTimeOnStop = db.inputs.resetSimulationTimeOnStop

                db.per_instance_state.publishStepSize = db.inputs.frameSkipCount + 1

                writer = None

                time_type = ""
                if db.inputs.useSystemTime:
                    time_type = "SystemTime"
                    if db.inputs.resetSimulationTimeOnStop:
                        carb.log_warn("System timestamp is being used. Ignoring resetSimulationTimeOnStop input")

                try:
                    if sensor_type == "laser_scan":
                        if db.inputs.fullScan:
                            carb.log_warn("fullScan does not have an effect with the laser_scan setting")
                        writer = rep.writers.get("RtxLidar" + f"ROS2{time_type}PublishLaserScan")

                    elif sensor_type == "point_cloud":
                        # Dynamically name, build, and register a new Annotator based on the selected metadata if it doesn't exist yet
                        annotator_name = "IsaacCreateRTXLidarScanBuffer"
                        annotator_name += "PerFrame" if not db.inputs.fullScan else ""
                        annotator_name += "_".join(db.inputs.selectedMetadata)
                        if annotator_name not in rep.AnnotatorRegistry.get_registered_annotators():
                            init_params = {"enablePerFrameOutput": not db.inputs.fullScan}
                            for metadata in db.inputs.selectedMetadata:
                                init_params[f"output{metadata[0].upper()}{metadata[1:]}"] = True
                            register_annotator_from_node_with_telemetry(
                                name=annotator_name,
                                input_rendervars=[
                                    "GenericModelOutputPtr",
                                ],
                                node_type_id="isaacsim.sensors.rtx.IsaacCreateRTXLidarScanBuffer",
                                init_params=init_params,
                                output_data_type=np.float32,
                                output_channels=3,
                            )

                        # Dynamically name, build, and register a new Writer based on the selected metadata if it doesn't exist yet
                        writer_name = "RtxLidar" + f"ROS2{time_type}PublishPointCloud"
                        writer_name += "Buffer" if db.inputs.fullScan else ""
                        writer_name += "_".join(db.inputs.selectedMetadata)
                        if writer_name not in rep.WriterRegistry.get_writers():
                            time_node_type = "system" if db.inputs.useSystemTime else "simulation"
                            register_node_writer_with_telemetry(
                                name=writer_name,
                                node_type_id="isaacsim.ros2.bridge.ROS2PublishPointCloud",
                                annotators=[
                                    annotator_name,
                                    "PostProcessDispatchIsaacSimulationGate",
                                    omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                                        f"IsaacRead{time_node_type.capitalize()}Time",
                                        attributes_mapping={f"outputs:{time_node_type}Time": "inputs:timeStamp"},
                                    ),
                                ],
                                category="isaacsim.ros2.bridge",
                            )

                        writer = rep.writers.get(writer_name)

                        if "ObjectId" in db.inputs.selectedMetadata and db.inputs.enableObjectIdMap:
                            object_id_map_writer = rep.writers.get(f"ROS2{time_type}PublishObjectIdMap")
                            object_id_map_writer.initialize(
                                nodeNamespace=collect_namespace(db.inputs.nodeNamespace, render_product_path),
                                queueSize=db.inputs.queueSize,
                                topicName=db.inputs.objectIdMapTopicName,
                            )
                            db.per_instance_state.append_writer(object_id_map_writer)

                    else:
                        carb.log_error("type is not supported")
                        db.per_instance_state.initialized = False
                        return False
                    if writer is not None:
                        writer.initialize(
                            frameId=db.inputs.frameId,
                            nodeNamespace=collect_namespace(db.inputs.nodeNamespace, render_product_path),
                            queueSize=db.inputs.queueSize,
                            topicName=db.inputs.topicName,
                            context=db.inputs.context,
                            qosProfile=db.inputs.qosProfile,
                        )
                        db.per_instance_state.append_writer(writer)
                        if db.inputs.showDebugView:
                            # Disable transform for OmniLidar prims whose output frame of reference is WORLD
                            doTransform = not (
                                prim.GetTypeName() == "OmniLidar"
                                and prim.HasAttribute("omni:sensor:Core:outputFrameOfReference")
                                and prim.GetAttribute("omni:sensor:Core:outputFrameOfReference").Get() == "WORLD"
                            )
                            # Use the correct writer based on the fullScan input
                            writer = rep.writers.get(
                                "RtxLidarDebugDrawPointCloud" + ("Buffer" if db.inputs.fullScan else "")
                            )
                            writer.initialize(doTransform=doTransform)
                            db.per_instance_state.append_writer(writer)
                    db.per_instance_state.attach_writers(render_product_path)
                except Exception as e:
                    print(traceback.format_exc())
                    pass
        else:
            return True

    @staticmethod
    def release_instance(node, graph_instance_id):
        try:
            state = OgnROS2RtxLidarHelperInternalState.per_instance_internal_state(node)
        except Exception:
            state = None
            pass

        if state is not None:
            state.reset()
