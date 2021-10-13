# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np
import os
import yaml

import omni.client

from distributions import Distribution, Choice, Normal, Range, Uniform, Walk


class Parser:
    """ For parsing the input parameterization to Replicator. """

    def __init__(self, args):
        """ Construct Parser. Parse input file. """

        self.args = args
        self.default_group_name = "<default>"
        self.param_to_file_type = {
            "model": [".usd", ".usdz", ".usda", ".usdc"],
            "texture": [".png", ".jpg", ".jpeg"],
            "material": [".mdl"],
        }

        Distribution.input_mount = args.input_mount
        self.params = self.parse_input()

    def initialize_params(self, params):
        """ Evaluate parameter values in Python. """

        for key, val in params.items():
            if type(val) is dict:
                self.initialize_params(val)
            elif type(val) is str:
                try:
                    val = eval(val)
                    if type(val) is tuple:
                        val = np.array(val)
                    params[key] = val
                except ValueError as e:
                    raise e
                except Exception as e:
                    # TODO: handle exceptions clearer
                    pass

    def override_params(self, params):
        """ Override params with CLI args. """

        if self.args.output:
            params["output_dir"] = self.args.output
        if self.args.num_samples:
            params["num_samples"] = self.args.num_samples
        if self.args.no_overwrite:
            params["overwrite"] = False
        if self.args.input_mount:
            params["input_mount"] = self.args.input_mount
        if self.args.headless:
            params["headless"] = True
        if self.args.visualize_models:
            params["visualize_models"] = True

    def get_directory_elems(self, elem):
        """ Grab files in a potential Nucleus server directory. """

        elem_can_be_nucleus_dir = type(elem) is str and "." not in os.path.basename(elem) and elem.startswith("/")
        if elem_can_be_nucleus_dir:
            (_, directory_elems) = omni.client.list(self.nucleus_server + elem)
            return directory_elems
        else:
            return ()

    def process_directory(self, directory_elems, directory, key):
        """ Unpack a directory on Nucleus into a list of file paths. """

        processed_elems = []
        for directory_elem in directory_elems:
            directory_elem = os.path.join(directory, str(directory_elem.relative_path))

            file_type = directory_elem[directory_elem.rfind(".") :].lower()
            valid_file_types = self.param_to_file_type.get(key[key.rfind("_") + 1 :], [])
            if file_type in valid_file_types:
                processed_elem = os.path.join(directory, directory_elem)
                processed_elems.append(processed_elem)
            else:
                sub_directory_elems = self.get_directory_elems(directory_elem)
                if sub_directory_elems:
                    # Recurse on subdirectories
                    unpacked_elems = self.process_directory(sub_directory_elems, directory_elem, key)
                    processed_elems.extend(unpacked_elems)

        return processed_elems

    def unpack_directories_from_params(self, params):
        """ Unpack all potential Nucleus server directories refenced in the parameter values. """

        for key, val in params.items():
            if type(val) is dict:
                self.unpack_directories_from_params(val)
            elif key.startswith("obj") or key.startswith("light"):
                if type(val) is Choice or type(val) is Walk:
                    unpacked_elems = []
                    for elem in val.get_elems():
                        directory_elems = self.get_directory_elems(elem)
                        if directory_elems:
                            directory = elem
                            unpacked_elems.extend(self.process_directory(directory_elems, directory, key))
                        else:
                            unpacked_elems.append(elem)
                    params[key].set_elems(unpacked_elems)
                else:
                    directory_elems = self.get_directory_elems(val)
                    if directory_elems:
                        directory = directory = val
                        unpacked_elems = self.process_directory(directory_elems, directory, key)
                        val = Choice(unpacked_elems)
                        params[key] = val

    def parse_parameter_file(self, input_file, is_profile=False):
        """ Parse input parameter file. """

        # Determine parameter file path
        if input_file.startswith("/"):
            input_file = input_file
        elif input_file.startswith("~"):
            input_file = os.path.join(Distribution.input_mount, input_file)
        else:
            input_file = os.path.join(os.path.dirname(__file__), "../..", input_file)

        # Read parameter file
        with open(input_file, "r") as f:
            # TODO: add schema check
            params = yaml.load(f, Loader=yaml.FullLoader)

        # Initialize params
        self.initialize_params(params)

        # Process parameter groups
        params["groups"] = {}
        for key, value in list(params.items()):
            # Add group
            if type(value) is dict and key != "groups":
                if is_profile:
                    raise ValueError('Profile file "{}" cannot have a parameter group'.format(input_file))
                if key in params["groups"]:
                    raise ValueError("Parameter group name is not unique: {}".format(key))
                params["groups"][key] = value
                params.pop(key)

            # Add to default group
            if key.startswith("obj_") or key.startswith("light_"):
                if self.default_group_name not in params["groups"]:
                    params["groups"][self.default_group_name] = {}
                params["groups"][self.default_group_name][key] = value
                params.pop(key)

        # Add a parameter for the input file path
        params["input_file"] = input_file

        return params

    def parse_input(self):
        """ Parse all input parameter files. """

        # Parse input parameter file
        params = self.parse_parameter_file(self.args.input)
        input_file = params["input_file"]

        profile_files = []
        if "profiles" in params:
            # Pull params from parameter profile files
            parameters_path = params["input_file"][: params["input_file"].rfind("/")]
            for profile in params["profiles"]:

                if profile.startswith("/"):
                    profile_file = profile
                elif profile.startswith("~"):
                    profile_file = os.path.join(Distribution.input_mount, profile_file)
                else:
                    profile_file = os.path.join(parameters_path, profile)
                profile_files.append(profile_file)

        # Always add default profile as the lowest profile
        profile_files.append("parameters/profiles/default.yaml")

        all_profile_params = [self.parse_parameter_file(profile, is_profile=True) for profile in profile_files]

        # Union parameters from input file and profile file(s)
        all_profile_params = all_profile_params[::-1]
        final_profile_params = all_profile_params[0]
        for profile_params in all_profile_params:
            profile_params["groups"][self.default_group_name] = {
                **final_profile_params["groups"][self.default_group_name],
                **profile_params["groups"][self.default_group_name],
            }
            final_profile_params = {**final_profile_params, **profile_params}

        for group in params["groups"]:
            params["groups"][group] = {
                **final_profile_params["groups"][self.default_group_name],
                **params["groups"][group],
            }
        params = {**final_profile_params, **params}

        # Overwrite file params, as needed
        params["input_file"] = input_file
        params["profile_files"] = [profile_params["input_file"] for profile_params in all_profile_params]

        # Set nucleus server
        self.nucleus_server = params["nucleus_server"]

        # Unpack directory elems
        self.unpack_directories_from_params(params)

        # Override final parameter set with CLI arg parameters
        self.override_params(params)

        return params

    def get_params(self):
        return self.params
