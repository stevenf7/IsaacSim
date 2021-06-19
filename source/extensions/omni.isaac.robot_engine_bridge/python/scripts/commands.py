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
import omni.isaac.RobotEngineBridgeSchema as REBSchema
import carb
from omni.isaac.robot_engine_bridge import _robot_engine_bridge
from pxr import Gf


def get_path(stage, path: str, parent=None) -> str:
    if parent:
        path = omni.usd.get_stage_next_free_path(stage, parent + path, False)
    else:
        path = omni.usd.get_stage_next_free_path(stage, path, True)
    return path


def setup_publisher(prim, component: str, channel: str):
    prim.CreateOutputComponentAttr(component)
    prim.CreateOutputChannelAttr(channel)


def setup_receiver(prim, component: str, channel: str):
    prim.CreateInputComponentAttr(component)
    prim.CreateInputChannelAttr(channel)


class RobotEngineBridgeCreateApplication(omni.kit.commands.Command):
    def __init__(self, asset_path: str, app_file: str, module_paths: list = [], json_files: list = []):
        self._asset_path = asset_path
        self._app_file = app_file
        self._module_paths = module_paths
        self._json_files = json_files
        self._re_bridge = _robot_engine_bridge.acquire_robot_engine_bridge_interface()
        pass

    def do(self) -> bool:

        return self._re_bridge.create_application(
            self._asset_path, self._app_file, self._module_paths, self._json_files
        )

    def undo(self):
        pass


class RobotEngineBridgeDestroyApplication(omni.kit.commands.Command):
    def __init__(self):
        self._re_bridge = _robot_engine_bridge.acquire_robot_engine_bridge_interface()
        pass

    def do(self) -> bool:
        return self._re_bridge.destroy_application()

    def undo(self):
        pass


class RobotEngineBridgeInitStageLoader(omni.kit.commands.Command):
    def __init__(
        self, input_component: str, request_channel: str, camera_control: str, output_component: str, reply_channel: str
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._re_bridge = _robot_engine_bridge.acquire_robot_engine_bridge_interface()
        pass

    def do(self) -> bool:
        self._re_bridge.initialize_stage_loader(
            self._input_component,
            self._request_channel,
            self._camera_control,
            self._output_component,
            self._reply_channel,
        )
        return True

    def undo(self):
        pass


class RobotEngineBridgeTickComponent(omni.kit.commands.Command):
    def __init__(self, path: str):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._re_bridge = _robot_engine_bridge.acquire_robot_engine_bridge_interface()
        pass

    def do(self):
        return self._re_bridge.tick_component(self._path)

    def undo(self):
        # undo must be defined even if empty
        pass


omni.kit.commands.register_all_commands_in_module(__name__)
