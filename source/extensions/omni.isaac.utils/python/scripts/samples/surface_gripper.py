# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni
import omni.kit.usd
import omni.kit.commands
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
import omni.ui as ui
import omni.ext
from omni.isaac.dynamic_control import _dynamic_control as dc
import carb.tokens
import carb
import asyncio
import numpy as np
from pxr import UsdLux, UsdGeom, Sdf, Gf, UsdPhysics
import omni.physx as _physx
import weakref

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.utils._isaac_utils.surface_grippers import Surface_Gripper_Properties, Surface_Gripper


EXTENSION_NAME = "Surface Gripper"


class Extension(omni.ext.IExt):
    def on_startup(self):
        """
        Creates the User inferface and loads the interfaces for required libraries.
        """

        # Loads interfaces
        self._timeline = omni.timeline.get_timeline_interface()
        self._viewport = omni.kit.viewport.get_default_viewport_window()
        self._dc = dc.acquire_dynamic_control_interface()
        self._usd_context = omni.usd.get_context()
        # Creates UI window with default size of 600x300
        self._window = omni.ui.Window(
            title=EXTENSION_NAME, width=300, height=200, visible=False, dockPreference=ui.DockPreference.LEFT_BOTTOM
        )
        self._window.set_visibility_changed_fn(self._on_window)
        menu_items = [
            MenuItemDescription(name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
        ]
        self._menu_items = [
            MenuItemDescription(
                name="Controlling", sub_menu=[MenuItemDescription(name="Manipulation", sub_menu=menu_items)]
            )
        ]
        # self._menu_items = [
        #     MenuItemDescription(
        #         name="Samples",
        #         sub_menu=[
        #             MenuItemDescription(
        #                 name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback()
        #             )
        #         ],
        #     )
        # ]
        add_menu_items(self._menu_items, "Isaac Examples")
        self._models = {}
        with self._window.frame:
            with ui.VStack(height=0):
                self._models["create_button"] = ui.Button(
                    "Create Scenario",
                    clicked_fn=self._on_create_scenario_button_clicked,
                    tooltip="Creates a new scenario with the cone on top of the Cube",
                )
                self._models["toggle_button"] = ui.Button(
                    "Close Gripper",
                    clicked_fn=self._on_toggle_gripper_button_clicked,
                    tooltip="Toggles the surface gripper",
                )
                with ui.HStack(height=0):
                    ui.Label("Gripper Force Up")
                    self._models["force_slider"] = ui.FloatSlider(min=0.0, max=5.0e4).model
                    self._models["force_button"] = ui.Button(
                        "Apply Force",
                        clicked_fn=self._on_force_button_clicked,
                        tooltip="Applies a force on the Z axis on the cone Center of Mass with the slider value",
                    )
                with ui.HStack(height=0):
                    ui.Label("Gripper Speed Up")
                    self._models["speed_slider"] = ui.FloatSlider(min=0.0, max=1.0e3).model
                    self._models["speed_button"] = ui.Button(
                        "Set Speed",
                        clicked_fn=self._on_speed_button_clicked,
                        tooltip="Sets the Cone velocity towards the Z axis with the slider value",
                    )

        self.surface_gripper = None
        self.cone = None
        self.box = None
        self._stage_id = -1

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Isaac Examples")
        self._physx_subs = None
        self._window = None

    def _on_window(self, status):
        if status:
            self._usd_context = omni.usd.get_context()
            if self._usd_context is not None:
                self._stage_event_sub = (
                    omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self._on_update_ui)
                )
        else:
            self._stage_event_sub = None
            self._physx_subs = None

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    def _on_update_ui(self, widget):
        self._models["create_button"].enabled = self._timeline.is_playing()
        self._models["toggle_button"].enabled = self._timeline.is_playing()
        self._models["force_button"].enabled = self._timeline.is_playing()
        self._models["speed_button"].enabled = self._timeline.is_playing()
        # If the scene has been reloaded, reset UI to create Scenario
        if self._usd_context.get_stage_id() != self._stage_id:
            self._models["create_button"].enabled = True
            self._models["create_button"].text = "Create Scenario"
            self._models["create_button"].set_tooltip("Creates a new scenario with the cone on top of the Cube")
            self._models["create_button"].set_clicked_fn(self._on_create_scenario_button_clicked)
            self.cone = None
            self.box = None
            self._stage_id = -1

    def _toggle_gripper_button_ui(self):
        # Checks if the surface gripper has been created
        if self.surface_gripper is not None:
            if self.surface_gripper.is_closed():
                self._models["toggle_button"].text = "Open Gripper"
            else:
                self._models["toggle_button"].text = "Close Gripper"

    def _on_simulation_step(self, step):
        # Checks if the simulation is playing, and if the stage has been loaded
        if self._timeline.is_playing() and self._stage_id != -1:
            # Check if the handles for cone and box have been loaded
            if self.cone is None:
                self.cone = self._dc.get_rigid_body("/GripperCone")
                self.box = self._dc.get_rigid_body("/Box")
            # If the surface Gripper has been created, update wheter it has been broken or not
            if self.surface_gripper is not None:
                self.surface_gripper.update()
                if self.surface_gripper.is_closed():
                    self.coneGeom.GetDisplayColorAttr().Set([self.color_closed])
                else:
                    self.coneGeom.GetDisplayColorAttr().Set([self.color_open])
                self._toggle_gripper_button_ui()

    def _on_reset_scenario_button_clicked(self):
        if self._timeline.is_playing() and self._stage_id != -1:
            self._dc.set_rigid_body_linear_velocity(self.cone, [0, 0, 0])
            self._dc.set_rigid_body_linear_velocity(self.box, [0, 0, 0])
            self._dc.set_rigid_body_angular_velocity(self.cone, [0, 0, 0])
            self._dc.set_rigid_body_angular_velocity(self.box, [0, 0, 0])

            self._dc.set_rigid_body_pose(self.cone, self.gripper_start_pose)
            self._dc.set_rigid_body_pose(self.box, self.box_start_pose)

        if self.surface_gripper is not None:
            self.surface_gripper.open()

    async def _create_scenario(self, task):
        done, pending = await asyncio.wait({task})
        if task in done:
            # Repurpose button to reset Scene
            self._models["create_button"].text = "Reset Scene"
            self._models["create_button"].set_tooltip("Resets scenario with the cone on top of the Cube")

            # Get Handle for stage and stage ID to check if stage was reloaded
            self._stage = self._usd_context.get_stage()
            self._stage_id = self._usd_context.get_stage_id()
            self._timeline.stop()
            self._models["create_button"].set_clicked_fn(self._on_reset_scenario_button_clicked)

            # Adds a light to the scene
            distantLight = UsdLux.DistantLight.Define(self._stage, Sdf.Path("/DistantLight"))
            distantLight.CreateIntensityAttr(500)
            distantLight.AddOrientOp().Set(Gf.Quatf(-0.3748, -0.42060, -0.0716, 0.823))

            # Set up stage with Z up, treat units as cm, set up gravity and ground plane
            UsdGeom.SetStageUpAxis(self._stage, UsdGeom.Tokens.z)
            UsdGeom.SetStageMetersPerUnit(self._stage, 0.01)
            self.scene = UsdPhysics.Scene.Define(self._stage, Sdf.Path("/physicsScene"))
            self.scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
            self.scene.CreateGravityMagnitudeAttr().Set(981.0)
            omni.kit.commands.execute(
                "AddGroundPlaneCommand",
                stage=self._stage,
                planePath="/groundPlane",
                axis="Z",
                size=1000.0,
                position=Gf.Vec3f(0),
                color=Gf.Vec3f(0.5),
            )
            # Colors to represent when gripper is open or closed
            self.color_closed = Gf.Vec3f(1.0, 0.2, 0.2)
            self.color_open = Gf.Vec3f(0.2, 1.0, 0.2)

            # Cone that will represent the gripper
            self.gripper_start_pose = dc.Transform([0, 0, 50.1], [0, 0, 0, 1])
            self.coneGeom = self.createRigidBody(
                UsdGeom.Cone,
                "/GripperCone",
                1.0,
                [10, 10, 30],
                self.gripper_start_pose.p,
                self.gripper_start_pose.r,
                self.color_open,
            )

            # Box to be picked
            self.box_start_pose = dc.Transform([0, 0, 10], [0, 0, 0, 1])
            self.boxGeom = self.createRigidBody(
                UsdGeom.Cube, "/Box", 1.0, [10, 10, 10], self.box_start_pose.p, self.box_start_pose.r, [0.2, 0.2, 1]
            )

            # Gripper properties
            self.sgp = Surface_Gripper_Properties()
            self.sgp.d6JointPath = ""
            self.sgp.parentPath = "/GripperCone"
            self.sgp.offset = dc.Transform()
            self.sgp.offset.p.x = 0
            self.sgp.offset.p.z = -30.01
            self.sgp.offset.r = [0, 0.7171, 0, 0.7171]  # Rotate to point gripper in Z direction
            self.sgp.gripThreshold = 2
            self.sgp.forceLimit = 1.0e4
            self.sgp.torqueLimit = 1.0e5
            self.sgp.bendAngle = np.pi / 4
            self.sgp.stiffness = 1.0e4
            self.sgp.damping = 1.0e3

            self.surface_gripper = Surface_Gripper(self._dc)
            self.surface_gripper.initialize(self.sgp)

            # Set camera to a nearby pose and looking directly at the Gripper cone
            self._viewport.set_camera_position("/OmniverseKit_Persp", 400, 400, 400, True)
            self._viewport.set_camera_target("/OmniverseKit_Persp", *self.gripper_start_pose.p, True)

            self._physx_subs = _physx.get_physx_interface().subscribe_physics_step_events(self._on_simulation_step)
            self._timeline.play()

    def _on_create_scenario_button_clicked(self):
        # wait for new stage before creating scenario
        task = asyncio.ensure_future(omni.usd.get_context().new_stage_async())
        asyncio.ensure_future(self._create_scenario(task))

    def _on_toggle_gripper_button_clicked(self):
        if self._timeline.is_playing():
            if self.surface_gripper.is_closed():
                self.surface_gripper.open()
            else:
                self.surface_gripper.close()

    def _on_speed_button_clicked(self):
        if self._timeline.is_playing():
            self._dc.set_rigid_body_linear_velocity(
                self.cone, [0, 0, self._models["speed_slider"].get_value_as_float()]
            )

    def _on_force_button_clicked(self):
        if self._timeline.is_playing():
            self._dc.apply_body_force(self.cone, [0, 0, self._models["force_slider"].get_value_as_float()], [0, 0, 0])

    def createRigidBody(self, bodyType, boxActorPath, mass, scale, position, rotation, color):
        p = Gf.Vec3f(position[0], position[1], position[2])
        orientation = Gf.Quatf(rotation[0], rotation[1], rotation[2], rotation[3])
        scale = Gf.Vec3f(scale[0], scale[1], scale[2])

        bodyGeom = bodyType.Define(self._stage, boxActorPath)
        bodyPrim = self._stage.GetPrimAtPath(boxActorPath)
        bodyGeom.AddTranslateOp().Set(p)
        bodyGeom.AddOrientOp().Set(orientation)
        bodyGeom.AddScaleOp().Set(scale)
        bodyGeom.CreateDisplayColorAttr().Set([color])

        UsdPhysics.CollisionAPI.Apply(bodyPrim)
        if mass > 0:
            massAPI = UsdPhysics.MassAPI.Apply(bodyPrim)
            massAPI.CreateMassAttr(mass)
        UsdPhysics.RigidBodyAPI.Apply(bodyPrim)
        UsdPhysics.CollisionAPI(bodyPrim)
        print(bodyPrim.GetPath().pathString)
        return bodyGeom
