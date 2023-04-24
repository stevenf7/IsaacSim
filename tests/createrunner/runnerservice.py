import os
import platform
from pathlib import Path
from typing import AnyStr, Dict, List, Optional, Tuple, Union

from nv_benchflow.client import Benchmark, Inputs, service_method
from nv_benchflow.client.services import BenchmarkServiceNotFoundException


class BaseRunnerService:
    """
    Base class for functionality used by Kit related runner services..
    """

    service_name = "BaseRunnerService"
    app_name = "base"

    def clean(self):
        """
        The `clean()` function is automatically called on your behalf after your Test
        completes, *regardless* of whether or not it was successful or errored out.

        This method is responsible for adding `omniverse-kit.log` as an output, as well as
        Kit's stdout and stderr. If Kit was downloaded from Teamcity to a temporary directory,
        it will be deleted as well.
        """
        # this throws an exception if Kit was never prepared
        logFile = self._k.get_log_file()
        if logFile:
            Benchmark.outputs.add_file_contents("omniverse-kit.log", logFile.read_bytes())
        if self._k.stdout:
            Benchmark.outputs.add_file_contents("Kit stdout.txt", self._k.stdout)
        if self._k.stderr:
            Benchmark.outputs.add_file_contents("Kit stderr.txt", self._k.stderr)
        if self._k.cleanup_required():
            Benchmark.log_info(f"Deleting {self.app_name}'s work directory: {self._k.build_extraction_dir}")
            # this will error the task, but in reality we shouldn't
            try:
                self._k.cleanup()
            except PermissionError as e:
                Benchmark.log_error(f"Unable to cleanup {self.app_name}'s work directory: {e}")
                Benchmark.log_error(f"Leftover files: {list(Path(self._k.build_extraction_dir).rglob('*'))}")
        else:
            Benchmark.log_info(f"Skipping deletion of {self.app_name}'s work directory: {self._k.build_extraction_dir}")

    # RPC Service Methods
    @service_method
    def prepare(self):
        """
        Sets up the Kit environment. If a Local Kit Directory was passed, just initialize paths,
        otherwise, download Kit from Teamcity and extract it.

        Try to automatically configure the MQTT Synchronizer library if the service is part of
        this task definition, as well as Omnitrace.

        """
        Benchmark.log_info(f"Preparing {self.app_name} in {self._k.build_extraction_dir}")
        if self._tc_build_id:
            Benchmark.log_info("Downloading from Teamcity, this can take a while")
        self._k.prepare()

        # OVAT Synchronizer Support
        try:
            synchronizer = Benchmark.services.find_service("Synchronizer", "0.1")
            Benchmark.log_info(self.service_name + " found a Synchronizer Service, setting up the environment for Kit")
            mqtt_url, task_id = synchronizer.get_config()
            self.set_env("MQTT_SYNC_URL", mqtt_url)
            self.set_env("MQTT_SYNC_ID", task_id)
            self.pip_install("nv-mqtt-synchronizer==1.8.3", upgrade=True)
        except BenchmarkServiceNotFoundException:
            pass

        # Omnitrace Support
        try:
            omnitrace = Benchmark.services.find_service("Omnitrace", "0.1")
            Benchmark.log_info(self.service_name + " found an Omnitrace Service, overlaying files and setting env vars")
            if Inputs.skip_omnitrace_overlay:
                Benchmark.log_info(
                    self.service_name + " is skipping the Omnitrace overlay (file copy) by request"
                    " (Skip Omnitrace Overlay = True)"
                )
            else:
                self.add_overlaid_content(omnitrace.get_kit_overlay_path())
            env_vars: Dict = omnitrace.get_env_vars()
            for name, value in env_vars.items():
                Benchmark.log_info(f"Setting env {name}={value}")
                os.environ[name] = value
        except BenchmarkServiceNotFoundException:
            pass

    @service_method
    def run_kit(self, args: str = "", timeout: Optional[int] = None) -> Tuple[int, AnyStr, AnyStr, bool]:
        """
        Runs Kit in a blocking manner.

        Args:
            args: command line options to pass to Kit
            timeout: time limit in seconds for Kit's execution

        Returns:
            Tuple of (return_code, stdout, stderr, did_kit_timeout)
        """
        timeout = timeout if timeout else Inputs.timeout

        # we have to suppress some Kit plugins' log because it spams the log
        # and makes debugging impossible
        suppress_plugins = ["carb.fastcache.plugin"]

        for plugin in suppress_plugins:
            if f"--carb/log/sources/{plugin}/level" not in args:
                args = f"{args} --carb/log/sources/{plugin}/level=Warning"

        # we need to be in our kit directory to capture crash dumps
        _cur_dir = os.getcwd()
        os.chdir(self._k.app_root_dir)

        # GTL runs as root on Linux and Kit doesn't like that
        if platform.system() == "Linux" and os.geteuid() == 0:
            if "DISPLAY" not in os.environ:
                os.environ["DISPLAY"] = ":0"
            if "--allow-root" not in args:
                args = f"{args} --allow-root"

        Benchmark.log_info(
            f"Launching {self.app_name} (timeout={timeout}) with commandline: {self._k.app_exe_path} {args}"
        )
        try:
            return_code, stdout, stderr, timed_out = self._k.run_app(
                args=args, timeout=timeout, tee_output=Inputs.realtime_output
            )
        finally:
            os.chdir(_cur_dir)

        return return_code, stdout, stderr, timed_out

    @service_method
    def run_command(
        self, app_exe_path: Union[str, Path], args: str = "", timeout: Optional[int] = None
    ) -> Tuple[int, AnyStr, AnyStr, bool]:
        """
        Runs a command under the Kit base path
        Args:
            exe_path: relative path (anchored to the Kit root) to an executable
            args: command line options to pass to Kit
            timeout: time limit in seconds for Kit's execution

        Returns:
            Tuple of (return_code, stdout, stderr, did_command_timeout)
        """
        timeout = timeout if timeout else Inputs.timeout

        app_exe_path = self._k.app_root_dir / app_exe_path

        Benchmark.log_info(f"Launching custom command (timeout={timeout}) with commandline: {app_exe_path} {args}")
        return_code, stdout, stderr, timed_out = self._k.run_command(
            app_exe_path=app_exe_path, args=args, timeout=timeout
        )

        return return_code, stdout, stderr, timed_out

    @service_method
    def run_kitpy(self, args: str = "", timeout: Optional[int] = None) -> Tuple[int, AnyStr, AnyStr, bool]:
        """
        Runs Kit's Python interpreter with the given arguments

        Args:
            args: arguments to pass to Kit's python interpreter
            timeout: timeout to wait

        Returns:
            Tuple of (return_code, stdout, stderr, did_command_timeout)
        """
        return self._k.run_kitpy(args, timeout)

    @service_method
    def pip_install(
        self, package: str, pypi_repo: str = "https://pypi.perflab.nvidia.com/simple", upgrade: bool = False
    ):
        """
        Install a Python package from PyPI to Kit's Python environment

        Args:
            package: Name of package
            pypi_repo: Optional PyPI URL to source package from, Perflab's PyPI by default
            upgrade: Flag to request a pip upgrade instead of normal install
        """
        Benchmark.log_info(f"Installing Python Package: {package} to Kit's Python Environment")
        self._k.pip_install(package, pypi_repo=pypi_repo, upgrade=upgrade)

    @service_method
    def set_env(self, key: str, value: str):
        """
        Sets an environment variable for Kit's process

        Args:
            key: name of environment variable to set
            value: value for variable
        """
        os.putenv(key, value)

    @service_method
    def add_overlaid_content(self, root_dir: Union[str, Path]):
        """
        Adds the file and directory structure at the given path to the Kit directory.
        Please note:

        !platform is a special directory name that will be replaced with
        the current OS platform so that files can be overlaid regardless
        of the platform-specific Kit directory structure

        Args:
            root_dir: path with special components (!platform) that contains the file
            and directory structure to overlay on top of Kit
        """
        Benchmark.log_info(
            f"Overlaying content from: {root_dir} to {self.app_name}'s directory: {self._k.app_root_dir}"
        )
        self._k.add_overlaid_content(root_dir)

    @service_method
    def get_log_path(self) -> Union[Path, None]:
        """
        Returns the path to the Kit log file if it exists, None otherwise
        """
        return self._k.log_file

    @service_method
    def get_kit_dir(self) -> Path:
        """
        Returns the path to the Kit directory
        """
        return self._k.app_root_dir

    @service_method
    def get_omnitrace_captures(self) -> List[Path]:
        """
        Returns a list of all paths to Omnitrace OTB files in the Kit directory
        """
        otbs = []

        if self._k.app_root_dir:
            p = Path(self._k.app_root_dir)
            otbs = [x for x in p.rglob("*.otb")]

        return otbs

    @service_method
    def get_crashdumps(self) -> List[Path]:
        """
        Returns a list of paths to all crash dumps in the Kit directory
        """
        dumps = []

        if self._k.app_root_dir:
            p = Path(self._k.app_root_dir)
            dumps = [x for x in p.rglob("*.dmp")]

        return dumps

    @service_method
    def detect_version(self) -> str:
        """
        Detects the package version from the PACKAGE_INFO.yaml file, if it exists

        Returns:
            The detected version, or an empty string otherwise
        """
        return self._k.detect_version()
