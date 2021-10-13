# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np
import os
from PIL import Image, ImageFont, ImageDraw
import sys

from generator import Generator
from distributions.choice import Choice
from distributions.walk import Walk
from sampling import Sampler


class Visualizer:
    """ For generating visuals of each input object model in the input parameterization. """

    def __init__(self, parser, params, output_dir):
        """ Construct Visualizer. Parameterize Replicator to output necessary data to process into visuals. """

        self.parser = parser
        self.params = params
        self.output_dir = os.path.join(output_dir, "visuals")
        os.makedirs(self.output_dir, exist_ok=True)

        self.tile_width = 500
        self.tile_height = 500
        self.obj_size = 100
        self.room_size = 5 * self.obj_size
        self.cam_distance = 1.8 * self.obj_size
        self.background_color = (100, 150, 175)
        self.group_name = parser.default_group_name

        # Get object models from input parameter files
        self.obj_models = self.get_all_obj_models()

        # Copy model list to output file
        model_list = os.path.join(self.output_dir, "models.txt")
        with open(model_list, "w") as f:
            for obj_model in self.obj_models:
                f.write(obj_model)
                f.write("\n")

        # Filter obj models
        if not self.params["overwrite"]:
            self.filter_obj_models(self.obj_models)

        # Set parameters to default
        parser.args.input = "parameters/profiles/default.yaml"
        self.params = parser.parse_input()

        # Override parameters
        self.set_obj_parameters()
        self.set_light_parameters()
        self.set_room_parameters()
        self.set_cam_parameters()
        self.set_other_parameters()

        # Set parameters
        Sampler.params = self.params

        # Initiate Replicator
        self.generator = Generator(self.params, 0, self.output_dir)

    def visualize_models(self):
        """ Generate samples and post-process captured data into visuals. """

        num_models = len(self.obj_models)
        for i, obj_model in enumerate(self.obj_models):
            print("Sample {}/{} - visualizing: {}".format(i, num_models, obj_model))

            self.set_obj_model(obj_model)

            # Capture 4 angles per model
            outputs = [self.generator.generate_sample() for j in range(4)]
            image_matrix = self.process_outputs(outputs)
            self.save_visual(obj_model, image_matrix)

    def get_all_obj_models(self):
        """ Get all object models from input parameterization. """

        obj_models = []
        groups = self.params["groups"]
        for group_name, group in groups.items():
            group_models = group["obj_model"]
            if group_models:
                if type(group_models) is Choice or type(group_models) is Walk:
                    group_models = group_models.get_elems()
                else:
                    group_models = [group_models]

                obj_models.extend(group_models)

        return obj_models

    def filter_obj_models(self, obj_models):
        """ Filter out obj models that have already been visualized. """

        existing_filenames = set([f for f in os.listdir(self.output_dir)])

        for obj_model in obj_models:
            filename = self.model_to_filename(obj_model)
            if filename not in existing_filenames:
                obj_models.remove(obj_model)

        if not obj_models:
            print("all obj models visuals have been already created.")
            sys.exit()

    def model_to_filename(self, obj_model):
        """ Map obj_model Nucleus path to a filename. """

        filename = obj_model.replace("/", "__")
        r_index = filename.rfind(".")
        filename = filename[:r_index]
        filename += ".jpg"
        return filename

    def process_outputs(self, outputs):
        """ Tile output data from scene into one image matrix. """

        rgbs = [groundtruth["DATA"]["RGB"] for groundtruth in outputs]
        depths = [groundtruth["DATA"]["DEPTH"] for groundtruth in outputs]
        wireframes = [groundtruth["DATA"]["WIREFRAME"] for groundtruth in outputs]

        rgbs = [rgb[:, :, :3] for rgb in rgbs]
        top_row_matrix = np.concatenate(rgbs, axis=1)

        depths = [np.stack((depth,) * 3, axis=-1) for depth in depths[:2]]
        wireframes = [wireframe[:, :, :3] for wireframe in wireframes[:2]]
        bottom_row_matrix = np.concatenate(depths + wireframes, axis=1)

        image_matrix = np.concatenate([top_row_matrix, bottom_row_matrix], axis=0)
        image_matrix = np.array(image_matrix, dtype=np.uint8)

        return image_matrix

    def save_visual(self, obj_model, image_matrix):
        """ Save image matrix as image. """

        image = Image.fromarray(image_matrix, "RGB")

        font_path = os.path.join(os.path.dirname(__file__), "RobotoMono-Regular.ttf")
        font = ImageFont.truetype(font_path, 18)

        draw = ImageDraw.Draw(image)
        width, height = image.size
        draw.text((10, int(0.96 * height)), "model name: {}".format(obj_model), font=font)

        model_name = self.model_to_filename(obj_model)
        filename = os.path.join(self.output_dir, model_name)
        image.save(filename, "JPEG", quality=85)

    def set_cam_parameters(self):
        """ Set camera parameters. """

        self.params["camera_coord_x"] = -self.cam_distance
        self.params["camera_coord_y"] = 0
        self.params["camera_coord_z"] = self.room_size / 2
        self.params["camera_rot_x"] = 0
        self.params["camera_rot_y"] = 0
        self.params["camera_rot_z"] = 0
        self.params["focal_length"] = 30

    def set_room_parameters(self):
        """ Set room parameters. """

        self.params["generate_room"] = True
        self.params["scenario_model"] = None

        self.params["floor_size"] = self.room_size
        self.params["wall_height"] = self.room_size

        self.params["floor_color"] = np.array(self.background_color)
        self.params["floor_material"] = None
        self.params["wall_color"] = np.array(self.background_color)
        self.params["wall_reflectance"] = 0
        self.params["ceiling_color"] = np.array(self.background_color)
        self.params["ceiling_reflectance"] = 0

    def set_obj_parameters(self):
        """ Set object parameters. """

        group = self.params["groups"][self.group_name]
        group["obj_coord_sensor_relative"] = False
        group["obj_rot_sensor_relative"] = False
        group["obj_coord_x"] = 0
        group["obj_coord_y"] = 0
        group["obj_coord_z"] = self.room_size / 2
        group["obj_rot_x"] = Walk([0, 90, 180, 270])
        group["obj_rot_y"] = 0
        group["obj_rot_z"] = 0
        group["obj_size_enabled"] = True
        group["obj_size"] = self.obj_size
        group["obj_count"] = 1

    def set_light_parameters(self):
        """ Set light parameters. """

        group = self.params["groups"][self.group_name]
        group["light_count"] = 1
        group["light_coord_sensor_relative"] = True
        group["light_rot_sensor_relative"] = False
        group["light_horiz_fov_loc"] = 0
        group["light_vert_fov_loc"] = 0
        group["light_distance"] = -100
        group["light_intensity"] = 300000
        group["light_radius"] = 20
        group["light_color"] = np.array([200, 200, 200])

    def set_other_parameters(self):
        """ Set other parameters. """

        self.params["img_width"] = self.tile_width
        self.params["img_height"] = self.tile_height
        self.params["write_data"] = False
        self.params["verbose"] = False
        self.params["stereo"] = False
        self.params["rgb"] = True
        self.params["depth"] = True
        self.params["wireframe"] = True

        self.params["nap"] = False
        self.params["pause"] = 2
        self.params["headless"] = False

    def set_obj_model(self, obj_model):
        """ Set obj_model parameter. """

        group = self.params["groups"][self.group_name]
        group["obj_model"] = obj_model
