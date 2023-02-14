import carb
import asyncio

import omni.ui as ui

from omni.isaac.core.world import World
from omni.isaac.core.utils.stage import update_stage_async

from ..ui_widget_wrappers import UIWidgetWrapper

from omni.isaac.ui.ui_utils import btn_builder


class LoadButton(UIWidgetWrapper):
    def __init__(self, label: str, text: str, tooltip="", setup_scene_fn=None, setup_post_load_fn=None):
        """_summary_

		Args:
			frame (ui.Frame): A UI frame under which this UI element will live
			label (str): A short descriptive text next to the button
			text (str): The label that is directly on the button.
			tooltip (str, optional): Text that appears when the mouse is hovered over the button. Defaults to "".
			setup_scene_fn (function, optional): _description_. Defaults to None.
			setup_post_load_fn (function, optional): _description_. Defaults to None.
		"""
        self.setup_scene_fn = setup_scene_fn
        self.setup_post_load_fn = setup_post_load_fn

        self.button = self._create_ui_widget(label, text, tooltip)
        super().__init__(self.button)

        self._world_settings = {}

    def set_setup_scene_fn(self, function):
        """_summary_

		Args:
			function (_type_): _description_
		"""
        self.setup_scene_fn = function

    def set_setup_post_load_fn(self, function):
        """
		This is effectively the same as a reset() function.  It will get called after assets have been loaded onto the stage
		"""
        self.setup_post_load_fn = function

    def set_world_settings(self, **kwargs):
        """
		Pressing a Load Button will create a new instance of the omni.isaac.core.World.  
		The default settings will be used unless the user specifies new settings at runtime before the Load Button is clicked.

		The default settings will ensure that the physics and rendering timesteps are fixed at 1/60.0 seconds (see set_defaults argument).
		It is important to note that this will ensure that code is deterministic, but may not be executed in real time.
		By settings set_defaults = False, the simulation will attempt to roll out in real time.  I.e. physics and render dts will adjust automatically if the 
		simulation is running too fast or slow.

		Args:
            physics_dt (Optional[float], optional): dt between physics steps. Defaults to None.
            rendering_dt (Optional[float], optional): dt between rendering steps. Note: rendering means 
                                                       rendering a frame of the current application and not 
                                                       only rendering a frame to the viewports/ cameras. So UI
                                                       elements of Isaac Sim will be refereshed with this dt 
                                                       as well if running non-headless. 
                                                       Defaults to None.
            stage_units_in_meters (Optional[float], optional): The metric units of assets. This will affect gravity value..etc.
                                                       Defaults to None.
            physics_prim_path (Optional[str], optional): specifies the prim path to create a PhysicsScene at, 
                                                 only in the case where no PhysicsScene already defined. 
                                                 Defaults to "/physicsScene".
            set_defaults (bool, optional): set to True to use the defaults settings
                                            [physics_dt = 1.0/ 60.0,
                                            stage units in meters = 1 (i.e in meters),
                                            rendering_dt = 1.0 / 60.0,
                                            gravity = -9.81 m / s
                                            ccd_enabled,
                                            stabilization_enabled,
                                            gpu dynamics turned off,
                                            broadcast type is MBP,
                                            solver type is TGS]. Defaults to True.
            backend (str, optional): specifies the backend to be used (numpy or torch). Defaults to numpy.
            device (Optional[str], optional): specifies the device to be used if running on the gpu with torch backend.
        """
        self._world_settings = kwargs

    def _on_click(self):
        """This function is called when the Load Button is Clicked.
		"""

        # From an extension workflow, the stage and world need to be interacted with asynchronously

        async def _on_click_async():
            # Remove any previous World instance
            prev_world = World.instance()
            if prev_world is not None:
                prev_world.clear_all_callbacks()
                prev_world.clear_instance()
                prev_world = None
                # prev_world.clear()
            await update_stage_async()

            # Create a new World instance with user-defined settings.  See self.set_world_settings()
            world = World(**self._world_settings)

            # Call user function to put assets on the stage and add them to the World
            if self.setup_scene_fn is not None:
                self.setup_scene_fn()

            await world.reset_async()
            await world.pause_async()

            # User assets are now initialized, and the timeline is playing at timestep 0
            if self.setup_post_load_fn is not None:
                self.setup_post_load_fn()

        asyncio.ensure_future(_on_click_async())

    def _create_ui_widget(self, label, text, tooltip):
        load_btn = btn_builder(label=label, text=text, tooltip=tooltip, on_clicked_fn=self._on_click)
        load_btn.enabled = True
        return load_btn


class ResetButton(UIWidgetWrapper):
    def __init__(self, label: str, text: str, tooltip="", pre_reset_fn=None, post_reset_fn=None):
        self._pre_reset_fn = pre_reset_fn
        self._post_reset_fn = post_reset_fn

        self.button = self._create_ui_widget(label, text, tooltip)
        super().__init__(self.button)

    def set_pre_reset_fn(self, pre_reset_fn):
        self._pre_reset_fn = pre_reset_fn

    def set_post_reset_fn(self, post_reset_fn):
        self._post_reset_fn = post_reset_fn

    def _on_click(self):
        """This function is called when the Reset Button is Clicked.
		"""

        # From an extension workflow, the stage and world need to be interacted with asynchronously

        async def _on_click_async():
            # Call user function pre_reset
            if self._pre_reset_fn is not None:
                self._pre_reset_fn()

            world = World.instance()

            if world is None:
                carb.log_warn("Reset Button was used when there is no instance of World.")
            else:
                await world.reset_async()
                await world.pause_async()

            # User assets are initialized, and the timeline is playing at timestep 0
            if self._post_reset_fn is not None:
                self._post_reset_fn()

        asyncio.ensure_future(_on_click_async())

    def _create_ui_widget(self, label, text, tooltip):
        reset_btn = btn_builder(label=label, text=text, tooltip=tooltip, on_clicked_fn=self._on_click)
        reset_btn.enabled = True
        return reset_btn
