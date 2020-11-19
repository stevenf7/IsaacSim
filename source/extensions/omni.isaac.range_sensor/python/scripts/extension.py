import omni.ext
from .. import _range_sensor
from .menu import RangeSensorMenu


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._lidar = _range_sensor.acquire_lidar_sensor_interface()
        self._ultrasonic = _range_sensor.acquire_ultrasonic_sensor_interface()
        self._radar = _range_sensor.acquire_radar_sensor_interface()
        self._menu = RangeSensorMenu()

    def on_shutdown(self):
        self._menu.shutdown()
        self._menu = None
        _range_sensor.release_lidar_interface(self._lidar)
        _range_sensor.release_ultrasonic_interface(self._ultrasonic)
        _range_sensor.release_radar_interface(self._radar)
