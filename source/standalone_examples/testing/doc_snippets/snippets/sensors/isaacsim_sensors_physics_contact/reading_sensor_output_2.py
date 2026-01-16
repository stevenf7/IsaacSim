from isaacsim.sensors.physics import _sensor

_contact_sensor_interface = _sensor.acquire_contact_sensor_interface()
raw_data = _contact_sensor_interface.get_contact_sensor_raw_data("/World/Cube/Contact_Sensor")
print(str(raw_data))
