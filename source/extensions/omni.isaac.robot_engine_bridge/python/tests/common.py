import omni


def setup_base_prim(prim):
    prim.CreateNodeNameAttr("interface")
    prim.CreateEnabledAttr(True)
    prim.CreateTimeOffsetAttr(0.0)


class PyaliceApp:
    def __init__(self):
        from omni.isaac.pyalice import Application

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.robot_engine_bridge")
        self._reb_extension_path = ext_manager.get_extension_path(ext_id)

        self.app = Application(name="test", asset_path=self._reb_extension_path)
        self._stopped = True

    def run(self, duration: float = 1.0):
        self.app.start_wait_stop(duration)

    def start(self):
        self.app.start()
        self._stopped = False

    def stop(self):
        if self._stopped is False:
            self.app.stop()
            self._stopped = True

    def __del__(self):
        self.stop()
