from isaacsim.sensors.camera import SingleViewDepthSensorAsset

asset_path = "example_camera_with_depth_sensor.usd"
example_depth_sensor = SingleViewDepthSensorAsset(prim_path="/example_depth_sensor", asset_path=asset_path)
example_depth_sensor.initialize()
