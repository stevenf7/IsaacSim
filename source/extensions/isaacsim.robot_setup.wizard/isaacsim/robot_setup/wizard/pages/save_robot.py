import os

import omni.ui as ui
import omni.usd
from pxr import Gf, Sdf, Usd

from ..builders.robot_templates import RobotRegistry
from ..builders.save_robot_helper import create_variant_usd
from ..progress import ProgressColorState, ProgressRegistry
from ..utils.ui_utils import ButtonWithIcon, custom_header, separator


class SaveRobot:
    def __init__(self, visible, *args, **kwargs):
        self.visible = visible
        self.frame = ui.Frame(visible=visible)
        self.frame.set_build_fn(self._build_frame)

    def destroy(self):
        self.frame.destroy()

    def _build_frame(self):
        with ui.CollapsableFrame("Save Robot", build_header_fn=custom_header):
            with ui.ScrollingFrame():
                with ui.VStack(name="setting_content_vstack"):
                    with ui.ZStack(height=0):
                        ui.Rectangle(name="save_stack")
                        with ui.VStack(spacing=2, name="margin_vstack"):
                            separator("Minimal Environment")
                            ui.Spacer(height=4)
                            ui.Label(
                                "The minimal environment settings will be saved outside of the default robot prim, It is there to facilitate debugging and will not be loaded when adding the robot into other scenes by reference or payload.",
                                word_wrap=True,
                                height=0,
                                name="sub_separator",
                            )
                            ui.Spacer(height=10)
                            with ui.HStack(spacing=2):
                                ui.Label("Ground Plane", width=0, height=0, name="property")
                                ui.Spacer(width=2)
                                self._save_ground_check = ui.CheckBox(width=25, height=22)
                                self._save_ground_check.model.set_value(False)

                                ui.Spacer(width=10)
                                ui.Label("Default Light", width=0, height=0, name="property")
                                ui.Spacer(width=2)
                                self._save_light_check = ui.CheckBox(width=25, height=22)
                                self._save_light_check.model.set_value(False)

                                ui.Spacer(width=10)
                                ui.Label("Physics Scene", width=0, height=0, name="property")
                                ui.Spacer(width=2)
                                self._save_physics_scene_check = ui.CheckBox(width=25, height=22)
                                self._save_physics_scene_check.model.set_value(False)

                    with ui.ZStack(height=0):
                        ui.Rectangle(name="save_stack")

                        with ui.VStack(spacing=2, name="margin_vstack"):
                            separator("Save Robot")
                            ui.Spacer(height=4)
                            ui.Label(
                                "Once you are finished setting up your robot, you can save as a .usd file and use for training."
                                "If you make changes to the robot’s joints, drives or colliders, you will want to save your changes again",
                                word_wrap=True,
                                height=0,
                                name="sub_separator",
                            )
                            ui.Spacer(height=20)

                            ButtonWithIcon(
                                "Save Robot", name="save", image_width=18, height=44, clicked_fn=self.save_robot
                            )
                            ui.Spacer(height=10)

    def save_robot(self):
        ProgressRegistry().set_step_progress("Save Robot", ProgressColorState.COMPLETE)

        # save current layers
        robot = RobotRegistry().get()
        physics_filepath = f"{robot.name}_physics.usd"
        config_dir = os.path.join(robot.robot_root_folder, "configurations")

        stage = omni.usd.get_context().get_stage()

        # set the default prim to the robot prim
        stage.SetDefaultPrim(stage.GetPrimAtPath(f"/{robot.name}"))

        # the current stage is the physics usd
        omni.usd.get_context().save_as_stage(os.path.join(config_dir, physics_filepath))
        # base layer should already been saved during the hierarchy helper

        add_ground = self._save_ground_check.model.get_value_as_bool()
        add_lights = self._save_light_check.model.get_value_as_bool()
        add_physics_scene = self._save_physics_scene_check.model.get_value_as_bool()

        create_variant_usd(add_ground, add_lights, add_physics_scene)

    def set_visible(self, visible):
        if self.frame:
            self.frame.visible = visible
