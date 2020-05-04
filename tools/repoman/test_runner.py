import os
import sys
import glob
import shutil
import logging
import fnmatch
import argparse
import base64
import hashlib
import time
from typing import List

import packmanapi
import repoman

repoman.bootstrap()
import omni.repo.man

logger = logging.getLogger(os.path.basename(__file__))

ARCHIVE_PATTERN = "_builtpackages/isaac-sim*-{config}.7z"


def is_running_under_teamcity():
    return bool(os.getenv("TEAMCITY_VERSION"))


def short_hash(name: str, length: int = 5) -> str:
    hasher = hashlib.sha1(name.encode("utf-8"))
    return base64.urlsafe_b64encode(hasher.digest()[:length]).decode("ascii").rstrip("=")


def get_exe_ext(platform: str) -> str:
    return ".exe" if platform == "windows-x86_64" else ""


def get_shell_ext(platform: str) -> str:
    return ".bat" if platform == "windows-x86_64" else ".sh"


def get_execution_prefix(root: str, platform_host: str, linbuild_profile: str) -> str:
    return (
        []
        if (platform_host == "windows-x86_64" or linbuild_profile is None)
        else ["_build/host-deps/linbuild/linbuild.sh", f"--with-volume={root}", f"--profile={linbuild_profile}", "--"]
    )


def escape_value(value):
    quote = {"'": "|'", "|": "||", "\n": "|n", "\r": "|r", "[": "|[", "]": "|]"}
    return "".join(quote.get(x, x) for x in value)


def teamcity_message(messageName, **properties):
    current_time = time.time()
    (current_time_int, current_time_fraction) = divmod(current_time, 1)
    current_time_struct = time.localtime(current_time_int)
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S.", current_time_struct) + "%03d" % (int(current_time_fraction * 1000))
    message = "##teamcity[%s timestamp='%s'" % (messageName, timestamp)

    for k in sorted(properties.keys()):
        value = properties[k]
        if value is None:
            continue
        message += f" {k}='{escape_value(str(value))}'"

    message += "]\n"

    sys.stdout.write(message)
    sys.stdout.flush()


def teamcity_report_fail(test_id, fail_type, err):
    teamcity_message("testFailed", name=test_id, fail_type=fail_type, message=err)


def teamcity_start_test(test_id):
    teamcity_message("testStarted", name=test_id, captureStandardOutput="true")


def teamcity_stop_test(test_id):
    teamcity_message("testFinished", name=test_id)


def prepare_package(root: str, config: str, clean: bool) -> str:
    """Find and extract a package, return path to a folder"""

    candidates = list(glob.glob(os.path.join(root, ARCHIVE_PATTERN.format(config=config))))
    if len(candidates) == 0:
        logger.error(f"No archive files found.")
        sys.exit(-1)

    archive_path = candidates[0]
    if len(candidates) > 1:
        logger.warn(f"Multiple candidates for archive file, selecting first: {archive_path}")

    if not os.path.exists(archive_path):
        logger.error(f"Archive file doesn't exist: {archive_path}")
        sys.exit(-1)

    # Shorten folder name to workaround "too long path issue on TC"
    filename, _ = os.path.splitext(os.path.basename(archive_path))
    folder_to_extract = os.path.join(os.path.dirname(archive_path), short_hash(filename))

    if clean:
        if os.path.exists(folder_to_extract):
            logger.info(f"Cleaning folder: {folder_to_extract}")
            shutil.rmtree(folder_to_extract)

    if not os.path.exists(folder_to_extract):
        packmanapi.extract_archive7z_to_folder(archive_path, folder_to_extract)

    return folder_to_extract, archive_path


def run_unittests(root: str, platform_host: str, config: str, linbuild_profile: str, extra_args: List = []):
    executable = f"test.unit{get_exe_ext(platform_host)}"
    exec_prefix = get_execution_prefix(root, platform_host, linbuild_profile)

    args = []
    if is_running_under_teamcity():
        args.append("-r teamcity")
    args.extend(extra_args)

    proc_arglist = exec_prefix + [f"{root}/_build/{platform_host}/{config}/plugins/{executable}"] + args
    omni.repo.man.run_process(proc_arglist, exit_on_error=True)


def run_pythontests(root: str, platform_host: str, config: str, linbuild_profile: str, extra_args: List = []):
    """Run python tests suite inside of Kit"""

    executable = f"test-isaac-sim{get_shell_ext(platform_host)}"
    exec_prefix = get_execution_prefix(root, platform_host, linbuild_profile)
    args = ["--exec", '"run_tests.py"']
    args.extend(extra_args)

    proc_arglist = exec_prefix + [f"{root}/_build/{platform_host}/{config}/{executable}"] + args
    omni.repo.man.run_process(proc_arglist, exit_on_error=True)


def run_startuptest(root: str, platform_host: str, config: str, linbuild_profile: str, extra_args: List = []):
    """Start and quit Kit"""

    kit_folder = f"{root}/_build/target-deps/kit_sdk_{config}/_build/{platform_host}/{config}"
    bin_folder = f"{root}/_build/{platform_host}/{config}"

    # Search for all .bat/.sh files
    executable_files = [os.path.basename(f) for f in glob.glob(bin_folder + "/*" + get_shell_ext(platform_host))]

    # Explicitly add default kit:
    # executable_files.insert(0, f"omniverse-kit{get_exe_ext(platform_host)}")

    # Ignore some runners:
    IGNORE_LIST = [
        # "*-headless*",
        "python*",
        "mpirun*",
        "setup_python_env*",
        "example.python*",
        "tests-omni.kit.default*",
        "kit-default*",
        "kit-profile*",
        "kit-nonrtx*",
        "test-isaac-sim*",
    ]
    executable_files = [f for f in executable_files if not any(fnmatch.fnmatch(f, p) for p in IGNORE_LIST)]

    print(f"Found those executable files to run startup tests on: {executable_files}")

    exec_prefix = get_execution_prefix(root, platform_host, linbuild_profile)
    args = [
        "--exec",
        f"open {kit_folder}/../../../data/scenes/BuiltInMaterials.usda",
        "--carb/rtx/materialDb/syncLoads=true",
        "--carb/omni.kit.plugin/syncUsdLoads=true",
        "--carb/rtx/flow/enabled=true",
        "--carb/app/quitAfter=10",  # Quit after 10 updates
    ]
    args.extend(extra_args)

    os.environ["PYTHONPATH"] = ""  # Don't propagagate current ENV into the test (e.g. packman path is set there)

    # We will run all tests regardless of failure
    failure = False

    for executable_file in executable_files:
        # TC reporting
        extra_args_str = "_".join(extra_args)
        test_id = f"StartupTest:{executable_file}_{extra_args_str}"
        teamcity_start_test(test_id)

        # Run process
        proc_arglist = exec_prefix + [f"{bin_folder}/{executable_file}"] + args
        returncode = omni.repo.man.run_process(proc_arglist, exit_on_error=False)

        # Report failure and mark overall run as failure
        if returncode != 0:
            teamcity_report_fail(test_id, "Error", f"Exit code: {returncode}")
            failure = True

        teamcity_stop_test(test_id)

        # Override the command line options after the first execution to just launch and quit
        args = ["--carb/app/quitAfter=10"]  # Quit git after 10 updates

    # Exit with non-zero code on failure
    if failure:
        sys.exit(1)


def run_qatests(root: str, platform_host: str, config: str, linbuild_profile: str, extra_args: List = []):
    executable = f"omniverse-kit{get_exe_ext(platform_host)}"
    exec_prefix = get_execution_prefix(root, platform_host, linbuild_profile)

    args = ["--exec", f"qa_test.py", "--carb/app/omniverse/showLoginOnStart=false"]
    args.extend(extra_args)

    proc_arglist = exec_prefix + [f"{root}/_build/{platform_host}/{config}/{executable}"] + args
    omni.repo.man.run_process(proc_arglist, exit_on_error=True)


def run_qatest_mirror(root: str, platform_host: str, config: str, linbuild_profile: str, extra_args: List = []):
    extra_args.append("--carb/qatest/testType=mirror")
    run_qatests(root, platform_host, config, linbuild_profile, extra_args)


def run_qatest_nucleus_samples(
    root: str, platform_host: str, config: str, linbuild_profile: str, extra_args: List = []
):
    extra_args.append("--carb/qatest/testType=nucleusSamples")
    run_qatests(root, platform_host, config, linbuild_profile, extra_args)


TEST_SUITES = {
    "unittests": run_unittests,
    "pythontests": run_pythontests,
    "startuptest": run_startuptest,
    "qatests": run_qatests,
    "qatestmirror": run_qatest_mirror,
    "qatestnucleussamples": run_qatest_nucleus_samples,
}


def main():
    platform_host = omni.repo.man.get_and_validate_host_platform(["windows-x86_64", "linux-x86_64"])
    repo_folders = omni.repo.man.get_repo_paths()

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.name = "Universal Test Runner"
    parser.add_argument(
        "-p",
        "--from-package",
        dest="from_package",
        default=False,
        action="store_true",
        help=f"Use package from '{ARCHIVE_PATTERN}' instead of a root folder.",
    )
    parser.add_argument(
        "-x",
        "--clean",
        dest="clean",
        default=False,
        action="store_true",
        help="Clean run (force extract package again).",
    )
    parser.add_argument(
        "--suite", dest="suite", choices=TEST_SUITES.keys(), default="unittests", help="Test suite to run."
    )
    parser.add_argument(
        "-c",
        "--config",
        dest="config",
        required=False,
        default="debug",
        help="Config to run test against (debug or release). (default: %(default)s)",
    )
    parser.add_argument(
        "-e",
        "--extra-arg",
        action="append",
        dest="extra_args",
        default=[],
        help="Extra argument to pass. Can be specified multiple times.",
    )
    parser.add_argument(
        "--linbuild-profile",
        dest="linbuild_profile",
        required=False,
        default=None,
        help="linbuild profile within which to run tests.",
    )

    options = parser.parse_args()

    root_folder = repo_folders["root"]
    if options.from_package:
        root_folder, _ = prepare_package(root_folder, options.config, options.clean)

    if options.linbuild_profile is not None:
        packmanapi.pull(os.path.join(repo_folders["deps_xml_folder"], "linbuild.packman.xml"), platform=platform_host)

    logger.info(f"Running test suite: {options.suite}...")
    TEST_SUITES[options.suite](root_folder, platform_host, options.config, options.linbuild_profile, options.extra_args)


if __name__ == "__main__":
    main()
