import logging
import re
from pathlib import Path
from typing import Optional, Union

from process_helper import tee

from . import kit_runner, utilities

_log = logging.getLogger("create_runner")


class CreateRunner(kit_runner.KitRunner):
    """
    What's different to Kit?
    + We're using Kit, but are NOT kit. We download Kit's SDK via Packman (this can take a while - It's 1.x Gb)
    + Rather than a single exe, there are a number of script files that wrap kit calling "experiences" (which are .kit files)
    + One of these has to be specified either via the app_exe_path or an experience_name
    + TC job names etc are obviously different
    """

    app_shortname = "Create"
    tc_windows_build_and_packaging_job = "Omniverse_OvCreate_Master_WindowsX8664"
    tc_linux_build_and_packaging_job = "Omniverse_OvCreate_Master_LinuxX8664"

    artifact_re = r".*@\d+\.\d+\.\d+(?:-rc.\d+)?-.*\.7z"
    build_re = re.compile(rf"create@(\d+\.\d+\.\d+(?:-rc.\d+)?)-.*\.7z")

    def __init__(
        self,
        tc_build_id: Optional[int] = 0,
        app_root_dir: Optional[Union[str, Path]] = None,
        build_extraction_dir: Optional[Union[str, Path]] = None,
        build_archive_path: Optional[Union[str, Path]] = None,
        app_exe_path: Optional[Union[str, Path]] = None,
        experience_name: Optional[str] = "create",
        kit_tc_build_id: Optional[str] = None,
    ):

        """
        (Just showing changes wrt KitRunner - i.e the baseclass)

        Args:
            experience_name: The name of an experience e.g "create", "create-mini", "create-next" which has a
                supporting .bat/.sh script and a .kit file in the "apps" folder (maybe should be called appName?)

        """

        if not app_exe_path and not experience_name:
            raise ValueError("You must pass either app_exe_path or experience_name.")

        super().__init__(tc_build_id, app_root_dir, build_extraction_dir, build_archive_path, app_exe_path)
        self.experience_name = experience_name
        self.kit_tc_build_id = kit_tc_build_id

    def _find_exe(self):
        """
        Try to find the chosen experience script and Kit Python script inside the app_root_dir
        The current convention is "omni.create.bat", for an experience called "create"

        Note that this is hardcoded to use the release build
        """
        expected_app_exe_path = (
            f"_build/{self._platform.architecture()}/"
            f"release/omni.{self.experience_name}{self._platform.script_extension()}"
        )
        expected_kitpy_path = (
            "_build/target-deps/kit_sdk_release/_build"
            + self._platform.architecture()
            + "/release/python"
            + self._platform.script_extension()
        )
        exe = self.app_root_dir / expected_app_exe_path
        if not exe.exists():
            raise FileNotFoundError(f"Could not find the Create experience script, looked in: {exe}")
        self.app_exe_path = exe

        # We don't care about this so much, don't assert if its missing
        self.kitpy_path = self.app_root_dir / expected_kitpy_path

    def get_log_file(self):
        """
        Try to discover an `omniverse-kit.log` file in the directory structure of the App

        Returns:
            A Path object to the logfile if found, None otherwise
        """

        # @note The log path is in a place I don't really know how to derive...
        # it's what's below + e.g "create/100.1.3387" - so app name/build?
        expected_log_path_rel = (
            "_build/target-deps/kit_sdk_release/_build/"
            + self._platform.architecture()
            + "/release/data/Kit"
            + "/omni."
            + self.experience_name
        )
        if not self.app_root_dir:
            _log.debug("dont have an app_root_dir, so no log found!")
            return None

        expected_log_path = self.app_root_dir / expected_log_path_rel
        _log.debug("looking for log in %s" % expected_log_path)

        logs = [f for f in utilities.find_rglob(expected_log_path, "omniverse-kit.log") if f.is_file()]
        if len(logs) == 1:
            self.log_file = logs.pop()
        else:
            self.log_file = None
        _log.debug("found log file %s" % self.log_file)
        return self.log_file

    def prepare(self) -> Path:
        """
        Sets up the Create environment. If a app_root_dir was passed, just initialize paths,
        otherwise, download Create from Teamcity and extract it

        Returns:
            The path to the Kit executable

        Raises:
            FileNotFoundError if the artifact download from Teamcity fails
            RuntimeError if the artifact download was not successful
        """

        path = super().prepare()

        if self.kit_tc_build_id:
            # if we are using a different kit archive update the deps XML to indicate it
            _log.debug("===========Updating %s to use kit build %s" % (self.app_root_dir, self.kit_tc_build_id))
            utilities.writeUpdatedPackmanDeps(self.app_root_dir, self.kit_tc_build_id)

        # This is pulling down the kit_sdk.
        # We want to do this separately from launching Kit as it can take
        # a reasonable amount of time,
        autopull_path = self.app_root_dir / Path("tools/autopull/autopull" + self._platform.script_extension())
        args = " --config release"
        # need a fairly long timeout here as it's downloading 1.2Gb of Kit_SDK, then decompressing it
        timeout = 10000
        _log.debug(f"Starting Download of Kit SDK - setting timeout to {timeout}s as it can be slow!")

        # NOTE: would be nice to use the packman API directly,
        # but not easy to get it right now as a pip package
        return_code, stdout, stderr, timed_out = tee(autopull_path, args, timeout)
        _log.debug(f"Finished Download of Kit SDK")
        _log.debug(f"self.app_root_dir {self.app_root_dir}")
        return path
