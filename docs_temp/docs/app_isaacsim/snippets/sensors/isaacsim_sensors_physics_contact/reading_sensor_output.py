from isaacsim.sensors.experimental.physics import ContactSensorBackend

_contact_sensor_backend = ContactSensorBackend("/World/Cube/Contact_Sensor")
_contact_sensor_backend.get_sensor_reading()
