# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.ext
import omni.usd
from omni.physx import get_physx_interface

from .. import _range_sensor
from .proximity_sensor import ProximitySensorManager, clear_sensors


class Extension(omni.ext.IExt):
    def on_startup(self):
        # step the sensor every physics step
        self._physics_step_subscription = get_physx_interface().subscribe_physics_step_events(self._on_update)
        self._proximity_sensor_manager = ProximitySensorManager()  # Store instance to sensor manager singleton
        self._lidar = _range_sensor.acquire_lidar_sensor_interface()
        self._ultrasonic = _range_sensor.acquire_ultrasonic_sensor_interface()
        self._generic = _range_sensor.acquire_generic_sensor_interface()
        self._lightbeam = _range_sensor.acquire_lightbeam_sensor_interface()

    def on_shutdown(self):
        # Handle ProximitySensorManager
        self._physics_step_subscription = None  # clear subscription
        clear_sensors()  # clear sensors on shutdown
        self._proximity_sensor_manager = None

        # Release sensor interfaces
        _range_sensor.release_lidar_sensor_interface(self._lidar)
        _range_sensor.release_ultrasonic_sensor_interface(self._ultrasonic)
        _range_sensor.release_generic_sensor_interface(self._generic)
        _range_sensor.release_lightbeam_sensor_interface(self._lightbeam)

    def _on_update(self, dt):
        self._proximity_sensor_manager.update()
        pass
