from typing import Dict, Callable
import os, argparse


from omni.repo.build import setup_vscode_env, load_settings_from_config
from omni.repo.man import get_and_validate_host_platform, get_repo_paths, get_all_known_configs


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
        tool_config = config.get("repo_build", {})
        vscode_config = config.get("repo_generate_vscode_settings", {})
        template_paths = vscode_config["template_paths"]
        output_paths = vscode_config["output_paths"]
        if len(template_paths) != len(output_paths):
            print(f"length of template_paths {template_paths} must match output_paths {output_paths}")
            return False
        for input, output in zip(template_paths, output_paths):
            settings = load_settings_from_config(config)
            repo_folders = get_repo_paths()
            configs = get_all_known_configs()
            platform_target = get_and_validate_host_platform(
                ["windows-x86_64", "linux-x86_64", "linux-aarch64", "macos-x86_64", "macos-aarch64"]
            )
            tool_config["vscode"]["settings_template_file"] = input
            tool_config["vscode"]["write_python_paths_in_settings_json"] = True
            # print(tool_config.get("vscode", {}).get("settings_template_file"))
            repo_folders["root"] = output.replace("${config}", options.config)
            vscode_folder = os.path.join(repo_folders["root"], ".vscode")

            if not os.path.exists(vscode_folder):
                os.makedirs(vscode_folder)
            setup_vscode_env(
                repo_folders=repo_folders,
                platform_target=platform_target,
                configs=[options.config],
                settings=settings,
                tool_config=tool_config,
            )

    return run_repo_tool
