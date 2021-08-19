import os
import json

import carb


class BenchmarkConfigUtility:
    def __init__(self, mg_extension_path, benchmark_extension_path):
        """
        default_policy_map maps human-readable names for motion policies/robots to the appropriate directory 
        in the motion_generation extension containing a config.json file with default parameters for the policy
        on that robot
        """

        self._default_policy_config_dir = os.path.join(mg_extension_path, "policy_configs")
        with open(os.path.join(self._default_policy_config_dir, "policy_map.json")) as policy_map:
            self._default_policy_map = json.load(policy_map)

        """
        The robot_benchmark extension has three types of config files in it
        robot_configs: points to assets necessary to load a robot in Sim (path to USD file)
        environment_configs: configs for individual robot/environment combinations
            Any unspecified parameters will have their default values loaded
        policy_configs: config files to override the default config for a given robot/policy combination
          policy_configs are specific to a robot/policy/environment combination

        benchmark_config_map.json contains a mapping of human-readable environment/policy/robot names to
        their associated config files
        """
        self._benchmark_config_dir = os.path.join(benchmark_extension_path, "benchmark_config")
        with open(os.path.join(self._benchmark_config_dir, "benchmark_config_map.json")) as benchmark_config_map:
            self._benchmark_config_map = json.load(benchmark_config_map)

    def get_robot_options(self, robot_exclusion_list=[]):
        """
        Given the environment, return a list of the robots that have at least one 
        motion policy configured in the motion_generation extension, and are not explicitly excluded for this
        environment
        """
        all_robot_options = self._default_policy_map.keys()

        robot_options = []
        for op in all_robot_options:
            if op not in robot_exclusion_list:
                robot_options.append(op)

        return robot_options

    def get_motion_policy_options(self, robot_name, policy_exclusion_list=[]):
        """
        Given the robot selected, return the motion policies that have default configs
        for the robot in the motion_generation extension
        """

        all_policy_options = self._default_policy_map[robot_name].keys()
        policy_options = [pol for pol in all_policy_options if pol not in policy_exclusion_list]
        return policy_options

    def _process_policy_config(self, mp_config_file):
        """
            `mp_config_file` is expected to be an absolute path to a json file
            which provides configuration for the "MotionPolicy" being tested.
            A dictionary called "config" is created from reading this file

            Inside "config", relative paths included in "relative_asset_paths" will
            be prepended with the directory containing mp_config_file to convert to an absolute path.

            For example, if "config" constains:

            {
                "policy_type" : "RMP_Flow",
                "end_effector_frame_name": "tool",
                "relative_asset_paths": {
                    "robot_description_path" : "ur10_robot_description.yaml",
            }

            and mp_config_file is in the "path/to/config/" directory, then "config" will be converted to:

            {
                "policy_type" : "RMPflow",
                "end_effector_frame_name": "tool",
                "robot_description_path" : "/path/to/config/ur10_robot_description.yaml",
                "relative_asset_paths": {
                    "robot_description_path" : "ur10_robot_description.yaml",
                }
            }
        """

        if not os.path.exists(mp_config_file):
            carb.log_error("MotionPolicy config file does not exist at ", mp_config_file)
        mp_config_dir = os.path.dirname(mp_config_file)  # path to directory containing mp_config_file

        with open(mp_config_file) as config_file:
            config = json.load(config_file)

        rel_assets = config.get("relative_asset_paths", {})
        for k, v in rel_assets.items():
            config[k] = os.path.join(mp_config_dir, v)

        return config

    def get_default_policy_config(self, robot_name, policy_name):
        """ 
        load the default policy config for this robot from the motion_generation extension
        """

        local_policy_path = self._default_policy_map[robot_name][policy_name]

        default_policy_config_path = os.path.join(self._default_policy_config_dir, local_policy_path)

        return self._process_policy_config(default_policy_config_path)

    def overwrite_default_policy_config(self, env_name, robot_name, policy_name, default_policy_config):
        """
        get policy config for the selected robot in the selected environment
        
        If there is no path specified to a config gile for the specific robot/environment/policy combination,
        then the default policy config for this robot/policy combination will remain unchanged

        If there is an invalid path specified, it will be interpretted as an error.
        """

        local_policy_config_path = (
            self._benchmark_config_map.get(robot_name, {})
            .get("policy_config_paths", {})
            .get(env_name, {})
            .get(policy_name, None)
        )
        if local_policy_config_path is None:
            return default_policy_config

        overwriting_policy_config_path = os.path.join(self._benchmark_config_dir, local_policy_config_path)

        config = self._process_policy_config(overwriting_policy_config_path)
        for k, v in config.items():
            default_policy_config[k] = v

        return default_policy_config

    def get_environment_params(self, env_name, robot_name):
        """
        Load the json config file for this environment/robot combination and return a dictionary that 
        will act as **kwargs for the environment initialization.

        If there is no path specified to a config file for the specific robot/environment combination,
        an empty dictionary will be returned and the default params will be used in the environment

        If there is an invalid path specified, it will be interpretted as an error.
        """
        local_env_config_path = (
            self._benchmark_config_map.get(robot_name, {}).get("environment_config_paths", {}).get(env_name, None)
        )
        if local_env_config_path is None:
            return {}

        env_config_path = os.path.join(self._benchmark_config_dir, local_env_config_path)

        if os.path.exists(env_config_path):
            with open(env_config_path) as env_file:
                config = json.load(env_file)
        else:
            carb.log_error(
                "Invalid path to config file specified in benchmark_config_map.json for the "
                + robot_name
                + " in the "
                + env_name
                + "environment"
            )
            config = {}

        return config

    def get_robot_assets(self, robot_name):
        """
        Load robot_assets.json for the selected robot.
        robot_assets.json contains information necessary to load the robot into Sim
        (excluding the motion_generation policy config).  This currently only includes 
        the path to the robot's USD file.

        If there is not a valid path to robot_assets.json specified in benchmark_config_map.json,
        an error will be thrown.
        """
        local_robot_assets_path = self._benchmark_config_map.get(robot_name, {}).get("robot_assets_path", None)
        if local_robot_assets_path is None:
            carb.log_error("Path to robot_assets is not specified in benchmark_config_map.json for " + robot_name)
            return {}

        robot_assets_path = os.path.join(self._benchmark_config_dir, local_robot_assets_path)

        if os.path.exists(robot_assets_path):
            with open(robot_assets_path) as robot_assets_file:
                robot_assets = json.load(robot_assets_file)
        else:
            carb.log_error("Invalid path to robot_assets specified in benchmark_config_map.json for " + robot_name)
            robot_assets = {}

        return robot_assets
