import carb
import omni
import omni.ui as ui
import omni.kit.test
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription

import asyncio
from omni.isaac.dynamic_control import _dynamic_control
from pxr import Usd
import os
import omni.physx as _physx
import numpy as np
import weakref

# joint animation states
ANIM_SEEK_LOWER = 1
ANIM_SEEK_UPPER = 2
ANIM_SEEK_DEFAULT = 3
ANIM_FINISHED = 4

EXTENSION_NAME = "Joint Monkey"


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


def clamp(x, min_value, max_value):
    return max(min(x, max_value), min_value)


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
    def on_startup(self, ext_id):
        self._dc = _dynamic_control.acquire_dynamic_control_interface()
        self._window = None
        self._physxIFace = _physx.acquire_physx_interface()
        self._physx_subscription = None
        self._timeline = omni.timeline.get_timeline_interface()
        self._viewport = omni.kit.viewport.get_default_viewport_window()
        self.ar = _dynamic_control.INVALID_HANDLE

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        self._extension_path = ext_manager.get_extension_path(ext_id)
        menu_items = [
            MenuItemDescription(name="Joint Controller", onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
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
                title=EXTENSION_NAME, width=300, height=200, visible=True, dockPreference=ui.DockPreference.LEFT_BOTTOM
            )
            with self._window.frame:
                with ui.VStack():
                    ui.Button("Load Robot", clicked_fn=self._on_load_robot)
                    ui.Button("Move Joints", clicked_fn=self._on_move_joints)

                    ui.Separator(height=3)
                    with ui.ScrollingFrame():
                        with ui.VStack():
                            self.dof_states_label = ui.Label("")
                            self.dof_props_label = ui.Label("")

    def on_shutdown(self):
        self._sub_stage_event = None
        self._physx_subscription = None
        remove_menu_items(self._menu_items, "Isaac Examples")
        self._window = None

    async def _setup_camera(self, task):
        done, pending = await asyncio.wait({task})
        if task in done:
            self._viewport.set_camera_position("/OmniverseKit_Persp", 150, -150, 150, True)
            self._viewport.set_camera_target("/OmniverseKit_Persp", -96, 108, 0, True)

    def _on_load_robot(self):
        task = asyncio.ensure_future(load_test_file(self._extension_path + "/data/usd/robots/franka/franka.usd"))
        asyncio.ensure_future(self._setup_camera(task))

    def _on_move_joints(self):
        self._physx_subscription = self._physxIFace.subscribe_physics_step_events(self._on_physics_step)
        self._physxIFace.force_load_physics_from_usd()
        self._timeline.play()
        self._sub_stage_event = (
            omni.usd.get_context().get_stage_event_stream().create_subscription_to_pop(self._on_stage_event)
        )

    def _on_stage_event(self, event):
        if event.type == int(omni.usd.StageEventType.OPENED) or event.type == int(omni.usd.StageEventType.CLOSED):
            # stage was opened or closed, cleanup
            self._physx_subscription = None
            self.ar = _dynamic_control.INVALID_HANDLE

    def _on_first_step(self):
        self.ar = self._dc.get_articulation("/panda")
        if self.ar == _dynamic_control.INVALID_HANDLE:
            print("*** '%s' is not an articulation" % "/panda")
            return

        num_dofs = self._dc.get_articulation_dof_count(self.ar)
        dof_props = self._dc.get_articulation_dof_properties(self.ar)
        self.dof_props_label.text = str("--- DOF properties:\n") + str(dof_props) + "\n"

        dof_types = dof_props["type"]
        has_limits = dof_props["hasLimits"]
        lower_limits = dof_props["lower"]
        upper_limits = dof_props["upper"]

        self.dof_props_label.text = str("--- DOF properties:\n") + str(dof_props) + "\n"

        # allocate dof state buffer
        dof_states = np.zeros(num_dofs, dtype=_dynamic_control.DofState.dtype)
        dof_positions = dof_states["pos"]
        speed_scale = 1.0

        # initialize default positions, limits, and speeds (make sure they are in reasonable ranges)
        defaults = np.array([0.0, -0.0, 0.0, -0.0, 0.0, 3.037, 0.741, 4.0, 4.0], dtype=np.float32)
        speeds = np.zeros(num_dofs)

        for i in range(num_dofs):
            if has_limits[i]:
                if dof_types[i] == _dynamic_control.DOF_ROTATION:
                    lower_limits[i] = clamp(lower_limits[i], -np.pi, np.pi)
                    upper_limits[i] = clamp(upper_limits[i], -np.pi, np.pi)
                # make sure our default position is in range
                if lower_limits[i] > 0.0:
                    defaults[i] = lower_limits[i]
                elif upper_limits[i] < 0.0:
                    defaults[i] = upper_limits[i]
            else:
                # set reasonable animation limits for unlimited joints
                if dof_types[i] == _dynamic_control.DOF_ROTATION:
                    # unlimited revolute joint
                    lower_limits[i] = -np.pi
                    upper_limits[i] = np.pi
                elif dof_types[i] == _dynamic_control.DOF_TRANSLATION:
                    # unlimited prismatic joint
                    lower_limits[i] = -1.0
                    upper_limits[i] = 1.0
            # set DOF position to default
            dof_positions[i] = defaults[i]
            # set speed depending on DOF type and range of motion
            if dof_types[i] == _dynamic_control.DOF_ROTATION:
                speeds[i] = speed_scale * clamp(2 * (upper_limits[i] - lower_limits[i]), 0.25 * np.pi, 3.0 * np.pi)
            else:
                speeds[i] = speed_scale * clamp(2 * (upper_limits[i] - lower_limits[i]), 0.1, 7.0)

        self.num_dofs = num_dofs
        self.defaults = defaults
        self.speeds = speeds
        self.lower_limits = lower_limits
        self.upper_limits = upper_limits

        self.dof_states = dof_states
        self.dof_positions = dof_positions

        self.anim_state = ANIM_SEEK_LOWER
        self.current_dof = 0

    def _on_physics_step(self, step):
        if self._timeline.is_playing():
            if self.ar == _dynamic_control.INVALID_HANDLE:
                self._on_first_step()
            dof = self.current_dof
            speed = self.speeds[dof]
            # animate the dofs
            if self.anim_state == ANIM_SEEK_LOWER:
                self.dof_positions[dof] -= speed * step
                if self.dof_positions[dof] <= self.lower_limits[dof]:
                    self.dof_positions[dof] = self.lower_limits[dof]
                    self.anim_state = ANIM_SEEK_UPPER
            elif self.anim_state == ANIM_SEEK_UPPER:
                self.dof_positions[dof] += speed * step
                if self.dof_positions[dof] >= self.upper_limits[dof]:
                    self.dof_positions[dof] = self.upper_limits[dof]
                    self.anim_state = ANIM_SEEK_DEFAULT
            if self.anim_state == ANIM_SEEK_DEFAULT:
                self.dof_positions[dof] -= speed * step
                if self.dof_positions[dof] <= self.defaults[dof]:
                    self.dof_positions[dof] = self.defaults[dof]
                    self.anim_state = ANIM_FINISHED
            elif self.anim_state == ANIM_FINISHED:
                self.dof_positions[dof] = self.defaults[dof]
                self.current_dof = (dof + 1) % self.num_dofs
                self.anim_state = ANIM_SEEK_LOWER
                # print("Animating DOF %d" % (self.current_dof,))
            self._dc.wake_up_articulation(self.ar)
            self._dc.set_articulation_dof_position_targets(self.ar, self.dof_positions)
            dof_states = self._dc.get_articulation_dof_states(self.ar, _dynamic_control.STATE_ALL)
            self.dof_states_label.text = str("--- DOF states:\n") + str(dof_states) + "\n"

        return
