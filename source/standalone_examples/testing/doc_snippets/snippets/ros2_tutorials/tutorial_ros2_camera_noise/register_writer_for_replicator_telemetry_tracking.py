# Create the new writer and attach to our render product
writer = rep.writers.get(f"CustomROS2PublishImage")
writer.initialize(topicName="rgb_augmented", frameId="sim_camera")
writer.attach([render_product_path])
