# Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import logging
import re
import shutil
import tempfile
from pathlib import Path
from typing import AnyStr, List, Optional, Tuple, Union

from process_helper import spawn_process, tee
from sevenza_helper import extract_to_folder
from teamcity_helper import download_artifact_regex

from . import utilities

_log = logging.getLogger("kit_runner")


class KitRunner:
    """
    KitRunner is a helper class for dealing with all things Omniverse Kit.

    It takes care of build acquisition, extraction, execution and cleanup.
    It also provides clean interfaces to Kit's Python interpreter.
    """

    _platform = utilities.PlatformHelper()

    app_shortname = "Kit"
    tc_windows_build_and_packaging_job = "Omniverse_Kit_Master_BuildAndPackaging_BuildWindowsX8664ReleaseOnly"
    tc_linux_build_and_packaging_job = "Omniverse_Kit_Master_BuildAndPackaging_BuildLinuxX8664ReleaseOnly"
    artifact_re = r".*@\d+\.\d+\.\d+-.*\.7z"
    build_re = re.compile(rf"omniverse-kit@(.*)-{_platform.os.lower()}")

    def __init__(
        self,
        tc_build_id: Optional[int] = None,
        app_root_dir: Optional[Union[str, Path]] = None,
        build_extraction_dir: Optional[Union[str, Path]] = None,
        build_archive_path: Optional[Union[str, Path]] = None,
        app_exe_path: Optional[Union[str, Path]] = None,
    ):
        """
        Initialize a KitRunner object which helps you acquire, launch and manage
        a Kit instance.

        If a Teamcity Build ID and a Local Path are not provided, then the runner
        defaults to pulling the latest successful Master build from Teamcity

        Args:
            tc_build_id: A Teamcity Build ID (ie. 4577565)
            app_root_dir: The path to an existing Kit installation (the root directory)
            build_extraction_dir: The work directory where to unpack and execute Kit if pulling from Teamcity
                A temporary directory by default.
            build_archive_path: A path to an archive of Kit's artifact from Teamcity (useful if you want to
                use the entire extract-run-delete flow of the Runner without re-downloading Kit each time)
            app_exe_path: The path to an omniverse-kit[.exe] (overrides all above locators for Kit)

        Raises:
            ValueError if an incorrect combination of values is passed
            EnvironmentError if called on an unsupported OS
            FileNotFoundError if provided paths to the app's dir or EXE do not exist
        """
        if tc_build_id and app_root_dir:
            raise ValueError("You cannot pass tc_build_id and local_path at the same time, one negates the other.")

        # make all path args a Path
        self.app_root_dir = _sanitize_path(app_root_dir) if app_root_dir is not None else app_root_dir
        self.build_extraction_dir = (
            _sanitize_path(build_extraction_dir) if build_extraction_dir is not None else build_extraction_dir
        )
        self.build_archive_path = (
            _sanitize_path(build_archive_path) if build_archive_path is not None else build_archive_path
        )
        self.app_exe_path = _sanitize_path(app_exe_path) if app_exe_path is not None else app_exe_path
        self.tc_build_id = tc_build_id

        self.build_number: Optional[str] = None

        # process stuff
        self.stdout: Optional[AnyStr] = None
        self.stderr: Optional[AnyStr] = None
        self.return_code: Optional[int] = None
        self.timed_out: Optional[bool] = None
        self.log_file: Optional[Path] = None

        self.kitpy_path: Optional[Path] = None
        self.overlaid_files: List[Path] = []

        self._pip_target: Optional[Path] = None

        # Setup our current environment
        if self.build_extraction_dir and not self.app_root_dir:
            self._cleanup = False
            if not self.build_extraction_dir.exists():
                self.build_extraction_dir.mkdir(parents=True)
        elif self.app_root_dir:
            if not self.app_root_dir.exists():
                raise FileNotFoundError(f"App root directory not found: {self.app_root_dir}")
            self._cleanup = False
            self.build_extraction_dir = self.app_root_dir
        elif self.app_exe_path is not None:
            if not self.app_exe_path.exists():
                raise FileNotFoundError(f"App EXE not found: {self.app_exe_path}")
            self._cleanup = False
        else:
            self._cleanup = True
            self.build_extraction_dir = Path(tempfile.mkdtemp(prefix="ovat-kit."))

        if not tc_build_id and not app_root_dir and not build_archive_path and not app_exe_path:
            _log.debug(f"Runner configured to download latest {self.app_shortname} from Teamcity")

        _log.debug(
            "Using:\n"
            f" - {self.app_shortname} build extraction directory: {self.build_extraction_dir}\n"
            f" - {self.app_shortname} directory: {self.app_root_dir}\n"
            f" - {self.app_shortname} executable path: {self.app_exe_path}\n"
            f" - {self.app_shortname} python path: {self.kitpy_path}\n"
            f" - {self.app_shortname} archive path: {self.build_archive_path}"
        )

    def prepare(self) -> Path:
        """
        Sets up the Kit environment. If a app_root_dir was passed, just initialize paths,
        otherwise, download Kit from Teamcity and extract it

        Returns:
            The path to the Kit executable

        Raises:
            FileNotFoundError if the artifact download from Teamcity fails
            RuntimeError if the artifact download was not successful
        """
        # Overrides everything.
        if self.app_exe_path:
            # Assume a default kit structure _build/platform/config
            # 4 parents here because the first drops the EXE from the path
            self.app_root_dir = self.app_exe_path.parent.parent.parent.parent
            kitpy = "python" + self._platform.script_extension()
            self.kitpy_path = self.app_exe_path.parent / kitpy
            _log.debug(f"Using {self.app_shortname} exe: {self.app_exe_path}")
            return self.app_exe_path

        # If we have a app_root_dir, we don't have to do any hard work
        if self.app_root_dir:
            self._find_exe()
            _log.debug(f"Using Kit exe: {self.app_exe_path}")
            return self.app_exe_path

        # if we didn't get an archive, pull one from teamcity
        if not self.build_archive_path:
            self.build_archive_path, self.build_number = self.download_from_teamcity(
                self.build_extraction_dir, tc_build_id=self.tc_build_id
            )
        else:
            self._guess_build_number()

        # we'll put Kit in a subdirectory of the build_extraction_dir
        self.app_root_dir = self.build_extraction_dir / f"{self.app_shortname.lower()}"

        extract_to_folder(self.build_archive_path, self.app_root_dir)

        # set app_exe_path and kitpy_path
        self._find_exe()
        _log.debug(f"Using {self.app_shortname} exe: {self.app_exe_path}")
        return self.app_exe_path

    def _guess_build_number(self):
        """
        Try to figure out the build number from Kit's archive

        Raises:
            EnvironmentError if platform is unsupported
        """

        _ = self.build_re.findall(str(self.build_archive_path))
        if len(_) > 0:
            self.build_number = _.pop()
        else:
            self.build_number = "unknown-build"

        _log.debug(f"Guessed build number from archive: {self.build_number}")

    def _find_exe(self):
        """
        Try to find the Kit EXE and Kit Python script inside the app_root_dir
        Note that this is hardcoded to use the release build
        """
        expected_app_exe_path = (
            "_build/" + self._platform.architecture() + "/release/omniverse-kit" + self._platform.executable_extension()
        )
        expected_kitpy_path = (
            "_build/" + self._platform.architecture() + "/release/python" + self._platform.script_extension()
        )

        exe = self.app_root_dir / expected_app_exe_path
        if not exe.exists():
            raise FileNotFoundError(f"Could not find the {self.app_shortname} EXE, looked in: {exe}")
        self.app_exe_path = exe

        # We don't care about this so much, don't assert if its missing
        self.kitpy_path = self.app_root_dir / expected_kitpy_path

    def set_pip_target(self, target_dir: Union[str, Path]):
        """
        Sets the target directory for KitPy's pip packages

        Args:
            target_dir: Absolute path where KitPy's packages should be installed.
                This will automatically be set to Kit's /app/extensions/pythonUserEnvPath
                configuration setting
        """
        self._pip_target = _sanitize_path(target_dir)

    def add_overlaid_content(self, root_dir: Union[str, Path], relative_to_exe: bool = False):
        """
        Takes a root directory and copies the file and directory structure inside to
        the current app_root_dir. Please note:

        !build and !platform are special directory names that will be replaced with
        _build and the current OS platform so that files can be overlaid regardless
        of the platform-specific Kit directory structure

        Args:
            root_dir: Source of file overlays
            relative_to_exe: Place files beside Kit EXE rather than in the Kit Root
        """
        root_dir = _sanitize_path(root_dir)
        for file in (f for f in utilities.find_rglob(root_dir, "*") if f.is_file()):
            # filter files for their respective OS
            if file.suffix in self._platform.invalid_script_extensions():
                continue
            elif file.name == ".packman.sha1":
                continue

            new_component = file.relative_to(root_dir)
            if relative_to_exe:
                destination = self.app_exe_path.parent / new_component
            else:
                destination = self.app_root_dir / new_component

            destination.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy(file, destination)

            self.overlaid_files.append(destination)

    def run_command(
        self, app_exe_path: Union[str, Path], args: str = "", timeout: int = 60, tee_output=False
    ) -> Tuple[int, AnyStr, AnyStr, bool]:
        """
        Run any command in the foreground (blocks) until it exits or the timeout is reached

        Args:
            app_exe_path: complete path to the executable to run
            args: arguments to be passed to the executable
            timeout: seconds to wait before killing the process
            tee_output: see the output from the python process piped to stdout/stderr in realtime

        Returns:
            Tuple (return_code, stdout, stderr, did_exe_timeout)

        Raises:
            FileNotFoundError if app_exe_path does not exist
        """
        app_exe_path = _sanitize_path(app_exe_path)
        if not app_exe_path.exists():
            raise FileNotFoundError(f"run_command() error: {app_exe_path} not found")

        run_func = tee if tee_output else spawn_process

        self.return_code, self.stdout, self.stderr, self.timed_out = run_func(app_exe_path, args, timeout)

        return self.return_code, self.stdout, self.stderr, self.timed_out

    def get_log_file(self) -> Optional[Path]:
        """
        Try to discover an `omniverse-kit.log` file in the directory structure of the App
        EXE Path's parent directory

        Returns:
            A Path object to the logfile if found, None otherwise
        """
        logs = [f for f in utilities.find_rglob(self.app_exe_path.parent, "omniverse-kit.log") if f.is_file()]
        if len(logs) == 1:
            self.log_file = logs.pop()
        else:
            self.log_file = None

        return self.log_file

    def run_app(self, args: str = "", timeout: int = 60, tee_output=False) -> Tuple[int, AnyStr, AnyStr, bool]:
        """
        Runs the App in the foreground (blocks) until it exits or the timeout is reached.
        Args:
            args: arguments to be passed to the App's exe
            timeout: seconds to wait before killing the App
            tee_output: see the output from the python process piped to stdout/stderr in realtime

        Returns:
            Tuple (return_code, stdout, stderr, did_app_timeout)
        """
        if self._pip_target and "--carb/app/extensions/pythonUserEnvPath" not in args:
            args = f"{args} --carb/app/extensions/pythonUserEnvPath={self._pip_target}"

        self.return_code, self.stdout, self.stderr, self.timed_out = self.run_command(
            self.app_exe_path, args, timeout, tee_output=tee_output
        )
        self.get_log_file()

        return self.return_code, self.stdout, self.stderr, self.timed_out

    def run_kitpy(self, args: str = "", timeout: int = 60) -> Tuple[int, AnyStr, AnyStr, bool]:
        """
        Run Kit's Python interpreter with the given options until it exits or the timeout is reached
        Args:
            args: arguments to be passed to Python
            timeout: seconds to wait before killing Python

        Returns:
            Tuple (return_code, stdout, stderr, if_python_timed_out)
        """
        return self.run_command(self.kitpy_path, args, timeout)

    def pip_install(
        self, package: str, timeout: int = 60, pypi_repo: str = None, upgrade: bool = False
    ) -> Tuple[int, AnyStr, AnyStr, bool]:
        """
        Installs a package to Kit's Python environment.
        Args:
            package: package name
            timeout: seconds to wait before killing pip
            pypi_repo: URL to a PyPI repository where to find the package
            upgrade: use the --upgrade/-U flag for the pip install command

        Returns:
            Tuple (return_code, stdout, stderr, if_pip_timed_out)
        """
        args = f"-m pip --isolated install {package}"
        if self._pip_target:
            args = f"{args} --target={self._pip_target}"
        if pypi_repo:
            args = f"{args} --extra-index-url={pypi_repo}"
        if upgrade:
            args = f"{args} --upgrade"

        return_code, stdout, stderr, timed_out = spawn_process(self.kitpy_path, args, timeout)

        return return_code, stdout, stderr, timed_out

    def detect_version(self) -> str:
        """
        Detects the package version from the PACKAGE_INFO.yaml file, if it exists

        Returns:
            The detected version, or an empty string otherwise

        Raises:
            RuntimeError if version could not be detected
        """
        pi_yaml = Path(self.app_root_dir) / "PACKAGE-INFO.yaml"
        if not pi_yaml.exists():
            return ""

        version_re = re.compile(r"^Version : ([\w.-]+)", re.MULTILINE)
        contents = pi_yaml.read_text()

        matches = version_re.findall(contents)

        if len(matches) == 1:
            return matches[0]

        raise RuntimeError(f"Too many matches found, likely PACKAGE-INFO.yaml has changed its structure: {matches}")

    def cleanup(self):
        """
        Removes the temporary environment for the Runner. This will be skipped
        if the Runner was instanced with a local path.
        """
        if not self.cleanup_required():
            _log.debug(f"Skipping delete of work dir: {self.build_extraction_dir}")
            return

        _log.debug(f"Deleting work dir: {self.build_extraction_dir}")

        utilities.remove_directory_item(self.build_extraction_dir)

    def cleanup_required(self) -> bool:
        """
        Provide an indication if the temporary environment would be cleaned.

        Returns:
            True if the Runner has to remove the local environment
        """
        return self._cleanup

    @classmethod
    def download_from_teamcity(
        cls, destination_dir: Union[str, Path], tc_build_id: Optional[int] = None
    ) -> Tuple[Path, str]:
        """
        Downloads the Kit archive from Teamcity

        Returns:
            A Tuple[path_to_archive, tc_build_number]

        Raises:
            FileNotFoundError if the artifact was not found in Teamcity
            RuntimeError if the artifact download was not successful
            EnvironmentError if run on an unsupported OS
        """
        destination_dir = _sanitize_path(destination_dir)

        _platform = utilities.PlatformHelper()
        # _platform_dir = _platform.architecture()

        if _platform.os == "Windows":
            build_type_id = cls.tc_windows_build_and_packaging_job
        else:
            build_type_id = cls.tc_linux_build_and_packaging_job

        artifact_file, build_number = download_artifact_regex(
            build_type_id, cls.artifact_re, destination_dir, tc_build_id
        )

        return artifact_file, build_number


def _sanitize_path(path: str) -> Path:
    """
    Given a string path, try to return a nicely formatted and resolved path

    Args:
        path: Input path to sanitize

    Returns:
        A clean, sanitized path
    """
    if not path:
        raise ValueError(f"Invalid path provided: {path}")

    return Path(path).expanduser()
