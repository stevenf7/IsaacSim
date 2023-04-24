# Copyright (c) 2018-2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import asyncio
import os
import weakref

import carb
import omni.ext
import omni.kit.menu
import omni.syntheticdata._syntheticdata as sd
import omni.ui
from omni.isaac.ui.menu import make_menu_item_description
from omni.kit.menu.utils import MenuItemDescription, add_menu_items, remove_menu_items
from omni.syntheticdata import sensors

from .. import _gxf_bridge

EXTENSION_NAME = "GXF Bridge"


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._settings = carb.settings.get_settings()
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        self._reb_extension_path = ext_manager.get_extension_path(ext_id)

        self._window = omni.ui.Window(
            EXTENSION_NAME, width=600, height=400, visible=True, dockPreference=omni.ui.DockPreference.LEFT_BOTTOM
        )
        self._window.deferred_dock_in("Console", omni.ui.DockPolicy.DO_NOTHING)
        self._window.dock_order = 3

        self._menu_items = [
            make_menu_item_description(ext_id, EXTENSION_NAME, lambda a=weakref.proxy(self): a._menu_callback())
        ]
        add_menu_items(self._menu_items, "Isaac Utils")

        self._scene_loader = {}
        with self._window.frame:
            with omni.ui.VStack(style={"margin": 1}):
                with omni.ui.CollapsableFrame("GXF Bridge", height=0, collapsed=False):
                    with omni.ui.VStack(height=0):
                        with omni.ui.HStack():
                            omni.ui.Label("Graph Path ", width=0)
                            self._scene_loader["gxf_graph"] = omni.ui.StringField().model
                            self._scene_loader["gxf_graph"].set_value(
                                self._reb_extension_path + "/data/config/tcp_server.yaml"
                            )
                        self._scene_loader["create_gxf"] = omni.ui.Button(
                            "Create Application", height=0, clicked_fn=self._on_create_destroy_gxf_app_fn
                        )

        self._is_gxf_created = False
        self.registered_template = []
        self._gxf_bridge = _gxf_bridge.acquire_gxf_bridge_interface()
        self.register_nodes()

        try:
            import omni.graph.ui as ogu

            ogu.ComputeNodeWidget.get_instance().add_template_path(__file__)
        except ImportError:
            pass

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    def on_shutdown(self):
        async def safe_shutdown(bridge):
            omni.timeline.get_timeline_interface().stop()
            await omni.kit.app.get_app().next_update_async()
            if bridge is not None:
                _gxf_bridge.release_gxf_bridge_interface(bridge)

        asyncio.ensure_future(safe_shutdown(self._gxf_bridge))
        self.unregister_nodes()
        remove_menu_items(self._menu_items, "Isaac Utils")

    def _on_create_destroy_gxf_app_fn(self):
        if self._is_gxf_created is False:

            result, status = omni.kit.commands.execute(
                "RobotEngineBridgeGxfCreateApplication",
                base_path=self._reb_extension_path + "/lib",
                manifest_file="manifest.yaml",
                graph_files=[
                    self._scene_loader["gxf_graph"].get_value_as_string(),
                    self._reb_extension_path + "/data/config/isaac_sim_allocator.yaml",
                ],
            )

            self._is_gxf_created = True
            self._scene_loader["create_gxf"].text = "Destroy Application"
        else:
            omni.timeline.get_timeline_interface().stop()
            result, status = omni.kit.commands.execute("RobotEngineBridgeGxfDestroyApplication")

            self._is_gxf_created = False
            self._scene_loader["create_gxf"].text = "Create Application"

    def register_nodes(self):
        ##### Publish RGB
        rv = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(sd.SensorType.Rgb.name)
        template_name = rv + "GXFPublishImage"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,  # node template stage
                    "omni.isaac.gxf_bridge.GXFPublishImage",  # node template type
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
                            "IsaacReadCameraInfo",
                            attributes_mapping={
                                "outputs:focalLength": "inputs:focalLength",
                                "outputs:horizontalAperture": "inputs:horizontalAperture",
                                "outputs:verticalAperture": "inputs:verticalAperture",
                                "outputs:horizontalOffset": "inputs:horizontalOffset",
                                "outputs:verticalOffset": "inputs:verticalOffset",
                                "outputs:projectionType": "inputs:projectionType",
                                "outputs:cameraFisheyeParams": "inputs:cameraFisheyeParams",
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
        template_name = rv + "GXFPublishImage"
        if template_name not in sensors.get_synthetic_data()._ogn_templates_registry:
            template = sensors.get_synthetic_data().register_node_template(
                omni.syntheticdata.SyntheticData.NodeTemplate(
                    omni.syntheticdata.SyntheticDataStage.ON_DEMAND,  # node template stage
                    "omni.isaac.gxf_bridge.GXFPublishImage",  # node template type
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
                            "IsaacReadCameraInfo",
                            attributes_mapping={
                                "outputs:focalLength": "inputs:focalLength",
                                "outputs:horizontalAperture": "inputs:horizontalAperture",
                                "outputs:verticalAperture": "inputs:verticalAperture",
                                "outputs:horizontalOffset": "inputs:horizontalOffset",
                                "outputs:verticalOffset": "inputs:verticalOffset",
                                "outputs:projectionType": "inputs:projectionType",
                                "outputs:cameraFisheyeParams": "inputs:cameraFisheyeParams",
                            },
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            rv + "IsaacSimulationGate", attributes_mapping={"outputs:execOut": "inputs:execIn"}
                        ),
                        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                            "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                        ),
                    ],
                    attributes={"inputs:encoding": "f32"},
                ),
                template_name=template_name,
            )

            self.registered_template.append(template)

    def unregister_nodes(self):
        for template in self.registered_template:
            sensors.get_synthetic_data().unregister_node_template(template)
