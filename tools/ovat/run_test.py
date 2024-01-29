# Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import os
import platform
import re
import socket
import ssl
import subprocess
import sys
import time
from argparse import ArgumentParser
from pathlib import Path
from urllib.request import HTTPSHandler, build_opener, install_opener, urlretrieve
from zipfile import ZipFile

import pkg_resources
from setuptools._vendor.packaging import version

# Bump this before you tag :)
VERSION = "3.0.0"
# Flag to understad if we are on windows or not
IS_WINDOWS = os.name == "nt"
# User home folder
USER_HOME = Path(os.getenv("USERPROFILE" if IS_WINDOWS else "HOME"))
# Minimum pip version required.
MIN_PIP_VERSION = version.parse("20.2")
PERFLAB_PYPI = "https://pypi.perflab.nvidia.com/simple"

VENV_DIR = Path.cwd() / "_venv"
# The requirements.txt is a sibling of this file
REQUIRED_TOOLS = Path(__file__).parent.resolve() / "requirements.txt"
# We try to resolve these domain names to verify vpn access
HOSTNAMES_RESOLVE = ("pypi.perflab.nvidia.com", "nv.nvidia.com", "ru-mow.nstorage.nvidia.com")
# Error message when gcn.yml is missing
GCN_MISSING = """gcn.yml file not found.
Learn how to build one here: https://nv/ovat/docs/userguide/hello_world/#executing-locally-on-gcn"""
# Error message when ovat_test.toml is missing
OVAT_TEST_MISSING = """ovat_test.toml file not found.
Learn how to build one here: https://nv/ovat/docs/"""


def setup_ssl():
    """Install a default SSL handler that does not verify certificates"""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    install_opener(build_opener(HTTPSHandler(context=context)))


def parse_cli_arguments() -> object:
    parser = ArgumentParser(description=f"OVAT run test/bootstrapper v{VERSION}")
    parser.add_argument("-d", "--debug", help="Use debug mode instead of release", action="store_true")
    parser.add_argument(
        "-i", "--init-only", help="Initialize environment only. No tests will run.", action="store_true"
    )
    parser.add_argument(
        "-m", "--mode", help="Specific mode, by default release ", default="release", action="store_true"
    )
    return parser.parse_args()


def check_required_files() -> bool:
    cwd = Path.cwd()
    print(f"Checking current directory for required files ({cwd})")

    if not (cwd / "gcn.yml").exists():
        print(GCN_MISSING)
        return False

    if not (cwd / "ovat_test.toml").exists():
        print(OVAT_TEST_MISSING)
        return False
    return True


def check_network_access() -> bool:
    for hostname in HOSTNAMES_RESOLVE:
        try:
            print(f"Checking if we can resolve: {hostname}")
            socket.gethostbyname(hostname)
        except socket.gaierror:
            print(f"Cannot resolve {hostname}")
            return False
    return True


def parse_requirements(requirements: str) -> list:
    requirements = re.sub(r"^(--|#).*$", "", requirements, flags=re.M)
    parsed = pkg_resources.parse_requirements(requirements)
    requirements = {}
    for item in parsed:
        name = item.name
        parsed_version = None if len(item.specs) == 0 else version.parse(item.specs[0][1])
        requirements[name] = (parsed_version, item)
    return requirements


def ensure_packages():
    # pip first
    run_pip = [sys.executable, "-m", "pip"]
    pip_version_output = subprocess.check_output(run_pip + ["-V"]).decode("utf-8")
    upgrade_pip = True
    if pip_version_output.startswith("pip "):
        pip_version = version.parse(pip_version_output.split(" ")[1])
        if pip_version >= MIN_PIP_VERSION:
            upgrade_pip = False
    if upgrade_pip:
        print("Upgrading pip")
        subprocess.run(run_pip + ["install", "-U", "pip"])

    # pip setup
    try:
        current_global_index = (
            subprocess.check_output(
                run_pip + ["config", "get", "--site", "global.extra-index-url"], stderr=subprocess.DEVNULL
            )
            .decode("utf-8")
            .strip()
        )
    except subprocess.CalledProcessError:
        current_global_index = ""
    if current_global_index != PERFLAB_PYPI:
        subprocess.run(run_pip + ["config", "set", "--site", "global.extra-index-url", PERFLAB_PYPI])

    # packages
    reqs = subprocess.check_output([sys.executable, "-m", "pip", "freeze"]).decode("utf-8")
    installed = parse_requirements(reqs)

    with open(REQUIRED_TOOLS, "r") as tools_file:
        required_packages = parse_requirements(tools_file.read())

    to_install = []
    for req_name, (min_version, item) in required_packages.items():
        if req_name not in installed:
            to_install.append(str(item))
            continue
        installed_version, _ = installed[req_name]
        if min_version and installed_version < min_version:
            to_install.append(str(item))

    if len(to_install) > 0:
        print(f"Installing packages: {to_install}")
        subprocess.run([sys.executable, "-m", "pip", "install"] + to_install)

    print("Python packages ready.")


def download_gcn_windows(destination: Path):
    filename, headers = urlretrieve("http://nv/ovat/gcn/windows")
    with ZipFile(filename, "r") as zip_file:
        zip_file.extractall(destination)


def ensure_gcn_daemon_windows():
    gcn_home = USER_HOME / ".ovat" / "GCN"
    gcn_command = gcn_home / "Daemon" / "gcn.cmd"

    if not gcn_command.exists():
        print("No GCN daemon found. Downloading one...")
        download_gcn_windows(gcn_home.parent)

    print(f"GCN Daemon available at: {gcn_home}")
    # This is available after installing
    import psutil

    found = False
    for proc in psutil.process_iter(["cmdline"]):
        if proc.name() != "python.exe":
            continue
        cmdline = proc.info["cmdline"]
        if len(cmdline) > 2 and cmdline[2] == "gcn.core.node_master":
            found = True
    if not found:
        print("GCN daemon not running. Starting")
        os.system(f"start {gcn_command}")
        time.sleep(6)
    else:
        print("GCN daemon already running!")


def ensure_gcn_daemon():
    if IS_WINDOWS:
        ensure_gcn_daemon_windows()
    else:
        raise RuntimeError("Only windows gcn supported for now")


def run_gcn_test(mode: str) -> int:
    subprocess.run(["ovat", "dev", "create", "-m", mode])

    ovat_ouputs_re = re.compile(r".*__OVAT_OUTPUTS_JSON.txt.*gtl:\/\/file\/([0-9A-Z-]+)", re.M)
    args = f"gcn_cli run --node {platform.node()} .\\gcn_local.yml".split(" ")
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, universal_newlines=True, bufsize=1)
    outputs_file = None
    while proc.poll() is None:
        out = proc.stdout.readline()
        sys.stdout.write(out)
        match = ovat_ouputs_re.search(out)
        if match is not None:
            outputs_file = match[1]

    if outputs_file is not None:
        subprocess.run(["ovat", "jobs", "fetch-file", outputs_file])

    return proc.returncode


def cli() -> int:
    """Command line functionality

    Returns:
        The exit code of the program.
    """
    args = parse_cli_arguments()

    ensure_packages()
    ensure_gcn_daemon()

    if not args.init_only:
        mode = args.mode if not args.debug else "debug"
        return run_gcn_test(mode)
    return 0


def inside_right_venv() -> bool:
    """Checks if the process is inside the right venv

    The right vm hast the VIRTUAL_ENV variable set and uses _venv python
    """
    venv_home = os.environ.get("VIRTUAL_ENV")
    if venv_home is None:
        return False
    # Is it the righ environment
    return VENV_DIR == Path(venv_home) and VENV_DIR in Path(sys.executable).parents


def create_venv():
    """Creates a venv like python -m venv will do"""
    import venv

    venv.create(VENV_DIR, with_pip=True, clear=True, symlinks=not IS_WINDOWS)


def switch_to_venv():
    """Launch this script in the ovat venv

    It will launch the new python as a child process and finish the current process
    after the child has finished, bubbling the exit code.
    """
    environment = dict(os.environ)
    win_python = VENV_DIR / "Scripts" / "python.exe"
    unix_python = VENV_DIR / "bin" / "python"

    if win_python.exists():
        python_bin = win_python

    elif unix_python.exists():
        python_bin = unix_python
    else:
        raise RuntimeError(f"No python found in {VENV_DIR}")

    environment["PATH"] = str(python_bin.parent) + os.pathsep + environment["PATH"]
    environment["VIRTUAL_ENV"] = str(VENV_DIR)

    result = subprocess.run([str(python_bin)] + sys.argv, env=environment)
    # Stop here
    exit(result.returncode)


def prelaunch_checks():
    if not check_required_files():
        return 2

    if not check_network_access():
        return 3
    return 0


def launch():
    """Switch to the ovat venv if not already in it"""
    if not inside_right_venv():
        print("Getting into the tools virtual environment...")
        if not VENV_DIR.exists():
            print("Creating virtual environment...")
            create_venv()
        switch_to_venv()


def main():
    launch()
    prelaunch = prelaunch_checks()
    if prelaunch != 0:
        return prelaunch
    setup_ssl()
    return cli()


if __name__ == "__main__":
    exit(main())
