from isaacsim.sensors.experimental.physics import ContactSensorBackend

_contact_sensor_backend = ContactSensorBackend("/World/Cube/Contact_Sensor")
raw_data = _contact_sensor_backend.get_raw_data()
print(str(raw_data))
