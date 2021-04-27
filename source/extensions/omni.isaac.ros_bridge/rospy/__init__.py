import os, sys
import omni.ext


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        self._ros_extension_path = ext_manager.get_extension_path(ext_id)
        sys.path.append(os.path.join(os.path.dirname(self._ros_extension_path + "/noetic/lib/python3/dist-packages/")))

    def on_shutdown(self):
        sys.path.remove(os.path.join(os.path.dirname(self._ros_extension_path + "/noetic/lib/python3/dist-packages/")))
