# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb
import omni
import asyncio
from omni.isaac.contact_sensor import _contact_sensor
from omni.physx.scripts.physicsUtils import *
from pxr import Usd, UsdLux, UsdGeom, UsdShade, Sdf, Gf, Tf, Vt, UsdPhysics, PhysxSchema
from omni.physx import get_physx_interface
from omni.physx.bindings._physx import SimulationEvent
from random import seed
from random import random


import weakref
from pxr import Usd, UsdGeom
import os
import omni.physx as _physx
import omni
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription


class Contact_sensor_demo(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        self._extension_path = ext_manager.get_extension_path(ext_id)

        self._menu_items = [
            MenuItemDescription(
                name="Sensing",
                sub_menu=[MenuItemDescription(name="Contact", onclick_fn=lambda a=weakref.proxy(self): a.build_ui())],
            )
        ]
        add_menu_items(self._menu_items, "Isaac Examples")
        self.meters_per_unit = 0.01
        self._window = None

    def _on_stage_event(self, event):
        if event.type == int(omni.usd.StageEventType.CLOSED):
            self.on_closed()

    def build_ui(self):
        if self._window is None:
            self._cs = _contact_sensor.acquire_contact_sensor_interface()

            self._timeline = omni.timeline.get_timeline_interface()
            self.sub = _physx.get_physx_interface().subscribe_physics_step_events(self._on_update)

            self.leg_paths = ["/Ant/Arm_{:02d}/Lower_Arm".format(i + 1) for i in range(4)]
            self.sensor_ofsets = [
                carb.Float3(40, 0, 0),
                carb.Float3(40, 0, 0),
                carb.Float3(40, 0, 0),
                carb.Float3(40, 0, 0),
            ]

            self.shoulder_joints = ["/Ant/Arm_{:02d}/Upper_Arm/shoulder_joint".format(i + 1) for i in range(4)]

            self.lower_joints = ["{}/lower_arm_joint".format(i) for i in self.leg_paths]
            self._sensor_handles = [0 for i in range(4)]
            self.sliders = None
            self._window = ui.Window(
                title="Contact Sensor Sample", width=300, height=200, dockPreference=ui.DockPreference.LEFT_BOTTOM
            )
            self.sliders = []
            self.colors = [0xFFBBBBFF, 0xFFBBFFBB, 0xBBFFBBBB, 0xBBBBFFFF]
            style = {"background_color": 0xFF888888, "color": 0xFF333333, "secondary_color": self.colors[0]}
            with self._window.frame:
                with ui.VStack():
                    ui.Label("Sensor Readings (Newtons)")
                    for i in range(4):
                        with ui.HStack():
                            ui.Label("Arm {}".format(i + 1), width=0)
                            ui.Spacer(height=0, width=10)
                            style["secondary_color"] = self.colors[i]
                            self.sliders.append(ui.FloatDrag(min=0.0, max=15.0, step=0.001, style=style))
                            self.sliders[-1].enabled = False

            asyncio.ensure_future(self.create_scenario())

        self._window.visible = True

    def on_shutdown(self):
        self.on_closed()
        remove_menu_items(self._menu_items, "Isaac Examples")

    def on_closed(self):
        if self._window:
            self.sub = None
            self._timeline = None
            self._stage_event_subscription = None

        self._window = None

    def _on_update(self, dt):
        if self._timeline.is_playing() and self.sliders:
            for i, sensor in enumerate(self._sensor_handles):
                reading = self._cs.get_sensor_readings(sensor)
                # print(reading)
                if reading.shape[0]:
                    self.sliders[i].model.set_value(
                        float(reading[-1]["value"]) * self.meters_per_unit
                    )  # readings are in kg⋅m⋅s−2, converting to Newtons
                else:
                    self.sliders[i].model.set_value(0)

    async def create_scenario(self):

        # Add Contact Sensor
        await omni.usd.get_context().open_stage_async(self._extension_path + "/data/ant.usd")
        await omni.kit.app.get_app().next_update_async()

        self.meters_per_unit = UsdGeom.GetStageMetersPerUnit(omni.usd.get_context().get_stage())

        props = _contact_sensor.SensorProperties()
        props.radius = 12  # Cover the entire leg tip
        props.minThreshold = 0
        props.maxThreshold = 1000000000000
        props.sensorPeriod = 1 / 100.0

        for i in range(len(self.leg_paths)):
            props.position = self.sensor_ofsets[i]
            self._sensor_handles[i] = self._cs.add_sensor_on_body(self.leg_paths[i], props)

        self._events = omni.usd.get_context().get_stage_event_stream()
        self._stage_event_subscription = self._events.create_subscription_to_pop(
            self._on_stage_event, name="Contact Sensor Sample stage Watch"
        )
