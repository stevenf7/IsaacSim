# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import asyncio
import weakref

import carb
import omni.ext
import omni.kit.menu
import omni.replicator.core as rep
import omni.syntheticdata._syntheticdata as sd
import omni.ui
from omni.isaac.ui.menu import make_menu_item_description
from omni.kit.menu.utils import add_menu_items, remove_menu_items

from .. import _gxf_bridge

EXTENSION_NAME = "GXF Bridge"
BRIDGE_NAME = "omni.isaac.gxf_bridge"
BRIDGE_PREFIX = "GXF"


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._settings = carb.settings.get_settings()
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        self._gxf_extension_path = ext_manager.get_extension_path(ext_id)

        self._menu_items = [
            make_menu_item_description(ext_id, EXTENSION_NAME, lambda a=weakref.proxy(self): a._menu_callback())
        ]
        add_menu_items(self._menu_items, "Isaac Utils")

        self.registered_template = []
        self._gxf_bridge = _gxf_bridge.acquire_gxf_bridge_interface()
        self.register_nodes()

        try:
            import omni.graph.ui as ogu

            ogu.ComputeNodeWidget.get_instance().add_template_path(__file__)
        except ImportError:
            pass

    def on_shutdown(self):
        async def safe_shutdown(bridge):
            omni.timeline.get_timeline_interface().stop()
            await omni.kit.app.get_app().next_update_async()
            if bridge is not None:
                _gxf_bridge.release_gxf_bridge_interface(bridge)

        asyncio.ensure_future(safe_shutdown(self._gxf_bridge))
        self.unregister_nodes()
        remove_menu_items(self._menu_items, "Isaac Utils")

    def register_nodes(self):
        ##### Publish RGB
        rv = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(sd.SensorType.Rgb.name)
        rep.writers.register_node_writer(
            name=f"{rv}{BRIDGE_PREFIX}PublishImage",
            node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishImage",
            annotators=[
                f"{rv}IsaacConvertRGBAToRGB",
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
                        "outputs:physicalDistortionModel": "inputs:physicalDistortionModel",
                        "outputs:physicalDistortionCoefficients": "inputs:physicalDistortionCoefficients",
                    },
                ),
                omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                    "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                ),
                f"{rv}IsaacSimulationGate",
            ],
            category=BRIDGE_NAME,
        )

        ##### Publish Depth
        rv = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(sd.SensorType.DistanceToImagePlane.name)
        rep.writers.register_node_writer(
            name=f"{rv}{BRIDGE_PREFIX}PublishImage",
            node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishImage",
            annotators=[
                "distance_to_image_plane",
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
                        "outputs:physicalDistortionModel": "inputs:physicalDistortionModel",
                        "outputs:physicalDistortionCoefficients": "inputs:physicalDistortionCoefficients",
                    },
                ),
                omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                    "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                ),
                f"{rv}IsaacSimulationGate",
            ],
            encoding="f32",
            category=BRIDGE_NAME,
        )

        # RTX lidar Range Scan publisher
        rep.writers.register_node_writer(
            name=f"RtxLidar{BRIDGE_PREFIX}PublishRTXRangeScan",
            node_type_id=f"{BRIDGE_NAME}.{BRIDGE_PREFIX}PublishRTXRangeScan",
            annotators=[
                "RtxSensorCpu" + "IsaacReadRTXLidarData",
                "PostProcessDispatchIsaacSimulationGate",
                omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
                    "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
                ),
            ],
            category=BRIDGE_NAME,
        )

    def unregister_nodes(self):
        for writer in rep.WriterRegistry.get_writers(category=BRIDGE_NAME):
            rep.writers.unregister_writer(writer)
