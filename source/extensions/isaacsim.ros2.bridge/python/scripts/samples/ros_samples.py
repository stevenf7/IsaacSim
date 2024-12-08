# Copyright (c) 2018-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


import asyncio
import os
import weakref

import carb
import omni.ext
import omni.ui as ui
import omni.usd
from isaacsim.examples.browser import get_instance as get_browser_instance
from isaacsim.gui.components.ui_utils import setup_ui_headers
from isaacsim.storage.native import get_assets_root_path


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._ext_id = ext_id

        name = "Carter"
        get_browser_instance().register_example(
            name=name,
            execute_entrypoint=self.build_window,
            ui_hook=lambda a=weakref.proxy(self): a.build_ui(
                name, "/Isaac/Samples/ROS2/Scenario/carter_warehouse_navigation.usd"
            ),
            category="ROS2/Navigation",
        )

        name = "iw_hub"
        get_browser_instance().register_example(
            name=name,
            execute_entrypoint=self.build_window,
            ui_hook=lambda a=weakref.proxy(self): a.build_ui(
                name, "/Isaac/Samples/ROS2/Scenario/iw_hub_warehouse_navigation.usd"
            ),
            category="ROS2/Navigation",
        )

        name = "Sample Scene"
        get_browser_instance().register_example(
            name=name,
            execute_entrypoint=self.build_window,
            ui_hook=lambda a=weakref.proxy(self): a.build_ui(
                name, "/Isaac/Samples/ROS2/Scenario/carter_warehouse_apriltag_worker.usd"
            ),
            category="ROS2/Isaac ROS",
        )

        name = "Perceptor Scene"
        get_browser_instance().register_example(
            name=name,
            execute_entrypoint=self.build_window,
            ui_hook=lambda a=weakref.proxy(self): a.build_ui(
                name, "/Isaac/Samples/ROS2/Scenario/perceptor_navigation.usd"
            ),
            category="ROS2/Isaac ROS",
        )

        name = "Hospital Scene"
        get_browser_instance().register_example(
            name=name,
            execute_entrypoint=self.build_window,
            ui_hook=lambda a=weakref.proxy(self): a.build_ui(
                name, "/Isaac/Samples/ROS2/Scenario/multiple_robot_carter_hospital_navigation.usd"
            ),
            category="ROS2/Navigation/Multiple Robots",
        )

        name = "Office Scene"
        get_browser_instance().register_example(
            name=name,
            execute_entrypoint=self.build_window,
            ui_hook=lambda a=weakref.proxy(self): a.build_ui(
                name, "/Isaac/Samples/ROS2/Scenario/multiple_robot_carter_office_navigation.usd"
            ),
            category="ROS2/Navigation/Multiple Robots",
        )

    def build_window(self):
        pass

    def build_ui(self, name, file_path):

        # check if ros2 bridge is enabled before proceeding
        extension_enabled = omni.kit.app.get_app().get_extension_manager().is_extension_enabled("isaacsim.ros2.bridge")
        if not extension_enabled:
            msg = "ROS2 Bridge is not enabled. Please enable the extension to use this feature."
            carb.log_error(msg)
        else:
            overview = "This sample demonstrates how to use ROS2 Navigation packages with Isaac Sim. \n\n The Environment Loaded already contains the OmniGraphs needed to connect with ROS2."
            self._main_stack = ui.VStack(spacing=5, height=0)
            with self._main_stack:
                setup_ui_headers(
                    self._ext_id,
                    file_path=os.path.abspath(__file__),
                    title=name,
                    overview=overview,
                    info_collapsed=False,
                )
                ui.Button(
                    "Load Sample Scene", clicked_fn=lambda a=weakref.proxy(self): a._on_environment_setup(file_path)
                )

    def _on_environment_setup(self, stage_path):
        async def load_stage(path):
            await omni.usd.get_context().open_stage_async(path)

        self._assets_root_path = get_assets_root_path()
        if self._assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return
        scenario_path = self._assets_root_path + stage_path

        asyncio.ensure_future(load_stage(scenario_path))

    def on_shutdown(self):
        get_browser_instance().deregister_example(name="Carter Navigation", category="ROS2")
        get_browser_instance().deregister_example(name="iw_hub Navigation", category="ROS2")
        get_browser_instance().deregister_example(name="Sample Scene", category="Isaac ROS")
        get_browser_instance().deregister_example(name="Perceptor Scene", category="Isaac ROS")
        get_browser_instance().deregister_example(name="Hospital Scene (Multiple Robot Navigation)", category="ROS2")
        get_browser_instance().deregister_example(name="Office Scene (Multiple Robot Navigation)", category="ROS2")
