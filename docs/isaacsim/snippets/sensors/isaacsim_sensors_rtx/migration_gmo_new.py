from isaacsim.sensors.experimental.rtx import Lidar, LidarSensor, parse_generic_model_output_data

sensor = LidarSensor(
    Lidar.create("/World/Lidar", config="Example_Rotary"),
    annotators=["generic-model-output"],
)
data, info = sensor.get_data("generic-model-output")
gmo = parse_generic_model_output_data(data)
