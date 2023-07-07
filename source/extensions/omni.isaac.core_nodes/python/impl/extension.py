# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

"""
Support required by the Carbonite extension loader
"""
import copy

import carb
import omni.ext
import omni.kit.commands
import omni.replicator.core as rep
import omni.syntheticdata
import omni.syntheticdata._syntheticdata as sd
from omni.isaac.core.utils.prims import get_prim_at_path
from omni.isaac.core.utils.stage import get_current_stage
from omni.syntheticdata import sensors
from pxr import Sdf, Usd

from ..bindings._omni_isaac_core_nodes import acquire_interface, release_interface

# Any class derived from `omni.ext.IExt` in a top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when the extension is enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() will be called.


class Extension(omni.ext.IExt):
    def on_startup(self):
        self.__interface = acquire_interface()
        self.registered_template = []
        try:
            self.register_nodes()
        except Exception as e:
            carb.log_error(f"Could not register node templates {e}")

        self._stage_event_sub = (
            omni.usd.get_context()
            .get_stage_event_stream()
            .create_subscription_to_pop_by_type(int(omni.usd.StageEventType.OPENED), self._on_stage_open_event)
        )
        pass

    def on_shutdown(self):
        release_interface(self.__interface)
        self.__interface = None
        try:
            self.unregister_nodes()
        except Exception as e:
            carb.log_warn(f"Could not unregister node templates {e}")
        self._stage_event_sub = None
        pass

    def _on_stage_open_event(self, event):
        # Workaround for issue where an opened stage can contain a dirty /Render path
        stage = get_current_stage()
        path = "/Render"
        # delete any deltas on the root layer
        try:
            from omni.kit.widget.layers.layer_commands import RemovePrimSpecCommand

            RemovePrimSpecCommand(layer_identifier=stage.GetRootLayer().realPath, prim_spec_path=[Sdf.Path(path)]).do()
        except:
            pass
        # Make sure /Render is hidden
        if get_prim_at_path(path):
            get_prim_at_path(path).SetMetadata("hide_in_stage_window", True)

    def register_nodes(self):
        # need to set the viewport manually at runtime
        template_name = "IsaacReadCameraInfo"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND, "omni.isaac.core_nodes.IsaacReadCameraInfo"
                ),
                template_name=template_name,
            )
            self.registered_template.append(template)

        ##### Time
        # TODO105 : ASYNCRENDERING VALIDATION
        template_name = "IsaacReadTimesAOV"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.POST_RENDER,
                    "omni.isaac.core_nodes.IsaacReadTimes",
                    [
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            omni.syntheticdata.SyntheticData._rendererTemplateName,
                            attributes_mapping={
                                "outputs:rp": "inputs:renderResults",
                                "outputs:exec": "inputs:execIn",
                                "outputs:gpu": "inputs:gpu",
                            },
                        ),
                    ],
                ),
                template_name=template_name,
            )
            self.registered_template.append(template)

        template_name = "IsaacReadTimes"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,
                    "omni.isaac.core_nodes.IsaacReadTimes",
                    [
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "PostProcessDispatch",
                            attributes_mapping={
                                "outputs:renderResults": "inputs:renderResults",
                                "outputs:exec": "inputs:execIn",
                            },
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "IsaacReadTimesAOV",
                            attributes_mapping={
                                "outputs:execOut": "inputs:execIn",
                            },
                        ),
                    ],
                ),
                template_name=template_name,
            )
            self.registered_template.append(template)

        template_name = "IsaacReadSimulationTime"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,
                    "omni.isaac.core_nodes.IsaacReadSimulationTime",
                    [
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "IsaacReadTimes",
                            attributes_mapping={
                                "outputs:swhFrameNumber": "inputs:swhFrameNumber",
                            },
                        )
                    ],
                ),
                template_name=template_name,
            )
            self.registered_template.append(template)

        ##### Simulation Gates
        for rv in sensors.get_synthetic_data()._ogn_rendervars:
            if sensors.get_synthetic_data().is_node_template_registered(rv + "ExportRawArray"):
                template_name = rv + "IsaacSimulationGate"
                if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
                    template = sensors.get_synthetic_data().register_node_template(
                        omni.syntheticdata.SyntheticData.NodeTemplate(
                            omni.syntheticdata.SyntheticDataStage.ON_DEMAND,
                            "omni.isaac.core_nodes.IsaacSimulationGate",
                            [
                                omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                                    rv + "ExportRawArray", attributes_mapping={"outputs:exec": "inputs:execIn"}
                                )
                            ],
                        ),
                        template_name=template_name,
                    )
                    self.registered_template.append(template)
        # These gates connect to annotators
        # instance_segmentation = anotator name?
        # InstanceSegmentation = sensor type
        # InstanceSegmentationSD = rendervar
        sensor_names = {
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
            "PostProcessDispatch": "PostProcessDispatch",
        }
        # TODO105 why postProcessDispatch?
        for name in sensor_names.items():
            template_name = name[1] + "IsaacSimulationGate"
            if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
                template = sensors.get_synthetic_data().register_node_template(
                    omni.syntheticdata.SyntheticData.NodeTemplate(
                        omni.syntheticdata.SyntheticDataStage.ON_DEMAND,
                        "omni.isaac.core_nodes.IsaacSimulationGate",
                        [
                            omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                                name[0], attributes_mapping={"outputs:exec": "inputs:execIn"}
                            )
                        ],
                    ),
                    template_name=template_name,
                )
                self.registered_template.append(template)

        ##### RGBA to RGB
        rv = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(sd.SensorType.Rgb.name)
        template_name = rv + "IsaacConvertRGBAToRGB"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,  # node template stage
                    "omni.isaac.core_nodes.IsaacConvertRGBAToRGB",  # node template type
                    [
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(rv + "ExportRawArray"),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            rv + "IsaacSimulationGate", attributes_mapping={"outputs:execOut": "inputs:execIn"}
                        ),
                    ],
                    attributes={"inputs:encoding": "rgba8"},
                ),
                template_name=template_name,
            )
            self.registered_template.append(template)

        # convert depth to pcl
        rv = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(sd.SensorType.DistanceToImagePlane.name)
        template_name = rv + "IsaacConvertDepthToPointCloud"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,  # node template stage
                    "omni.isaac.core_nodes.IsaacConvertDepthToPointCloud",  # node template type
                    [
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            rv + "ExportRawArray",
                            attributes_mapping={
                                "outputs:data": "inputs:data",
                                "outputs:width": "inputs:width",
                                "outputs:height": "inputs:height",
                                "outputs:format": "inputs:format",
                            },
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "IsaacReadCameraInfo",
                            attributes_mapping={
                                "outputs:focalLength": "inputs:focalLength",
                                "outputs:horizontalAperture": "inputs:horizontalAperture",
                                "outputs:verticalAperture": "inputs:verticalAperture",
                            },
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            rv + "IsaacSimulationGate", attributes_mapping={"outputs:execOut": "inputs:execIn"}
                        ),
                    ],
                ),
                template_name=template_name,
            )
            self.registered_template.append(template)

    def unregister_nodes(self):
        for template in self.registered_template:
            sensors.get_synthetic_data().unregister_node_template(template)
