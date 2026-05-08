hydra_texture_2D = rep.create.render_product(lidar_2D.paths[0], [1, 1], name="Isaac")

writer = rep.writers.get("RtxLidarROS2PublishLaserScan")
writer.initialize(topicName="scan", frameId="base_scan")
writer.attach([hydra_texture_2D])
