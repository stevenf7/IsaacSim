import omni.kit.commands
import omni.kit.utils
from omni.isaac.urdf import _urdf
import os


class CreateURDFImportConfigCommand(omni.kit.commands.Command):
    def __init__(self,):
        pass

    def do(self):
        return _urdf.ImportConfig()
        pass

    def undo(self):
        pass


class ParseURDFCommand(omni.kit.commands.Command):
    def __init__(self, urdf_path: str = "", import_config=_urdf.ImportConfig()):
        self._root_path, self._filename = os.path.split(os.path.abspath(urdf_path))
        self._import_config = import_config
        self._urdf_interface = _urdf.acquire_urdf_interface()
        pass

    def do(self):
        return self._urdf_interface.parse_urdf(self._root_path, self._filename, self._import_config)
        pass

    def undo(self):
        pass


class ParseAndImportURDFCommand(omni.kit.commands.Command):
    def __init__(self, urdf_path: str = "", import_config=_urdf.ImportConfig()):
        self._urdf_path = urdf_path
        self._root_path, self._filename = os.path.split(os.path.abspath(urdf_path))
        self._import_config = import_config
        self._urdf_interface = _urdf.acquire_urdf_interface()
        pass

    def do(self):
        status, imported_robot = omni.kit.commands.execute(
            "ParseURDFCommand", urdf_path=self._urdf_path, import_config=self._import_config
        )
        return self._urdf_interface.import_robot(self._root_path, self._filename, imported_robot, self._import_config)

        pass

    def undo(self):
        pass


omni.kit.commands.register_all_commands_in_module(__name__)
