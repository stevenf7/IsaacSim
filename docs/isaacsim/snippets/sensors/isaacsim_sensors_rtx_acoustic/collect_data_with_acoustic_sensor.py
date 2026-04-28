from isaacsim.sensors.experimental.rtx import Acoustic, AcousticSensor, parse_generic_model_output_data

acoustic = Acoustic.create("/World/Acoustic")

sensor = AcousticSensor(acoustic, annotators=["generic-model-output"])
data, info = sensor.get_data("generic-model-output")
gmo = parse_generic_model_output_data(data)

# gmo.x      -> transmitter mount IDs
# gmo.y      -> receiver mount IDs
# gmo.z      -> channel IDs
# gmo.scalar -> amplitude values
