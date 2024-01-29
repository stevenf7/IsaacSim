import argparse
import os
from typing import Callable, Dict

from omni.repo.build import REPO_BUILD_DEFAULT_JOBS, load_settings_from_config, setup_vscode_env
from omni.repo.man import get_all_known_configs, get_and_validate_host_platform, get_repo_paths


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict) -> Callable:
    parser.description = "Generate vscode settings."
    parser.add_argument(
        "-c",
        "--config",
        dest="config",
        required=False,
        default="release",
        help="Package only specified config. (default: %(default)s)",
    )

    def run_repo_tool(options: Dict, config: Dict):
        # get config specific to repo build tool
        tool_config = config.get("repo_build", {})
        options.build_verbose = False
        options.jobs = REPO_BUILD_DEFAULT_JOBS
        options.compilation_cores = 1
        settings = load_settings_from_config(config, options)
        repo_folders = get_repo_paths()

        # configs = get_all_known_configs()
        platform_target = get_and_validate_host_platform(
            ["windows-x86_64", "linux-x86_64", "linux-aarch64", "macos-x86_64", "macos-aarch64"]
        )

        # get config specific to the isaac vscode generation tool
        vscode_config = config.get("repo_generate_vscode_settings", {})
        template_paths = vscode_config["template_paths"]
        output_paths = vscode_config["output_paths"]
        python_analysis_extra_mapping = vscode_config["python_analysis_extra_mapping"]

        if len(template_paths) != len(output_paths):
            print(f"length of template_paths {template_paths} must match output_paths {output_paths}")
            return False

        # generate all templates
        for input, output in zip(template_paths, output_paths):
            tool_config["vscode"]["settings_template_file"] = input
            # print(tool_config.get("vscode", {}).get("settings_template_file"))
            repo_folders["root"] = output.replace("${config}", options.config)
            vscode_folder = os.path.join(repo_folders["root"], ".vscode")

            if not os.path.exists(vscode_folder):
                os.makedirs(vscode_folder)

            # generate python env only
            settings.generate_python_setup_shell_script = True
            tool_config["vscode"]["write_python_paths_in_settings_json"] = False
            settings.vscode_python_env_postprocess_fn = None
            setup_vscode_env(
                repo_folders=repo_folders,
                platform_target=platform_target,
                configs=[options.config],
                settings=settings,
                tool_config=tool_config,
            )

            # generate vscode settings only
            settings.generate_python_setup_shell_script = False
            tool_config["vscode"]["write_python_paths_in_settings_json"] = True

            def append_analysis_paths(env_dict, platform_target, config):
                env_dict["PYTHONPATH"].extend(python_analysis_extra_mapping)
                return env_dict

            settings.vscode_python_env_postprocess_fn = append_analysis_paths
            setup_vscode_env(
                repo_folders=repo_folders,
                platform_target=platform_target,
                configs=[options.config],
                settings=settings,
                tool_config=tool_config,
            )

    return run_repo_tool
