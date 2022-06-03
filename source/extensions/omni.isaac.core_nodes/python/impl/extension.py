"""
Support required by the Carbonite extension loader
"""
import omni.ext

# Any class derived from `omni.ext.IExt` in a top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when the extension is enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() will be called.

from ..bindings._omni_isaac_core_nodes import acquire_interface, release_interface
import omni.syntheticdata._syntheticdata as sd
import omni.syntheticdata
from omni.syntheticdata import sensors
import omni.kit.commands
from omni.isaac.core.utils.stage import get_current_stage
from omni.isaac.core.utils.prims import get_prim_at_path
from pxr import Sdf


class Extension(omni.ext.IExt):
    def on_startup(self):
        self.__interface = acquire_interface()
        self.registered_template = []

        self.register_nodes()

        self._stage_event_sub = (
            omni.usd.get_context().get_stage_event_stream().create_subscription_to_pop(self._on_stage_event)
        )
        pass

    def on_shutdown(self):
        release_interface(self.__interface)
        self.__interface = None
        self.unregister_nodes()
        self._stage_event_sub = None
        pass

    def _on_stage_event(self, event):
        # Workaround for issue where an opened stage can contain a dirty /Render path
        if event.type == int(omni.usd.StageEventType.OPENED):
            stage = get_current_stage()
            path = "/Render"
            # delete any deltas on the root layer
            try:
                from omni.kit.widget.layers.layer_commands import RemovePrimSpecCommand

                RemovePrimSpecCommand(
                    layer_identifier=stage.GetRootLayer().realPath, prim_spec_path=[Sdf.Path(path)]
                ).do()
            except:
                pass
            # Make sure /Render is hidden
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
        template_name = "IsaacReadSimulationTime"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,
                    "omni.isaac.core_nodes.IsaacReadSimulationTime",
                    [
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "PostProcessDispatch",
                            attributes_mapping={"outputs:swhFrameNumber": "inputs:swhFrameNumber"},
                        )
                    ],
                ),
                template_name=template_name,
            )
            self.registered_template.append(template)

        ##### Simulation Gates
        for rv in sensors.get_synthetic_data()._ogn_rendervars:
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
        sensor_names = {
            "instance_segmentation": "InstanceSegmentation",
            "semantic_segmentation": "SemanticSegmentation",
            "bounding_box_2d_tight": "BoundingBox2DTight",
            "bounding_box_2d_loose": "BoundingBox2DLoose",
            "bounding_box_3d": "BoundingBox3D",
            "PostProcessDispatch": "PostProcessDispatch",
        }
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
