# Copyright (c) 2018-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.ext
import omni.kit.commands
import gc
from .. import _sensor
import carb
from .menu import IsaacSensorMenu
from omni.syntheticdata import sensors
from omni.isaac.core.utils.stage import get_current_stage, traverse_stage


EXTENSION_NAME = "Isaac Sensor"


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._cs = _sensor.acquire_contact_sensor_interface()
        self._is = _sensor.acquire_imu_sensor_interface()
        self._menu = IsaacSensorMenu()

        self.registered_template = []
        try:
            self.register_nodes()
        except Exception as e:
            carb.log_warn(f"Could not register node templates {e}")

        def _on_pre_load_file(event):
            # Rename all nodes from omni.isaac.isaac_sensor to omni.isaac.sensor
            stage = get_current_stage()
            if event.type == int(omni.usd.StageEventType.OPENED):
                for prim in traverse_stage():
                    if prim.HasAttribute("node:type"):
                        type_attr = prim.GetAttribute("node:type")
                        value = type_attr.Get()
                        if "omni.isaac.isaac_sensor" in value:
                            carb.log_warn(
                                f"Updating node type from omni.isaac.isaac_sensor to omni.isaac.sensor for {str(prim.GetPath())}. Please save and reload the asset, The omni.isaac.isaac_sensor extension was renamed to omni.isaac.sensor "
                            )
                            value = value.replace("omni.isaac.isaac_sensor", "omni.isaac.sensor")
                            type_attr.Set(value)

        self._on_stage_load_sub = (
            omni.usd.get_context().get_stage_event_stream().create_subscription_to_pop(_on_pre_load_file)
        )

    def on_shutdown(self):
        _sensor.release_contact_sensor_interface(self._cs)
        _sensor.release_imu_sensor_interface(self._is)

        try:
            self.unregister_nodes()
        except Exception as e:
            carb.log_warn(f"Could not unregister node templates {e}")

        self._menu.shutdown()
        self._menu = None
        self._on_stage_load_sub = None
        gc.collect()

    def register_nodes(self):

        ### Add render var to omni.syntheticdata
        omni.syntheticdata.SyntheticData._ogn_rendervars[
            "RtxSensorCpu"
        ] = omni.syntheticdata.SyntheticData._rendererTemplateName

        ### Add template to export raw data.
        template_name = "RtxSensorCpu" + "ExportRaw"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,
                    "omni.isaac.sensor.IsaacRenderVarToCpuPointer",
                    [
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate("RtxSensorCpu", (0,), None),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate("PostProcessDispatch"),
                    ],
                    {"inputs:renderVar": "RtxSensorCpu"},
                ),
                template_name=template_name,
            )
            self.registered_template.append(template)

        ### Add sync gate
        template_name = "RtxSensorCpu" + "IsaacSimulationGate"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,
                    "omni.isaac.core_nodes.IsaacSimulationGate",
                    [
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "RtxSensorCpu" + "ExportRaw", attributes_mapping={"outputs:exec": "inputs:execIn"}
                        )
                    ],
                ),
                template_name=template_name,
            )
            self.registered_template.append(template)

        ### RtxLidar Point Cloud
        template_name = "RtxSensorCpu" + "IsaacReadRTXLidarPointCloud"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,
                    "omni.isaac.sensor.IsaacReadRTXLidarPointCloud",
                    [
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "RtxSensorCpu" + "ExportRaw", attributes_mapping={"outputs:cpuPointer": "inputs:cpuPointer"}
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "RtxSensorCpu" + "IsaacSimulationGate",
                            attributes_mapping={"outputs:execOut": "inputs:execIn"},
                        ),
                    ],
                    # {
                    #    "inputs:accuracyErrorAzimuthDeg": 0.00001,
                    #    "inputs:accuracyErrorElevationDeg": 0.00001,
                    #    "inputs:accuracyErrorPosition": [-0.0001, 0.0001, 0.0001]
                    # }
                ),
                template_name=template_name,
            )
            self.registered_template.append(template)

        ### RtxLidar Flat Scan
        template_name = "RtxSensorCpu" + "IsaacReadRTXLidarFlatScan"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,
                    "omni.isaac.sensor.IsaacReadRTXLidarFlatScan",
                    [
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "RtxSensorCpu" + "ExportRaw", attributes_mapping={"outputs:cpuPointer": "inputs:cpuPointer"}
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "RtxSensorCpu" + "IsaacSimulationGate",
                            attributes_mapping={"outputs:execOut": "inputs:execIn"},
                        ),
                    ],
                ),
                template_name=template_name,
            )
            self.registered_template.append(template)

        # RTX lidar Debug Draw
        template_name = "RtxSensorCpu" + "DebugDrawPointCloud"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,
                    "omni.isaac.debug_draw.DebugDrawPointCloud",
                    [
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "RtxSensorCpu" + "IsaacReadRTXLidarPointCloud",
                            attributes_mapping={
                                "outputs:pointCloudData": "inputs:pointCloudData",
                                "outputs:execOut": "inputs:execIn",
                                "outputs:toWorldMatrix": "inputs:transform",
                            },
                        )
                    ],
                ),
                template_name=template_name,
            )
            self.registered_template.append(template)

    def unregister_nodes(self):
        for template in self.registered_template:
            sensors.get_synthetic_data().unregister_node_template(template)
