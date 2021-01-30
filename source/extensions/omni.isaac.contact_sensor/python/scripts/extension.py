import omni.ext
import omni.kit.commands
import gc
from .. import _contact_sensor

EXTENSION_NAME = "Contact Sensor"


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._cs = _contact_sensor.acquire_contact_sensor_interface()

    def on_shutdown(self):
        _contact_sensor.release_contact_sensor_interface(self._cs)
        gc.collect()
