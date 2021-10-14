# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import asyncio
import numpy as np
import time

from output import Logger
from sampling import Sampler
from scene import Room, Object, Light


class SceneManager:
    """ For managing scene set-up and generation. """

    def __init__(self, sim_app, sim_context):
        """ Construct SceneManager. Set-up scenario in Isaac Sim. """

        import omni

        self.sim_app = sim_app
        self.sim_context = sim_context

        self.stage = omni.usd.get_context().get_stage()

        self.sample = Sampler().sample
        self.setup_scenario()

        # TODO: parameterize these variables
        self.model_substr_to_label = {"floor": "floor"}
        self.catch_all_label = "obstacle"

        self.play_frame = False
        self.objs = []
        self.lights = []

    def setup_scenario(self):
        """ Load in base scenario(s) """

        import omni
        from omni.isaac.core.utils import prims
        from omni.isaac.utils.scripts import scene_utils

        # Define world prim
        prims.create_prim(self.stage, "/World", "Xform")

        # Set scene units
        omni.kit.commands.execute(
            "ChangeSetting",
            path="/persistent/simulation/defaultMetersPerUnit",
            value=self.sample("meters_per_scene_unit"),
            prev=0,
        )

        # Load in a USD scenario, if needed
        self.load_scenario_model()

        # Generate a parameterizable room, if needed
        self.room = None
        if self.sample("generate_room"):
            self.room = Room(self.sim_app, self.sim_context)
            self.room.generate()

        self.stage = omni.usd.get_context().get_stage()

        # Set up axis to z axis
        scene_utils.set_up_z_axis(self.stage)

    def load_scenario_model(self):
        """ Load in a USD scenario. """

        import omni

        # TODO: add multiples scenario support

        # Load in base scenario from Nucleus
        if self.sample("scenario_model"):

            async def load_stage(path):
                await omni.usd.get_context().open_stage_async(path)

            scenario_ref = self.sample("nucleus_server") + self.sample("scenario_model")
            setup_task = asyncio.ensure_future(load_stage(scenario_ref))
            while not setup_task.done():
                self.sim_context.render()

    def populate_scene(self, cam_data):
        """ Populate a sample's scene, given a camera pose, with objects and lights. """

        # Iterate through each group
        self.objs = []
        self.lights = []
        for group in self.sample("groups"):
            # Spawn objects
            num_objs = self.sample("obj_count", group=group)
            for i in range(num_objs):
                path = "/World/Sample/Objects/object_{}".format(len(self.objs))
                ref = self.sample("nucleus_server") + self.sample("obj_model", group=group)
                obj = Object(self.sim_app, self.sim_context, ref, path, cam_data, group)
                obj.place_in_scene()
                obj.add_physics()
                self.objs.append(obj)

            # Spawn lights
            num_lights = self.sample("light_count", group=group)
            for i in range(num_lights):
                path = "/World/Sample/Lights/lights_{}".format(len(self.lights))
                light = Light(self.sim_app, self.sim_context, path, cam_data, group)
                light.place_in_scene()
                self.lights.append(light)

        # Update room
        if self.room:
            self.room.update()

    def update_scene(self):
        """ Update Omniverse after scene is generated. """

        # Update class labels
        self.update_class_labels()

        # Wait for scene to finish loading
        while self.sim_app.is_stage_loading():
            self.sim_context.render()

        # Determine if scene is played
        scene_assets = self.objs + self.lights
        self.play_frame = any([asset.physics for asset in scene_assets])

        # Play scene, if needed
        if self.play_frame:
            print("physically simulating...")
            self.sim_context.play()
            frame = 0
            frame_time = 1 / 60
            frame_count = self.sample("physics_simulate_time") / frame_time
            while frame < frame_count or self.sim_app.is_stage_loading():
                self.sim_context.step(frame_time)
                frame = frame + 1
        else:
            self.sim_context.stop()

        # Napping
        if self.sample("nap"):
            print("napping")
            while True:
                self.sim_context.render()

        # Pausing
        start_time = time.time()
        pause_time = self.sample("pause") + 0.01
        while time.time() - start_time < pause_time:
            self.sim_context.render()

    def update_class_labels(self):
        """ Update class labels of every object."""

        from pxr import Semantics

        for prim in self.stage.Traverse():
            if not prim.HasAPI(Semantics.SemanticsAPI):
                sem = Semantics.SemanticsAPI.Apply(prim, "Semantics")
                sem.CreateSemanticTypeAttr()
                sem.CreateSemanticDataAttr()
            else:
                sem = Semantics.SemanticsAPI.Get(prim, "Semantics")
                continue

            dataAttr = sem.GetSemanticDataAttr()
            for model_substr, label in self.model_substr_to_label.items():
                if model_substr in prim.GetPath().pathString.lower():
                    dataAttr.Set(label)
                    continue
            dataAttr.Set(self.catch_all_label)

    def prepare_scene(self, index):
        """ Scene preparation step. """

        self.valid_sample = True
        Logger.start_log_item(index)
        Logger.print("Sample: " + str(index) + "\n")

    def finish_scene(self):
        """ Scene finish step. Clean-up variables, Isaac Sim stage. """

        from pxr import Sdf

        self.objs = []
        self.lights = []
        self.stage.RemovePrim(Sdf.Path("/World/Sample"))
        self.stage.RemovePrim(Sdf.Path("/Looks"))
        self.sim_context.stop()
        self.play_frame = False
        Logger.finish_log_item()

    def is_given(param):
        """ If a parameter is given. """

        if type(param) is np.ndarray:
            return True
        else:
            return param != None
