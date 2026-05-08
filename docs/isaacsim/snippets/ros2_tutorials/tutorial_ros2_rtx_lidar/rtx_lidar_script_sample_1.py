import omni.replicator.core as rep

# RTX sensors are cameras and must be assigned to their own render product.
hydra_texture = rep.create.render_product(lidar.paths[0], [1, 1], name="Isaac")
