import os
import carb
import omni.ext
import omni.ui
import omni.kit.menu
import weakref
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription

from .. import _robot_engine_bridge
from .menu import RobotEngineBridgeMenu


EXTENSION_NAME = "Robot Engine Bridge"


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._re_bridge = _robot_engine_bridge.acquire_robot_engine_bridge_interface()

        self._settings = carb.settings.get_settings()
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        self._reb_extension_path = ext_manager.get_extension_path(ext_id)

        json_path_input = self._settings.get("/isaac/robot_engine_bridge/json")

        # The default app json is copied to the resources folder as part of the build process
        # exec_folder resolves automatically to the folder containing the kit binary
        json_path = self._reb_extension_path + "/resources/isaac_engine/json/isaacsim.app.json"

        if json_path_input is not None:
            json_path = json_path_input

        self._window = omni.ui.Window(
            EXTENSION_NAME, width=600, height=400, visible=True, dockPreference=omni.ui.DockPreference.LEFT_BOTTOM
        )
        self._window.deferred_dock_in("Console", omni.ui.DockPolicy.DO_NOTHING)
        self._window.dock_order = 3

        self._menu_items = [
            MenuItemDescription(
                name="Isaac",
                sub_menu=[
                    MenuItemDescription(
                        name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback()
                    )
                ],
            )
        ]
        add_menu_items(self._menu_items, "Window")

        self._scene_loader = {}
        with self._window.frame:
            with omni.ui.VStack(style={"margin": 1}):
                with omni.ui.CollapsableFrame("Isaac SDK Bridge", height=0):
                    with omni.ui.VStack(height=0):
                        with omni.ui.CollapsableFrame("Scene Loader Settings", height=0, collapsed=True):
                            with omni.ui.VStack(height=0):
                                with omni.ui.HStack():
                                    omni.ui.Label("Input Component")
                                    self._scene_loader["input_component"] = omni.ui.StringField().model
                                    self._scene_loader["input_component"].set_value("input")
                                    self._scene_loader["input_component"].add_end_edit_fn(self._on_init_stage_load_fn)
                                with omni.ui.HStack():
                                    omni.ui.Label("Request Channel")
                                    self._scene_loader["request_channel"] = omni.ui.StringField().model
                                    self._scene_loader["request_channel"].set_value("scenario_control")
                                    self._scene_loader["request_channel"].add_end_edit_fn(self._on_init_stage_load_fn)
                                with omni.ui.HStack():
                                    omni.ui.Label("Camera Control")
                                    self._scene_loader["camera_control"] = omni.ui.StringField().model
                                    self._scene_loader["camera_control"].set_value("camera_switch")
                                    self._scene_loader["camera_control"].add_end_edit_fn(self._on_init_stage_load_fn)
                                with omni.ui.HStack():
                                    omni.ui.Label("Output Component")
                                    self._scene_loader["output_component"] = omni.ui.StringField().model
                                    self._scene_loader["output_component"].set_value("output")
                                    self._scene_loader["output_component"].add_end_edit_fn(self._on_init_stage_load_fn)
                                with omni.ui.HStack():
                                    omni.ui.Label("Reply Channel")
                                    self._scene_loader["reply_channel"] = omni.ui.StringField().model
                                    self._scene_loader["reply_channel"].set_value("scenario_reply")
                                    self._scene_loader["reply_channel"].add_end_edit_fn(self._on_init_stage_load_fn)
                        with omni.ui.VStack(
                            height=0,
                            tooltip='Can specify with: --carb/isaac/robot_engine_bridge/json="path/to/app.json" \n Or by entering in this text box',
                        ):
                            omni.ui.Label("Application JSON Path: ")
                            self._scene_loader["json_path"] = omni.ui.StringField().model
                            self._scene_loader["json_path"].set_value(json_path)
                            self._scene_loader["create_sdk"] = omni.ui.Button(
                                "Create Application", height=0, clicked_fn=self._on_create_destroy_sdk_app_fn
                            )
                with omni.ui.CollapsableFrame("GXF Bridge", height=0, collapsed=False):
                    with omni.ui.VStack(height=0):
                        # with omni.ui.HStack():
                        #     omni.ui.Label("Manifest Path ")
                        #     self._scene_loader["gxf_manifest"] = omni.ui.StringField().model
                        #     self._scene_loader["gxf_manifest"].set_value(
                        #         "manifest.yaml"
                        #     )
                        with omni.ui.HStack():
                            omni.ui.Label("Graph Path ", width=0)
                            self._scene_loader["gxf_graph"] = omni.ui.StringField().model
                            self._scene_loader["gxf_graph"].set_value(
                                self._reb_extension_path + "/data/config/visualize_uss.yaml"
                            )
                        self._scene_loader["create_gxf"] = omni.ui.Button(
                            "Create Application", height=0, clicked_fn=self._on_create_destroy_gxf_app_fn
                        )

        self._menu = RobotEngineBridgeMenu()
        self._is_created = False
        self._is_gxf_created = False

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    def on_shutdown(self):
        self._menu.shutdown()
        self._menu = None
        remove_menu_items(self._menu_items, "Window")
        _robot_engine_bridge.release_robot_engine_bridge_interface(self._re_bridge)

    def _on_init_stage_load_fn(self, widget):
        self._re_bridge.initialize_stage_loader(
            self._scene_loader["input_component"].get_value_as_string(),
            self._scene_loader["request_channel"].get_value_as_string(),
            self._scene_loader["camera_control"].get_value_as_string(),
            self._scene_loader["output_component"].get_value_as_string(),
            self._scene_loader["reply_channel"].get_value_as_string(),
        )

    def _on_create_destroy_sdk_app_fn(self):
        if self._is_created is False:
            self._re_bridge.create_application(
                self._reb_extension_path, self._scene_loader["json_path"].get_value_as_string(), [], []
            )
            self._re_bridge.initialize_stage_loader(
                self._scene_loader["input_component"].get_value_as_string(),
                self._scene_loader["request_channel"].get_value_as_string(),
                self._scene_loader["camera_control"].get_value_as_string(),
                self._scene_loader["output_component"].get_value_as_string(),
                self._scene_loader["reply_channel"].get_value_as_string(),
            )
            self._is_created = True
            self._scene_loader["create_sdk"].text = "Destroy Application"
        else:
            self._re_bridge.destroy_application()
            self._is_created = False
            self._scene_loader["create_sdk"].text = "Create Application"

    def _on_create_destroy_gxf_app_fn(self):
        if self._is_gxf_created is False:

            self._re_bridge.create_gxf_application(
                self._reb_extension_path + "/gxf/lib",
                "manifest.yaml",
                # self._scene_loader["gxf_manifest"].get_value_as_string(),
                [
                    self._reb_extension_path + "/data/config/isaac_sim_allocator.yaml",
                    self._scene_loader["gxf_graph"].get_value_as_string(),
                ],
            )
            self._is_gxf_created = True
            self._scene_loader["create_gxf"].text = "Destroy Application"
        else:
            self._re_bridge.destroy_gxf_application()
            self._is_gxf_created = False
            self._scene_loader["create_gxf"].text = "Create Application"
