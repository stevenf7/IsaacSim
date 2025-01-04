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

        carter_name = "Carter"
        get_browser_instance().register_example(
            name=carter_name,
            execute_entrypoint=self.build_window,
            ui_hook=lambda a=weakref.proxy(self): a.build_ui(
                carter_name, "/Isaac/Samples/ROS/Scenario/carter_warehouse_navigation.usd"
            ),
            category="ROS/Navigation",
        )

        april_tag_name = "April Tag"
        get_browser_instance().register_example(
            name=april_tag_name,
            execute_entrypoint=self.build_window,
            ui_hook=lambda a=weakref.proxy(self): a.build_ui(
                april_tag_name, "/Isaac/Samples/ROS/Scenario/april_tag.usd"
            ),
            category="ROS",
        )

        teleport_name = "Teleport"
        get_browser_instance().register_example(
            name=teleport_name,
            execute_entrypoint=self.build_window,
            ui_hook=lambda a=weakref.proxy(self): a.build_ui(teleport_name, "/Isaac/Samples/ROS/Scenario/teleport.usd"),
            category="ROS",
        )

        hospital_scene_name = "Hospital Scene"
        get_browser_instance().register_example(
            name=hospital_scene_name,
            execute_entrypoint=self.build_window,
            ui_hook=lambda a=weakref.proxy(self): a.build_ui(
                hospital_scene_name, "/Isaac/Samples/ROS/Scenario/multiple_robot_carter_hospital_navigation.usd"
            ),
            category="ROS/Navigation/Multiple Robots",
        )

        office_scene_name = "Office Scene"
        get_browser_instance().register_example(
            name=office_scene_name,
            execute_entrypoint=self.build_window,
            ui_hook=lambda a=weakref.proxy(self): a.build_ui(
                office_scene_name, "/Isaac/Samples/ROS/Scenario/multiple_robot_carter_office_navigation.usd"
            ),
            category="ROS/Navigation/Multiple Robots",
        )

    def build_window(self):
        pass

    def build_ui(self, name, stage_path):
        # check if ros bridge is enabled before proceeding
        extension_enabled = omni.kit.app.get_app().get_extension_manager().is_extension_enabled("isaacsim.ros1.bridge")
        if not extension_enabled:
            msg = "ROS1 Bridge is not enabled. Please enable the extension to use this feature."
            carb.log_error(msg)
        else:
            overview = "This sample demonstrates how to use ROS1 Navigation packages with Isaac Sim. \n\n The Environment Loaded already contains the OmniGraphs needed to connect with ROS."
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
        get_browser_instance().deregister_example(name="Carter", category="ROS")
        get_browser_instance().deregister_example(name="Teleport", category="ROS")
        get_browser_instance().deregister_example(name="April Tag", category="ROS")
        get_browser_instance().deregister_example(name="Hospital Scene", category="ROS")
        get_browser_instance().deregister_example(name="Office Scene", category="ROS")
