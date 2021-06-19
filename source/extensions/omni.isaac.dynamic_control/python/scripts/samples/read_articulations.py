# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import os
import asyncio
import weakref
import textwrap
import carb
import omni
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription

from omni.isaac.dynamic_control import _dynamic_control
from pxr import Usd

import omni.physx as _physx
import omni.kit.menu

EXTENSION_NAME = "Read Articulations"


def get_data_file(file_name: str):
    if os.path.isabs(file_name):
        path_to_file = file_name
    else:
        path_to_file = os.path.abspath(
            os.path.join(carb.tokens.get_tokens_interface().resolve("${app}"), "..", "data", "usd", file_name)
        )
    return path_to_file


async def load_test_file(test_file_name: str):
    """
    Load the contents of the USD test file onto the stage, synchronously, when called as "await load_test_file(X)".
    In a testing environment we need to run one test at a time since there is no guarantee
    that tests can run concurrently, especially when loading files. This method encapsulates
    the logic necessary to load a test file using the open_stage_async method and then wait
    for it to complete before returning.
    :param test_file_name: Name of the test file to load - if not an absolute path then looks in the data/usd/tests/ComputeGraph directory
    :raises: ValueError if the test file is not a valid USD file
    """
    if not Usd.Stage.IsSupportedFile(test_file_name):
        raise ValueError("Only USD files can be loaded with this method")

    path_to_file = get_data_file(test_file_name)

    usd_context = omni.usd.get_context()
    usd_context.disable_save_to_recent_files()
    (result, error) = await omni.usd.get_context().open_stage_async(path_to_file)
    usd_context.enable_save_to_recent_files()
    return (result, error)


def _print_body_rec(dc, body, indent_level=0):
    indent = " " * indent_level

    body_name = dc.get_rigid_body_name(body)
    str_output = "%sBody: %s\n" % (indent, body_name)

    for i in range(dc.get_rigid_body_child_joint_count(body)):
        joint = dc.get_rigid_body_child_joint(body, i)
        joint_name = dc.get_joint_name(joint)
        child = dc.get_joint_child_body(joint)
        child_name = dc.get_rigid_body_name(child)
        str_output = str_output + "%s  Joint: %s -> %s\n" % (indent, joint_name, child_name)
        str_output = str_output + _print_body_rec(dc, child, indent_level + 4)
    return str_output


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._dc = _dynamic_control.acquire_dynamic_control_interface()
        self._window = None
        self._physxIFace = _physx.acquire_physx_interface()

        self._timeline = omni.timeline.get_timeline_interface()

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        self._extension_path = ext_manager.get_extension_path(ext_id)
        menu_items = [
            MenuItemDescription(name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
        ]
        self._menu_items = [
            MenuItemDescription(
                name="Controlling", sub_menu=[MenuItemDescription(name="Dynamic Control", sub_menu=menu_items)]
            )
        ]
        add_menu_items(self._menu_items, "Isaac Examples")

    def _menu_callback(self):
        self._build_ui()

    def _build_ui(self):
        if not self._window:
            self._window = ui.Window(
                title=EXTENSION_NAME, width=500, height=450, visible=True, dockPreference=ui.DockPreference.LEFT_BOTTOM
            )
            with self._window.frame:
                with ui.VStack(width=ui.Percent(100)):
                    ui.Label(
                        textwrap.fill(
                            "This sample demonstrates how to load a USD stage containing an articulated robot and then retreiving that articulation and using the dynamic_control python API to query it",
                            80,
                        ),
                        height=20,
                    )
                    with ui.HStack(height=0):
                        ui.Button(
                            "Load Franka USD",
                            tooltip="Press to load the Franka USD file and start simulation",
                            clicked_fn=lambda: self._on_load_robot(),
                        )
                        ui.Button(
                            "Get Articulation Info",
                            tooltip="Pressing this button will print information below",
                            clicked_fn=lambda: self._on_print_info(),
                        )

                    ui.Separator(height=3)
                    with ui.ScrollingFrame():
                        with ui.VStack():
                            with ui.CollapsableFrame("Hierarchy", height=ui.Pixel(0), collapsed=False):
                                with ui.ScrollingFrame(height=ui.Pixel(200)):
                                    self.hierarchy_label = ui.Label("")
                            with ui.CollapsableFrame("Body States", height=ui.Pixel(0), collapsed=True):
                                with ui.ScrollingFrame(height=ui.Pixel(150)):
                                    self.body_states_label = ui.Label("")
                            with ui.CollapsableFrame(
                                "Degree of freedom (DOF) States", height=ui.Pixel(0), collapsed=True
                            ):
                                with ui.ScrollingFrame(height=ui.Pixel(100)):
                                    self.dof_states_label = ui.Label("")
                            with ui.CollapsableFrame(
                                "Degree of freedom (DOF) Properties", height=ui.Pixel(0), collapsed=True
                            ):
                                with ui.ScrollingFrame(height=ui.Pixel(130)):
                                    self.dof_props_label = ui.Label("")

        self._window.visible = True

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Isaac Examples")
        self._window = None

    async def _setup_camera(self, task):
        # wait for the stage load task to finish before setting camera and starting simulation
        done, pending = await asyncio.wait({task})
        if task in done:
            self._viewport = omni.kit.viewport.get_default_viewport_window()
            self._viewport.set_camera_position("/OmniverseKit_Persp", 150, 150, 50, True)
            self._viewport.set_camera_target("/OmniverseKit_Persp", 0, 0, 50, True)
            self._timeline.play()

    def _on_load_robot(self):
        task = asyncio.ensure_future(load_test_file(self._extension_path + "/data/usd/robots/franka/franka.usd"))
        asyncio.ensure_future(self._setup_camera(task))

    def _on_print_info(self):
        self._physxIFace.force_load_physics_from_usd()

        ar = self._dc.get_articulation("/panda")
        if ar == _dynamic_control.INVALID_HANDLE:
            print("*** '%s' is not an articulation" % "/panda")
            return

        root = self._dc.get_articulation_root_body(ar)
        self.hierarchy_label.text = str("Articulation handle %d \n" % ar) + _print_body_rec(self._dc, root)

        body_states = self._dc.get_articulation_body_states(ar, _dynamic_control.STATE_ALL)
        self.body_states_label.text = str(body_states) + "\n"

        dof_states = self._dc.get_articulation_dof_states(ar, _dynamic_control.STATE_ALL)
        self.dof_states_label.text = str(dof_states) + "\n"

        dof_props = self._dc.get_articulation_dof_properties(ar)
        self.dof_props_label.text = str(dof_props) + "\n"

        return
