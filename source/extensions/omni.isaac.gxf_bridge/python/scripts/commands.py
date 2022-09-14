# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.kit.commands
import omni.kit.utils
from omni.isaac.gxf_bridge import _gxf_bridge


def setup_publisher(prim, component: str, channel: str):
    prim.CreateOutputComponentAttr(component)
    prim.CreateOutputChannelAttr(channel)


def setup_receiver(prim, component: str, channel: str):
    prim.CreateInputComponentAttr(component)
    prim.CreateInputChannelAttr(channel)


class RobotEngineBridgeGxfTickComponent(omni.kit.commands.Command):
    def __init__(self, path: str):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._re_bridge = _gxf_bridge.acquire_gxf_bridge_interface()
        pass

    def do(self):
        return self._re_bridge.tick_component(self._path)

    def undo(self):
        # undo must be defined even if empty
        pass


class RobotEngineBridgeGxfCreateApplication(omni.kit.commands.Command):
    def __init__(self, base_path: str, manifest_file: str, graph_files: []):
        self._base_path = base_path
        self._manifest_file = manifest_file
        self._graph_files = graph_files
        self._gxf_bridge = _gxf_bridge.acquire_gxf_bridge_interface()
        pass

    def do(self) -> bool:

        return self._gxf_bridge.create_default_context(self._base_path, self._manifest_file, self._graph_files)

    def undo(self):
        pass


class RobotEngineBridgeGxfDestroyApplication(omni.kit.commands.Command):
    def __init__(self):
        self._gxf_bridge = _gxf_bridge.acquire_gxf_bridge_interface()
        pass

    def do(self) -> bool:
        return self._gxf_bridge.destroy_default_context()

    def undo(self):
        pass


omni.kit.commands.register_all_commands_in_module(__name__)
