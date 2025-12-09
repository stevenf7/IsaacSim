# Check App Version Locks
#
# This script validates and generates shared version lock files for Isaac Sim applications.
# It ensures that all extensions used by individual app kit files are properly tracked in
# a shared version lock file (isaacsim.exp.extscache.kit).
#
# The script performs two main operations:
# 1. Compares extensions in individual app kit files (source/apps/*.kit) against the shared
#    version lock file and reports any missing or redundant extensions.
# 2. Generates a new shared version lock file by merging dependencies from all apps and
#    updating it using the repo precache mechanism.
#
# How to run:
#   ./repo.sh ci check_app_version_locks
#
# This command is configured in repo_internal.toml:
#   [repo_ci.jobs.check_app_version_locks]
#   script = "${root}/tools/ci/check_app_version_locks/check_app_version_locks.py"
#
# Prerequisites:
#   - source/apps/*.kit files must be present
#   - source/extensions must be fetched
#   - _build/packages must contain isaac-sim-standalone*.7z packages
#
# Outputs:
#   - ./details.txt: Report of differences between apps and the shared version lock
#   - ./isaacsim.exp.extscache.kit: Updated shared version lock file
#
# Exit codes:
#   0: No missing or redundant extensions found
#   1: Differences detected (missing or redundant extensions)
#

import glob
import os
import shutil
import sys
from pathlib import Path

import omni.repo.ci
import omni.repo.man
import tomli

ROOT = Path(__file__).joinpath("..", "..", "..", "..").resolve()
source_apps = ROOT / "source/apps"
shared_version_lock_filename = "isaacsim.exp.extscache.kit"

KIT_OUTPUT = str(ROOT / shared_version_lock_filename)


class App:
    """Represents an application with its extensions and dependencies.

    Args:
        name: The name of the application.
        extensions: Set of extension names enabled in the application.
        exact_dependencies: Set of exact version dependencies for the application.
    """
    def __init__(self, name: str, extensions: set[str], exact_dependencies: set[str]):
        self.name = name
        self.extensions = extensions
        self.exact_dependencies = exact_dependencies


class Result:
    """Represents the result of comparing app version locks.

    Args:
        all_from_apps: List of all extensions found across all apps.
        missings: List of tuples containing app groups and their missing extensions.
        redundants: List of extensions present in the lock file but not used by any app.
    """
    def __init__(self, all_from_apps: list[str], missings: list[tuple[str, list[str]]], redundants: list[str]):
        self.all_from_apps = all_from_apps
        self.missings = missings
        self.redundants = redundants


def _generate_differences(output_path: str) -> bool:
    """Generate a report of differences between app version locks and the shared lock file.

    Compares the extensions locked in individual app kit files against the shared version
    lock file, identifying missing and redundant extensions.

    Args:
        output_path: Path where the differences report will be written.

    Returns:
        True if there are no missing or redundant extensions, False otherwise.
    """
    # Load the shared lock file.
    shared_version_lock_path = str(source_apps / shared_version_lock_filename)
    lock = _load_version_lock(shared_version_lock_path)
    if not lock:
        print(f"Failed to load the version lock file: {shared_version_lock_path}")
        return False

    # Load all apps with version locks.
    apps = []
    for file_path in glob.glob(str(source_apps / "*.kit")):
        if os.path.isfile(file_path):
            app = _load_version_lock(file_path)
            if app:
                apps.append(app)
            else:
                print(f"Failed to load the version lock from the app: {file_path}")

    if not apps:
        print(f"Failed to load any apps from : {source_apps}")
        return False

    # Compare the version locks and print the difference.
    result = _check_app_version_locks(apps, lock)

    # Print the result to the console and a text file
    with open(output_path, "w") as fw:
        num_missings = 0
        _headline(fw, f"Extensions locked in some apps but not in {lock.name}")
        for group_name, extensions in result.missings:
            extensions = [ext for ext in extensions if ext not in lock.exact_dependencies]
            if not extensions:
                continue
            num_missings += len(extensions)
            _print(fw, f"> {group_name}")
            for ext in extensions:
                _print(fw, ext)
            _print(fw, "")

        _headline(fw, f"Extensions locked in {lock.name} but not in any app")
        num_redundants = len(result.redundants)
        for ext in result.redundants:
            _print(fw, ext)
        _print(fw, "")

        _headline(fw, "Summary")
        _print(fw, f" * {num_missings} extensions are missing in the shared version lock file")
        _print(fw, f" * {num_redundants} extensions are redundant in the shared version lock file")
        _print(fw, "")

    return num_missings == 0 and num_redundants == 0


def _load_version_lock(path: str):
    """Load version lock information from a kit file.

    Parses a kit file to extract enabled extensions and exact version dependencies.

    Args:
        path: Path to the kit file to load.

    Returns:
        An App object containing the version lock information, or None if loading fails.
    """
    try:
        config = _load_kit_toml(path)
    except Exception as e:
        print(f"Failed to load {path}: {e}")
        return None
    if "enabled" in config.get("settings",{}).get("app",{}).get("exts",{}):
        extensions = config["settings"]["app"]["exts"]["enabled"]
    else:
        extensions = {}
    exact_dependencies = set()
    in_block = False
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("# Exact Version dependencies:"):
                in_block = True
            elif in_block:
                tokens = line.split()
                if not tokens:
                    in_block = False
                else:
                    exact_dependencies.add(tokens[-1])

    return App(os.path.basename(path), set(extensions), exact_dependencies)


def _load_kit_toml(path) -> dict:
    """Load a kit TOML file that may contain duplicate table names.

    Kit TOML files are less strict than standard TOML and allow multiple tables with the
    same name (e.g., [settings] appearing twice). This function handles such cases by
    splitting the file at known boundaries and loading chunks separately.

    Args:
        path: Path to the kit TOML file to load.

    Returns:
        Dictionary containing the merged TOML data from all chunks.
    """
    with open(path, "r") as f:


        print(f"Loading {path}")  
        lines = f.readlines()

        # find split points
        split_indices = [i for i, v in enumerate(lines) if v.startswith("# BEGIN GENERATED PART") or v.startswith("[settings]")] + [None]

        # iterate chunks
        prev = 0
        data = {}
        for i in split_indices:
            content = "".join(lines[prev:i])
            prev = i
            data.update(tomli.loads(content))
        return data


def _check_app_version_locks(apps: list[App], lock: App) -> list[tuple[str, list[str]]]:
    """Check app version locks against a shared lock file.

    Compares extensions in individual apps against a shared lock file to identify
    missing extensions (in apps but not in lock) and redundant extensions (in lock
    but not in any app).

    Args:
        apps: List of App objects representing individual applications.
        lock: App object representing the shared version lock file.

    Returns:
        A Result object containing all extensions from apps, missing extensions grouped
        by app names, and redundant extensions.
    """
    # Determine redundants
    all_ = set()
    for app in apps:
        all_.update(app.extensions)
    redundants = list(sorted(lock.extensions - all_))

    # Determine missings
    extensions_to_app_names = {}
    for app in apps:
        for extension in app.extensions:
            if extension not in lock.extensions:
                if extension not in extensions_to_app_names:
                    extensions_to_app_names[extension] = []
                extensions_to_app_names[extension].append(app.name)

    merged_missings = {}
    for extension, names in extensions_to_app_names.items():
        group = tuple(sorted(names))
        if group not in merged_missings:
            merged_missings[group] = []
        merged_missings[group].append(extension)
    missings = [(group, list(sorted(extensions))) for group, extensions in merged_missings.items()]
    missings.sort(key=lambda x: (-len(x[0]), x[0]))

    return Result(list(sorted(all_)), missings, redundants)


def _headline(fw, message):
    """Print a formatted headline to a file and console.

    Args:
        fw: File writer object to write the headline to.
        message: The headline message text.
    """
    n = max(len(message) + 2, 80)
    _print(fw, "#" * n)
    _print(fw, f"# {message}")
    _print(fw, "#" * n)
    _print(fw, "")


def _print(fw, message):
    """Print a message to both a file and console.

    Args:
        fw: File writer object to write the message to.
        message: The message text to print.
    """
    fw.write(message + "\n")
    print(message)


def _generate_shared_version_lock(output_path: str):
    """Generate a shared version lock file from all app dependencies.

    Extracts packages, collects dependencies from all app kit files, and generates
    a unified version lock file. The lock file is then updated using the repo precache
    mechanism to lock extension versions.

    Args:
        output_path: Path where the generated shared version lock file will be written.
    """
    # Generate the build folder.
    build_path = ROOT / "_build/linux-x86_64/release"
    exts_path = str(build_path / "exts")
    extscache_path = str(build_path / "extscache")
    os.makedirs(exts_path, exist_ok=True)
    os.makedirs(extscache_path, exist_ok=True)

    # Unzip all packages and copy extscache
    archive_patterns = [
        str(Path("_build") / "packages/isaac-sim-standalone*.7z"),
    ]
    for pattern in archive_patterns:
        print(f"> Extract {pattern}")
        root, _ = omni.repo.man.find_and_extract_package(pattern)
        root = Path(root)
        _copytree(str(root / "extscache"), extscache_path)
        # _copytree(str(root / "exts"), exts_path)

    # Generate a new kit file with the union of dependencies from all apps.
    dependencies = {}
    experiences = []
    for file_path in glob.glob(str(source_apps / "*.kit")):
        if os.path.basename(file_path) == shared_version_lock_filename:
            # Skip the original lock file.
            continue
        experiences.append(file_path.split("/")[-1].removesuffix(".kit"))
        config = _load_kit_toml(file_path)
        for key, value in config["dependencies"].items():
            # If multiple apps configure the same extension, keep the one with the longest configuration.
            # For example,  {version: "=105.2.16"} is preferred over {}.
            if key not in dependencies or len(str(value)) > len(str(dependencies[key])):
                dependencies[key] = value

    print(f"> Experiences: {experiences}")

    dependencies = {k:v for (k,v) in dependencies.items() if k not in experiences}



    print(f"> Create the new version lock file {output_path}")
    _write_version_lock_file(dependencies, output_path)

    # Patch repo.toml such that we can update the version lock of the new generated file.
    repo_toml_path = str(ROOT / "repo.toml")
    content = open(repo_toml_path).readlines()
    with open(repo_toml_path, "w") as fw:
        pattern = "${root}/_build/$platform/$config/apps/isaacsim.exp.extscache.kit"
        for line in content:
            if pattern in line:
                line = line.replace(pattern, output_path)
            fw.write(line)

    # Update the version lock
    print(f"> Update the version lock file {output_path}")
    # `repo precache_exts` is in Kit kernel, so we need to download Kit kernel first.
    # We need to hardcode both platform_target and platform_target_abi because they're resolved by repo_build in the normal process.
    omni.repo.ci.launch(
        [
            "${root}/tools/packman/packman",
            "pull",
            "-p",
            "manylinux_2_35_x86_64",
            "-t",
            "platform_target=linux-x86_64",
            "-t",
            "platform_target_abi=manylinux_2_35_x86_64",
            "-t",
            "config=release",
            "deps/kit-sdk.packman.xml",
        ]
    )
    # Note that `repo precache_exts` prefers existing extensions in ${root}/source/extensions and ${root}/_build/linux-x86_64/release/extscache.
    # All required extensions should have been already there, so we locked the versions by using the extensions in extscache.
    # source/extensions and _build/packages are downloaded by the CI, and extscache is prepared in this function previously.
    omni.repo.ci.launch(["${root}/repo${shell_ext}", "precache_exts", "-c", "release"])


def _copytree(source: str, destination: str):
    """Copy directory contents from source to destination with error handling.

    Copies all files and subdirectories from the source directory to the destination,
    handling permission errors and other OS-level exceptions gracefully.

    Args:
        source: Source directory path to copy from.
        destination: Destination directory path to copy to.

    Raises:
        Exception: Re-raises unexpected exceptions after logging them.
    """
    print(f"Copy {source}/* to {destination}")
    for item in Path(source).iterdir():
        # Construct the destination path for the item
        dest_item = Path(destination) / item.name

        try:
            if item.is_file():
                shutil.copy2(item, dest_item)
            elif item.is_dir():
                shutil.copytree(item, dest_item, dirs_exist_ok=True)
        except (PermissionError, OSError) as e:
            # Log expected errors such as permission issues or read-only files
            print(f"Warning: Failed to copy {item} to {dest_item}: {e}")
        except Exception as e:
            # Log unexpected errors for debugging
            print(f"Error: Unexpected exception while copying {item} to {dest_item}: {type(e).__name__}: {e}")
            raise


def _write_version_lock_file(dependencies: dict, path: str):
    """Write extension dependencies to a version lock kit file.

    Creates a kit file with dependency declarations in TOML format, including
    platform-specific dependencies.

    Args:
        dependencies: Dictionary mapping extension names to their version specifications.
        path: Path where the version lock file will be written.
    """
    with open(path, "w") as fw:
        fw.write("# This kit file is only used to lock some (or all) extensions versions for a public registry.\n")
        fw.write("# It is excluded from the public version of this repo.\n")
        fw.write("\n")
        fw.write("[dependencies]\n")

        filter_platform = {}
        for key, value in sorted(dependencies.items()):
            if key == "filter:platform":
                filter_platform.update(value)
            else:
                fw.write(f'"{key}" = {_to_toml_value(value)}\n')

        fw.write("\n")
        for platform, extensions in sorted(filter_platform.items()):
            fw.write(f'[dependencies."filter:platform"."{platform}"]\n')
            for key, value in sorted(extensions.items()):
                fw.write(f'"{key}" = {_to_toml_value(value)}\n')


# A simple function to serialize a simple dict to toml string.
# If the scope of input is more complicated (e.g., nested dict), use a third party package to dump the string instead.
def _to_toml_value(config: dict):
    """Convert a dictionary to a TOML value string.

    Serializes a simple dictionary into TOML inline table format. For more complex
    nested structures, consider using a third-party TOML library.

    Args:
        config: Dictionary to convert to TOML format.

    Returns:
        String representation of the dictionary in TOML inline table format.
    """
    def to_value(v):
        if isinstance(v, str):
            return f'"{v}"'

        if isinstance(v, bool):
            return str(v).lower()

        return str(v)

    vs = [f"{key} = {to_value(value)}" for key, value in sorted(config.items())]
    if not vs:
        return "{}"
    return f'{{ {", ".join(vs)} }}'


def _get_artifact_url():
    """Get the CI artifact URL for the current job.

    Constructs a URL to access job artifacts in the CI/CD system using environment
    variables. Returns a local path if not running in CI.

    Returns:
        URL string pointing to the CI job artifacts, or "." if not in CI environment.
    """
    url = os.getenv("CI_SERVER_URL", "")
    if not url:
        return "."
    project_path = os.getenv("CI_PROJECT_PATH", "")
    job_id = os.getenv("CI_JOB_ID", "")
    return f"{url}/{project_path}/-/jobs/{job_id}/artifacts/file"


def main(args):
    """Main entry point for checking app version locks.

    Generates a report of differences between app version locks and the shared lock file,
    then generates a new shared version lock file based on all app dependencies.

    Args:
        args: Command line arguments (unused).
    """
    detail_filename = "details.txt"
    ok = _generate_differences(str(ROOT / detail_filename))

    print("#" * 80)
    new_lock_filename = shared_version_lock_filename
    _generate_shared_version_lock(str(ROOT / new_lock_filename))

    artifact_url = _get_artifact_url()
    print(f"Wrote the new shared lock to {artifact_url}/{new_lock_filename}")
    print(f"Wrote the details of differences to {artifact_url}/{detail_filename}")

    sys.exit(0 if ok else 1)
