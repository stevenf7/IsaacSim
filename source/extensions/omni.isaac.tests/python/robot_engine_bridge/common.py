import carb.tokens
import os


def setup_base_prim(prim):
    prim.CreateNodeNameAttr("interface")
    prim.CreateEnabledAttr(True)
    prim.CreateTimeOffsetAttr(0.0)


def get_json_data_path(filename):
    output = os.path.abspath(
        carb.tokens.get_tokens_interface().resolve(
            "${app}/../exts/omni.isaac.tests/omni/isaac/tests/data/robot_engine_bridge/" + filename
        )
    )
    print("OUTPUT", output)
    return output


class PyaliceApp:
    def __init__(self):
        from omni.isaac.pyalice import Application

        self._asset_path = os.path.abspath(
            carb.tokens.get_tokens_interface().resolve("${app}/../exts/omni.isaac.robot_engine_bridge/")
        )
        self.app = Application(name="test", asset_path=self._asset_path)
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
