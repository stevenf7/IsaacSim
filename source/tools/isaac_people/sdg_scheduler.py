# Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from multiprocessing import Process

from omni.isaac.kit import SimulationApp

CONFIG = {"renderer": "RayTracedLighting", "headless": True, "width": 1920, "height": 1080}
import argparse
import glob
import os
import re

"""
Standalone script to schedule people sdg jobs in a local env.
"""


class PeopleSDG:
    def __init__(self, num_runs, sim_app):
        self.num_runs = num_runs
        self.config_dict = None
        self._sim_manager = None
        self._data_generator = None
        self._settings = None
        self._sim_app = sim_app

    def set_config(self, config_file):
        import carb
        from omni.replicator.character.core.data_generation import DataGeneration
        from omni.replicator.character.core.simulation import SimulationManager

        self._sim_manager = SimulationManager()
        self.config_dict, is_modified = self._sim_manager.load_config_file(config_file)
        if not self.config_dict:
            carb.log_error("Loading config file ({0}) fails. Data generation will not start.".format(config_file))
            return

        try:
            folder_path = self.config_dict["replicator"]["parameters"]["output_dir"]
            self.config_dict["replicator"]["parameters"]["output_dir"] = PeopleSDG._get_output_folder_by_index(
                folder_path, index=self.num_runs
            )
        except:
            carb.log_warn("'output_dir' does not exists in config file. Will not auto increase output path")

        data_generation_config = {}
        data_generation_config["writer_name"] = self.config_dict["replicator"]["writer"]
        data_generation_config["num_cameras"] = self.config_dict["global"]["camera_num"]
        data_generation_config["num_lidars"] = self.config_dict["global"]["lidar_num"]
        data_generation_config["num_frames"] = self.config_dict["global"]["simulation_length"] * 30
        data_generation_config["writer_params"] = self.config_dict["replicator"]["parameters"]
        self._data_generator = DataGeneration(data_generation_config)

    def set_simulation_settings(self):
        import carb
        import omni.replicator.core as rep

        rep.settings.carb_settings("/omni/replicator/backend/writeThreads", 16)
        self._settings = carb.settings.get_settings()
        self._settings.set("/rtx/rtxsensor/coordinateFrameQuaternion", "0.5,-0.5,-0.5,-0.5")
        self._settings.set("/app/scripting/ignoreWarningDialog", True)
        self._settings.set("/persistent/exts/omni.anim.navigation.core/navMesh/viewNavMesh", False)
        self._settings.set("/exts/omni.anim.people/navigation_settings/navmesh_enabled", True)
        self._settings.set(
            "/exts/omni.replicator.character/default_robot_command_file_path", "default_robot_command.txt"
        )
        self._settings.set("/persistent/exts/omni.replicator.character/aim_camera_to_character", True)
        self._settings.set("/persistent/exts/omni.replicator.character/min_camera_distance", 6.5)
        self._settings.set("/persistent/exts/omni.replicator.character/max_camera_distance", 14.5)
        self._settings.set("/persistent/exts/omni.replicator.character/max_camera_look_down_angle", 60)
        self._settings.set("/persistent/exts/omni.replicator.character/min_camera_look_down_angle", 0)
        self._settings.set("/persistent/exts/omni.replicator.character/min_camera_height", 2)
        self._settings.set("/persistent/exts/omni.replicator.character/max_camera_height", 3)
        self._settings.set("/persistent/exts/omni.replicator.character/character_focus_height", 0.7)
        self._settings.set("/persistent/exts/omni.replicator.character/frame_write_interval", 10)

    def save_commands_to_file(self, file_path, commands):
        from omni.replicator.character.core.file_util import TextFileUtil

        command_str = ""
        for cmd in commands:
            command_str += cmd
            command_str += "\n"
        result = TextFileUtil.write_text_file(file_path, command_str)
        return result

    def generate_data(self, config_file):
        import carb
        from omni.isaac.core.utils.stage import open_stage

        # Set simulation settings
        self.set_simulation_settings()

        # Load from config file
        self.set_config(config_file)

        # Open stage with blocking call
        stage_open_result = open_stage(self.config_dict["scene"]["asset_path"])

        if not stage_open_result:
            carb.log_error("Unable to open stage {}".format(self.config_dict["scene"]["asset_path"]))
            self._sim_app.close()

        self._sim_app.update()

        # Create character and cameras
        self._sim_manager.load_agents_cameras_from_config_file()
        self._sim_app.update()

        # Create random character actions (when character section exists)
        if "character" in self.config_dict:
            commands = self._sim_manager.generate_random_commands()
            # Write commands to file
            self.save_commands_to_file(self.config_dict["character"]["command_file"], commands)
            self._sim_app.update()

        # Run data generation
        self._data_generator._init_recorder()
        self._data_generator.run_until_complete()
        self._sim_app.update()

        # Clear State after completion
        self._data_generator._clear_recorder()
        self._sim_app.update()
        self._sim_app.close()

    def _get_output_folder_by_index(path, index):
        """
        Get the next output_folder following naming convention '_d' where d is digit string.
        If file name dose not follow naming convention, append '_d' at the end.
        """
        if index == 0:
            return path
        m = re.search(r"_\d+$", path)
        if m:
            cur_index = int(m.group()[1:])
            if cur_index:
                index = cur_index + index
                path = path[: m.start()]
        return path + "_" + str(index)


def enable_extensions():
    # Enable extensions
    from omni.isaac.core.utils.extensions import enable_extension

    enable_extension("omni.kit.window.viewport")
    enable_extension("omni.kit.manipulator.prim")
    enable_extension("omni.kit.property.usd")
    enable_extension("omni.anim.navigation.bundle")
    enable_extension("omni.anim.timeline")
    enable_extension("omni.anim.graph.bundle")
    enable_extension("omni.anim.graph.core")
    enable_extension("omni.anim.graph.ui")
    enable_extension("omni.anim.retarget.bundle")
    enable_extension("omni.anim.retarget.core")
    enable_extension("omni.anim.retarget.ui")
    enable_extension("omni.kit.scripting")
    enable_extension("omni.anim.people")
    enable_extension("omni.replicator.character.core")
    enable_extension("omni.kit.mesh.raycast")


def launch_data_generation(num_runs, config_file):

    # Initalize kit app
    kit = SimulationApp(launch_config=CONFIG)

    # Enable extensions
    enable_extensions()
    kit.update()

    # Load modules from extensions
    import carb
    import omni.kit.loop._loop as omni_loop

    loop_runner = omni_loop.acquire_loop_interface()
    loop_runner.set_manual_step_size(1.0 / 30.0)
    loop_runner.set_manual_mode(True)
    carb.settings.get_settings().set("/app/player/useFixedTimeStepping", False)

    # set config app
    sdg = PeopleSDG(num_runs, kit)
    sdg.generate_data(config_file)


def get_args():
    parser = argparse.ArgumentParser("People SDG")
    parser.add_argument("-c", "--config_file", required=True, help="Path to config file or a folder of config files")
    parser.add_argument(
        "-n",
        "--num_runs",
        required=False,
        type=int,
        nargs="?",
        default=1,
        const=1,
        help="Number or run. After each run, the output path index will increase. If not provided, the default run is 1.",
    )
    args, _ = parser.parse_known_args()
    return args


def main():
    args = get_args()
    config_path = args.config_file
    num_runs = args.num_runs
    files = []

    # Check for config file or folder
    if os.path.isdir(config_path):
        files = glob.glob("{}/*.yaml".format(config_path))
    elif os.path.isfile(config_path):
        files.append(config_path)
    else:
        print("Invalid config path passed. Path must be a file or a folder containing config files.")
    print("Total SDG jobs - {}".format(len(files)))

    # Launch jobs
    for run in range(num_runs):
        for idx, config_file in enumerate(files):
            print("{} round: Starting SDG job number - {} with config file {}".format(run, idx, config_file))
            p = Process(
                target=launch_data_generation,
                args=(
                    run,
                    config_file,
                ),
            )
            p.start()
            p.join()


if __name__ == "__main__":
    main()
