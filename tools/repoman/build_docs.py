"""RepoMan command to build documentation with sphinx.

    Docs source is in "docs" folder. Results go into "_build/docs".
"""

import os
import sys
import argparse
import glob


import packmanapi
import repoman

repoman.bootstrap()
import omni.repo.man


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))


def main():
    platform_host = omni.repo.man.get_and_validate_host_platform(["windows-x86_64", "linux-x86_64"])

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", dest="config", required=False, default="debug")
    options = parser.parse_args()

    paths = omni.repo.man.get_repo_paths(ROOT_DIR)

    # Install sphinx
    sphinx_path = packmanapi.install("sphinx", "2.0.1-py3.5")["sphinx"]

    # Add extensions folder and sphinx folder (with sphinx) into PYTHONPATH
    path_to_extensions = f"{ROOT_DIR}/_build/{platform_host}/{options.config}/exts/"
    path_to_kit = f"{ROOT_DIR}/_build/target-deps/kit_sdk_{options.config}/_build/{platform_host}/{options.config}"
    all_exts = (
        list(glob.glob(f"{path_to_extensions}/*/"))
        + list(glob.glob(f"{path_to_kit}/exts/*/"))
        + list(glob.glob(f"{path_to_kit}/extsPhysics/*/"))
        + list(glob.glob(f"{path_to_kit}/extensions/extensions-bundled"))
        + list(glob.glob(f"{path_to_kit}/plugins/bindings-python"))
    )
    for t in all_exts:
        print(t)
    os.environ["PYTHONPATH"] += os.pathsep.join([sphinx_path] + all_exts)

    # To help find any shared libs that the extensions load:
    all_bindir = list(glob.glob(f"{path_to_extensions}/*/bin/{platform_host}/{options.config}/")) + list(
        glob.glob(f"{path_to_extensions}/*/omni/isaac/*/")
    )
    all_plugin_dirs = list(glob.glob(f"{path_to_kit}/plugins/")) + list(glob.glob(f"{path_to_kit}/plugins/*/"))

    if "LD_LIBRARY_PATH" in os.environ:
        os.environ["LD_LIBRARY_PATH"] += os.pathsep.join([sphinx_path] + all_bindir + all_plugin_dirs)
    else:
        os.environ["LD_LIBRARY_PATH"] = os.pathsep.join([sphinx_path] + all_bindir + all_plugin_dirs)

    # Run sphinx module. Use kit_sdk python runner, it already has properly PATH and PYTHONPATH set to enable importing of Kit SDK modules
    config_dir = paths["docs_src"]
    input_dir = ROOT_DIR
    output_dir = paths["docs_dst"]
    python_args = ["-m", "sphinx", "-c", config_dir, "-b", "html", input_dir, output_dir]
    python_exe = "python.bat" if platform_host == "windows-x86_64" else "python.sh"
    python_path = f"{ROOT_DIR}/tools/packman/{python_exe}"
    omni.repo.man.run_process([python_path] + python_args, exit_on_error=True)


if __name__ == "__main__":
    main()
