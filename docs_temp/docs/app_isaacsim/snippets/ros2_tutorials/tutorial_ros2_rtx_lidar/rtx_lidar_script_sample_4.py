hydra_texture_2D = rep.create.render_product(sensor_2D.GetPath(), [1, 1], name="Isaac")

writer = rep.writers.get("RtxLidar" + "ROS2PublishLaserScan")
writer.initialize(topicName="scan", frameId="base_scan")
writer.attach([hydra_texture_2D])
