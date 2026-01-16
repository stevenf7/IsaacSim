# Create the cameras using Replicator's functional API
cameras = []
num_cameras = capture_config.get("num_cameras", 0)
rep.functional.create.scope(name="Cameras")
for i in range(num_cameras):
    cam_prim = rep.functional.create.camera(parent="/Cameras", name=f"cam_{i}", clipping_range=(0.25, 1000))
    cameras.append(cam_prim)

# Create the render products for the cameras
render_products = []
resolution = capture_config.get("resolution", (1280, 720))
disable_render_products = capture_config.get("disable_render_products", False)
for cam in cameras:
    rp = rep.create.render_product(cam.GetPath(), resolution, name=f"rp_{cam.GetName()}")
    if disable_render_products:
        rp.hydra_texture.set_updates_enabled(False)
    render_products.append(rp)
