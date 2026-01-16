from isaacsim.sensors.physics import _sensor

_contact_sensor_interface = _sensor.acquire_contact_sensor_interface()
_contact_sensor_interface.get_sensor_reading("/World/Cube/Contact_Sensor", use_latest_data=True)
