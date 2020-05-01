import os

import omni.ext
import omni.kit.commands
import omni.kit.editor
import omni.kit.ui

import omni.physx._physx as omni_physx
from .. import _dynamic_control

from .test_body import test_body
from .test_pickles import test_pickles
from .test_articulation import test_articulation
from .test_dofs import test_dofs
from .joint_monkey import get_joint_monkey
from .test_attractor import get_test_attractor
from .test_cartpole import get_cart_pole

EXTENSION_NAME = "Dynamic Control"


class Extension(omni.ext.IExt):
    def on_startup(self):
        print("Loading Dynamic Control Extension")
        self._dc = _dynamic_control.acquire_dynamic_control_interface()

        # menu_path = f"Window/{EXTENSION_NAME}"
        # self._window = omni.kit.ui.Window(EXTENSION_NAME, 960, 600, menu_path=menu_path, add_to_menu=True)
        # self._window.hide()
        # self._build_window_ui()
        # self._window.set_update_fn(self._on_window_update)

        # self._editor = omni.kit.editor.get_editor_interface()

        # self._physx = omni_physx.acquire_physx_interface()
        # self._physics_subscription = self._physx.subscribe_physics_step_events(self._on_physics_step)

        # # active script
        # self._script = None

        # self._is_playing = self._editor.is_playing()

        # for b in self._dynamic_buttons:
        #     b.enabled = self._is_playing

    def on_shutdown(self):
        print("Shutting down Dynamic Control")
        _dynamic_control.release_dynamic_control_interface(self._dc)

    def _build_window_ui(self):

        self._dynamic_buttons = []

        hello_button = omni.kit.ui.Button("Hello")
        hello_button.set_clicked_fn(self._on_hello_clicked)
        self._window.layout.add_child(hello_button)

        pickles_button = omni.kit.ui.Button("Test pickles")
        pickles_button.set_clicked_fn(self._on_pickles_clicked)
        self._window.layout.add_child(pickles_button)

        test_body_button = omni.kit.ui.Button("Test Body")
        test_body_button.set_clicked_fn(self._on_test_body_clicked)
        self._window.layout.add_child(test_body_button)
        self._dynamic_buttons.append(test_body_button)

        test_articulation_button = omni.kit.ui.Button("Test Articulation")
        test_articulation_button.set_clicked_fn(self._on_test_articulation_clicked)
        self._window.layout.add_child(test_articulation_button)
        self._dynamic_buttons.append(test_articulation_button)

        test_cartpole_button = omni.kit.ui.Button("Test Cartpole")
        test_cartpole_button.set_clicked_fn(self._on_test_cartpole_clicked)
        self._window.layout.add_child(test_cartpole_button)
        self._dynamic_buttons.append(test_cartpole_button)

        test_dofs_button = omni.kit.ui.Button("Test DOFs")
        test_dofs_button.set_clicked_fn(self._on_test_dofs_clicked)
        self._window.layout.add_child(test_dofs_button)
        self._dynamic_buttons.append(test_dofs_button)

        test_attractor_button = omni.kit.ui.Button("Test Attractor")
        test_attractor_button.set_clicked_fn(self._on_test_attractor_clicked)
        self._window.layout.add_child(test_attractor_button)
        self._dynamic_buttons.append(test_attractor_button)

        joint_monkey_button = omni.kit.ui.Button("Joint Monkey")
        joint_monkey_button.set_clicked_fn(self._on_joint_monkey_clicked)
        self._window.layout.add_child(joint_monkey_button)
        self._dynamic_buttons.append(joint_monkey_button)

        self._cancel_button = omni.kit.ui.Button("Cancel Active Script")
        self._cancel_button.set_clicked_fn(self._on_cancel_clicked)
        self._window.layout.add_child(self._cancel_button)
        self._cancel_button.enabled = False

    def _on_window_update(self, dt):
        is_playing = self._editor.is_playing()
        if is_playing and not self._is_playing:
            self._on_start()
        elif not is_playing and self._is_playing:
            self._on_stop()
        self._is_playing = is_playing

    def _on_start(self):
        # restart active script, if any
        script = self._script
        if script is not None:
            if getattr(script, "start", None) is not None:
                script.start(self._dc)
        # enable dynamic buttons
        for b in self._dynamic_buttons:
            b.enabled = True

    def _on_stop(self):
        # stop (but don't delete) active script, if any
        if getattr(self._script, "stop", None) is not None:
            self._script.stop(self._dc)
        # disable dynamic buttons
        for b in self._dynamic_buttons:
            b.enabled = False

    def _on_physics_step(self, dt):
        # print("Stepping")
        if self._script is not None:
            if getattr(self._script, "update", None) is not None:
                self._script.update(self._dc, dt)

    def _set_active_script(self, script):
        self._cancel_active_script()
        try:
            if getattr(script, "start", None) is not None:
                script.start(self._dc)
            self._script = script
            self._cancel_button.enabled = True
        except:
            print("*** Failed to start script")

    def _cancel_active_script(self):
        if self._script is not None:
            if getattr(self._script, "stop", None) is not None:
                self._script.stop(self._dc)
            del self._script
            self._script = None
            self._cancel_button.enabled = False

    def _on_cancel_clicked(self, button):
        self._cancel_active_script()

    def _on_hello_clicked(self, button):
        self._dc.hello()

    def _on_pickles_clicked(self, button):
        test_pickles()

    def _on_test_body_clicked(self, button):
        test_body(self._dc)

    def _on_test_articulation_clicked(self, button):
        test_articulation(self._dc)

    def _on_test_cartpole_clicked(self, button):
        self._set_active_script(get_cart_pole())

    def _on_test_dofs_clicked(self, button):
        test_dofs(self._dc)

    def _on_test_attractor_clicked(self, button):
        self._set_active_script(get_test_attractor())

    def _on_joint_monkey_clicked(self, button):
        self._set_active_script(get_joint_monkey())
