import omni.ext
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
import carb
import gc
import asyncio
import weakref
import os
import omni.physx as _physx
from omni.isaac.pyalice import Codelet, Composite
import logging
import numpy as np
import time

EXTENSION_NAME = "REB Vehicle Control"


class PyaliceApp:
    def __init__(self):
        from omni.isaac.pyalice import Application

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.robot_engine_bridge")
        self._reb_extension_path = ext_manager.get_extension_path(ext_id)

        self.app = Application(name="vehicle_control", asset_path=self._reb_extension_path)
        self.app.logger.setLevel(logging.ERROR)
        self._stopped = True

    def run(self, duration: float = 1.0):
        self.app.start_wait_stop(duration)

    def start(self):
        self.app.start()
        self._stopped = False

    def stop(self):
        if self._stopped is False:
            self.app.stop()
            self._stopped = True
            time.sleep(2.0)

    def is_stopped(self):
        return self._stopped

    def __del__(self):
        self.stop()


class VehicleControl(Codelet):
    """
    Controls a REB vehicle
    """

    def start(self):
        self.tx = self.isaac_proto_tx("CompositeProto", "cmd")
        self._entities = [["body", "acceleration", 1], ["steering", "position", 1]]
        self.tick_periodically(0.05)

    def tick(self):
        values = np.array([self.config.accelerator, self.config.steering])
        self.tx._msg = Composite.create_composite_message(self._entities, values)
        self.tx.publish()


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._window = ui.Window(EXTENSION_NAME, width=800, height=400, visible=False)
        self._window.set_visibility_changed_fn(self._on_window)
        menu_items = [
            MenuItemDescription(name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
        ]
        self._menu_items = [
            MenuItemDescription(
                name="Communicating", sub_menu=[MenuItemDescription(name="Robot Engine Bridge", sub_menu=menu_items)]
            )
        ]
        add_menu_items(self._menu_items, "Isaac Examples")
        self._viewport = omni.kit.viewport.get_default_viewport_window()
        self._timeline = omni.timeline.get_timeline_interface()
        self._pyalice_app = None
        self._vehicle_control = None
        # Simple button style that grays out the button if disabled
        self._button_style = {":disabled": {"color": 0xFF000000}}
        with self._window.frame:
            with ui.VStack(height=0):
                ui.Label(
                    "Sample to show how pyalice can be used to send vehicle control commands directly from isaac sim"
                )

                ui.Label("Press the Toggle Controller button, and also create the REB application and press play")
                ui.Label("Use WASD to control")
                ui.Button("Toggle Controller", clicked_fn=self._start_app)
                # with ui.HStack():
                #     ui.Label("Command Channel: ")
                #     self._command_channel = omni.ui.StringField().model
                #     self._command_channel.set_value("vehicle_command")
                with ui.HStack():
                    ui.Label("Acceleration Gain: ")
                    self._acceleration_gain = ui.FloatField().model
                    self._acceleration_gain.set_value(1.0)
                # ui.HStack():
                #     ui.Label("Steering Gain: ")
                #     self._steering_gain = ui.FloatField().model
                #     self._steering_gain.set_value(1.0)

    def _on_window(self, status):
        if status:
            self._appwindow = omni.appwindow.get_default_app_window()
            self._input = carb.input.acquire_input_interface()
            self._keyboard = self._appwindow.get_keyboard()
            self._sub_keyboard = self._input.subscribe_to_keyboard_events(self._keyboard, self._sub_keyboard_event)
            self._timeline_sub = self._timeline.get_timeline_event_stream().create_subscription_to_pop(
                self._on_timeline_event
            )
        else:
            self._timeline_sub = None
            self._sub_keyboard = None

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    def _on_timeline_event(self, e):
        if not self._vehicle_control:
            return True
        if (
            e.type == int(omni.timeline.TimelineEventType.PLAY)
            or e.type == int(omni.timeline.TimelineEventType.STOP)
            or e.type == int(omni.timeline.TimelineEventType.PAUSE)
        ):
            self._vehicle_control.config.accelerator = 0.0
            self._vehicle_control.config.steering = 0.0

    def _start_app(self):
        if self._pyalice_app and self._pyalice_app.is_stopped() is False:
            self._pyalice_app.stop()
            self._pyalice_app = None
            self._vehicle_control = None
            return

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.robot_engine_bridge")
        self._reb_extension_path = ext_manager.get_extension_path(ext_id)

        self._pyalice_app = PyaliceApp()

        self._pyalice_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )
        sim_in = self._pyalice_app.app.nodes["simulation.interface"]["input"]
        sim_out = self._pyalice_app.app.nodes["simulation.interface"]["output"]
        self._vehicle_control = self._pyalice_app.app.add("controller").add(VehicleControl, name="VehicleControl")
        self._vehicle_control.config.accelerator = 0.0
        self._vehicle_control.config.steering = 0.0
        self._pyalice_app.app.connect(self._vehicle_control, "cmd", sim_in, "vehicle_command")
        self._pyalice_app.start()

    def _sub_keyboard_event(self, event, *args, **kwargs):
        """Handle keyboard events
        w,s,a,d as arrow keys for jetbot movement
        
        Args:
            event (int): keyboard event type
        # """
        if not self._vehicle_control:
            return True
        if event.type == carb.input.KeyboardEventType.KEY_PRESS:
            if event.input == carb.input.KeyboardInput.W:
                self._vehicle_control.config.accelerator = 1.0 * self._acceleration_gain.get_value_as_float()
            if event.input == carb.input.KeyboardInput.S:
                self._vehicle_control.config.accelerator = -1.0 * self._acceleration_gain.get_value_as_float()
            if event.input == carb.input.KeyboardInput.A:
                self._vehicle_control.config.steering = 1.0  # * self._steering_gain.get_value_as_float()
            if event.input == carb.input.KeyboardInput.D:
                self._vehicle_control.config.steering = -1.0  # * self._steering_gain.get_value_as_float()
        if event.type == carb.input.KeyboardEventType.KEY_REPEAT:
            pass
        if event.type == carb.input.KeyboardEventType.KEY_RELEASE:
            if event.input == carb.input.KeyboardInput.W or event.input == carb.input.KeyboardInput.S:
                self._vehicle_control.config.accelerator = 0.0
            if event.input == carb.input.KeyboardInput.A or event.input == carb.input.KeyboardInput.D:
                self._vehicle_control.config.steering = 0.0

        return True

    def on_shutdown(self):
        self._sub_keyboard = None
        if self._pyalice_app:
            self._pyalice_app.stop()
        self._pyalice_app = None
        remove_menu_items(self._menu_items, "Isaac Examples")
        gc.collect()
        pass
