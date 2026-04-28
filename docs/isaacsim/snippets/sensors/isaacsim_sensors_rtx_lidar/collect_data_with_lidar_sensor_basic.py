from isaacsim.sensors.experimental.rtx import Lidar, LidarSensor, parse_generic_model_output_data

lidar = Lidar.create("/World/Lidar", config="Example_Rotary")

sensor = LidarSensor(lidar, annotators=["generic-model-output"])
data, info = sensor.get_data("generic-model-output")
gmo = parse_generic_model_output_data(data)
