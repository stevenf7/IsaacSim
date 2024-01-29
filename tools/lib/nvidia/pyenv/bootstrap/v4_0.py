# Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import hashlib
import importlib
import json
import os
import platform
import subprocess
import sys
from pprint import pprint

_repoman = None
_repoman_bootstrapper = None
_packman_bootstrapped = 0


class opts:
    prep_env_only_env_var = "__PY_BOOTSTRAP_PREP_ONLY"
    load_prepped_env_env_var = "__PY_BOOTSTRAP_USE_PREPPED_ENV"
    relaunch_flag_env_var = "__PY_BOOTSTRAP_RELAUNCHED"
    no_relaunch_flag_env_var = "__PY_BOOTSTRAP_NO_RELAUNCH"

    packman_subdir = "packman"
    pip_subdir = "pip"

    pip_reqs_marker = "__pip_requirements_marker_file__"


class runtime:
    bin_name = os.path.basename(sys.argv[0])
    bin_path = os.path.dirname(os.path.realpath(sys.argv[0]))

    self_path = os.path.dirname(os.path.realpath(__file__))
    bootstrap_root = os.path.realpath(os.path.join(self_path, "..", "..", "..", ".."))
    runtime_dir = None

    packman_path = os.path.join(bootstrap_root, "packman")
    repoman_path = os.path.join(bootstrap_root, "repoman")

    pythons = {"windows": os.path.join(packman_path, "python.bat"), "linux": os.path.join(packman_path, "python.sh")}

    #  packmans = { 'windows' : os.path.join(packman_path, "packman.cmd"),
    #               'linux'   : os.path.join(packman_path, "packman") }

    deps = {"repoman": None, "pip": None, "packman": None}
    #           'packman-common': None, }

    env_config_file_name = "env_config.json"
    env_config_file_path = None


def bootstrap(runtime_dir=None, pip_requirements_file=None, packman_project_file=None, subdirs={}):

    if not (runtime_dir):
        runtime_dir = _default_runtime_dir()
    else:
        runtime_dir = _rel_to_bin(runtime_dir)

    runtime.runtime_dir = runtime_dir

    _setup_dep_dirs(runtime_dir)

    runtime.env_config_file_path = os.path.join(runtime_dir, runtime.env_config_file_name)

    ret = {}

    if os.getenv(opts.load_prepped_env_env_var, None):
        _relaunch_if_needed()
        ret = _bootstrap_prepared_env(subdirs=subdirs)

    else:
        prep_env_only_flag = os.getenv(opts.prep_env_only_env_var, None)

        if pip_requirements_file:
            _bootstrap_pip_deps(_rel_to_bin(pip_requirements_file))

        _relaunch_if_needed()

        pm_paths = {}

        if packman_project_file:
            pm_paths = _bootstrap_packman_deps(
                _rel_to_bin(packman_project_file), subdirs=subdirs, make_links=prep_env_only_flag
            )
            ret["packman_packages"] = pm_paths

        if prep_env_only_flag:
            _save_env_config(packman_links=pm_paths)
            _err_out(f"{opts.prep_env_only_env_var} is set, exiting")
            sys.exit(0)

    if "omni" in sys.modules:
        importlib.reload(sys.modules["omni"])

    _err_out("Bootstrap complete")
    _err_out("-" * 60)
    _clear_repoman_loggers()

    return ret


################################################################################
## Private
################################################################################


def _clear_repoman_loggers():
    global _repoman_bootstrapper

    if not _repoman_bootstrapper:
        return

    _repoman_bootstrapper.clear_loggers()


def _relaunch_if_needed():
    if not (os.getenv(opts.relaunch_flag_env_var, None)) and not (os.getenv(opts.no_relaunch_flag_env_var, None)):
        os.environ[opts.relaunch_flag_env_var] = "1"
        _relaunch()


def _bootstrap_prepared_env(subdirs={}):
    _err_out(f"Assuming env already prepared, will just set up paths")

    ret = {}

    _err_out(f"  > PIP:  {runtime.deps['pip']}")
    sys.path.append(runtime.deps["pip"])

    if os.path.isfile(runtime.env_config_file_path):
        _err_out(f"  > loading additional env info from " + f"{runtime.env_config_file_path}")
        ret = _load_and_process_env_file(runtime.env_config_file_path, subdirs=subdirs)

    return ret


def _load_and_process_env_file(path, subdirs={}):
    data = None

    with open(path, "r") as h:
        data = json.load(h)

    if "packman_deps" in data:
        for (dep, props) in data["packman_deps"].items():
            _err_out(f"  > {dep}")
            dep_path = os.path.join(runtime.bin_path, props["path"])

            if dep in subdirs:
                for subdir in _to_arr_if_scal(subdirs[dep]):
                    path = os.path.join(dep_path, subdir)
                    _err_out(f"    > {path}")
                    sys.path.append(path)
            else:
                err_out(f"  > {dep_path}")
                sys.path.append(dep_path)
        return data["packman_deps"]
    else:
        return {}


def _save_env_config(packman_links={}):
    _err_out(f"Saving env config to {runtime.env_config_file_path}")

    data = {"packman_deps": {}}

    for (dep, path) in packman_links.items():
        dep_rel_path = path[len(runtime.bin_path) + 1 :]
        data["packman_deps"][dep] = {"path": dep_rel_path}

    with open(runtime.env_config_file_path, "w") as h:
        h.write(json.dumps(data, indent=2))


def _setup_repoman():
    global _repoman
    global _repoman_bootstrapper

    #  _bootstrap_packman()

    if _repoman:
        return

    _err_out("Loading repoman")
    sys.path.append(runtime.repoman_path)

    import repoman

    _repoman_bootstrapper = repoman
    _repoman_bootstrapper.HOST_DEPS_PATH = runtime.deps["repoman"]
    _repoman_bootstrapper.bootstrap()

    import omni.repo.man

    _repoman = omni.repo.man


def _bootstrap_packman():
    global _packman_bootstrapped

    if _packman_bootstrapped:
        return ()

    _err_out(f"Bootstrapping packman")

    packman = runtime.packmans[_get_basic_platform()]
    os.environ["PM_MODULE_DIR_EXT"] = runtime.deps["packman-common"]
    os.environ["PM_INSTALL_PATH"] = runtime.packman_path
    os.environ["PM_PACKAGES_ROOT"] = os.path.expanduser("~/packman-repo")

    ret = subprocess.call([packman, "init"])
    if ret:
        _err_out(f"`packman init` failed with {ret}")
        sys.exit(ret)

    sys.path.append(runtime.deps["packman-common"])

    _packman_bootstrapped = 1


def _bootstrap_packman_deps(projectf, subdirs={}, make_links=0):
    _err_out(f"Bootstrapping packman dependencies from {projectf}")

    #  _bootstrap_packman()

    platform = _get_platform()
    import packmanapi

    pull_result = packmanapi.pull(project_path=projectf, platform=platform)

    ret = {}

    for (dep, location) in pull_result.items():
        paths = []

        if dep in subdirs:

            for subdir in _to_arr_if_scal(subdirs[dep]):

                path = os.path.join(location, subdir)
                if not (os.path.isdir(path)):
                    _err_out(f"Subdir `{subdirs[dep]}` does not exist at `{location}`, " + f"downloaded by packman")
                    sys.exit(1)
                else:
                    paths.append(path)
            del subdirs[dep]

        else:
            paths.append(location)

        for p in paths:
            _err_out(f"  > adding {p} to path")
            sys.path.append(p)

        if make_links:
            link_path = os.path.join(runtime.deps["packman"], dep)
            _err_out(f"    > linking `{dep}` to {link_path}")
            packmanapi.link(link_path, location)
            ret[dep] = link_path
        else:
            ret[dep] = location

    if len(subdirs):
        for (dep, subdir) in subdirs.items():
            _err_out(
                f"  > you requested to add `{subdir}` subdir of `{dep}`, "
                + f"but `{dep}` was not returned by Packman - probably, you got "
                + f"name mismatch between deps in your code and "
                + f"in your project file"
            )
        sys.exit(1)

    return ret


def _bootstrap_pip_deps(reqf):
    sys.path.append(runtime.deps["pip"])
    # If we were relaunched, it happened *after* PIP dependencies
    # were installed, so we don't need to install / check them again
    if os.getenv(opts.relaunch_flag_env_var, None):
        return

    _err_out(f"Bootstrapping pip dependencies from {reqf}")

    if _already_bootstrapped(reqf):
        _err_out(f"  > looks like already bootstrapped")
    else:
        ret = subprocess.call(
            [sys.executable, "-m", "pip", "--isolated", "install", "--target", runtime.deps["pip"], "-r", reqf]
        )
        if ret:
            _err_out(f"PIP failed with {ret}")
            sys.exit(ret)

        _set_pip_bootstrapped(reqf)
        sys.path.append(runtime.deps["pip"])


def _already_bootstrapped(reqf):
    marker = os.path.join(runtime.deps["pip"], opts.pip_reqs_marker)

    if not os.path.isfile(marker):
        return 0

    cur_checksum = _file_checksum(reqf)
    prior_checksum = ""

    with open(marker, "r") as h:
        prior_checksum = h.read()

    return cur_checksum == prior_checksum


def _set_pip_bootstrapped(reqf):
    with open(os.path.join(runtime.deps["pip"], opts.pip_reqs_marker), "w") as h:
        h.write(_file_checksum(reqf))


def _file_checksum(path):
    sha256 = hashlib.sha256()
    with open(path, "r") as h:
        sha256.update(h.read().encode("ascii"))

    return sha256.hexdigest()


def _setup_dep_dirs(runtime_dir):

    for subdir in runtime.deps.keys():
        runtime.deps[subdir] = os.path.join(runtime_dir, subdir)

        if not os.path.isdir(runtime.deps[subdir]):
            _err_out(f"Creating {runtime.deps[subdir]}")
            os.makedirs(runtime.deps[subdir])


def _to_arr_if_scal(var):
    if isinstance(var, list):
        return var
    elif isinstance(var, str):
        return [var]
    else:
        _err_out(f"{var}: should be an array or a string")
        sys.exit(1)


def _rel_to_bin(path):
    return os.path.join(runtime.bin_path, path)


def _default_runtime_dir():
    return _rel_to_bin(f"_deps_{runtime.bin_name}")


def _get_basic_platform():
    return platform.system().lower()


def _get_platform():
    _setup_repoman()
    return _repoman.get_host_platform()


def _err_out(*line):
    sys.stderr.write(" ".join(line))
    sys.stderr.write("\n")
    sys.stderr.flush()


def _relaunch():
    python = runtime.pythons[_get_basic_platform()]

    _err_out(f"Relaunching with {python}")

    cmd = list(sys.argv)
    cmd.insert(0, python)

    # FIXME add Halldor's magick

    import subprocess

    sys.exit(subprocess.run(cmd).returncode)
