# Setup render products
resolution = config.get("resolution", (512, 512))
forklift_rp = rep.create.render_product(top_view_cam, resolution, name="TopView")
driver_rp = rep.create.render_product(driver_cam, resolution, name="DriverView")
pallet_rp = rep.create.render_product(pallet_cam, resolution, name="PalletView")

render_products = [forklift_rp, driver_rp, pallet_rp]
for render_product in render_products:
    render_product.hydra_texture.set_updates_enabled(False)

# Initialize writer and attach to render products
writer = setup_writer(config)
if not writer:
    print("[SDG] Failed to setup writer")
    return

writer.attach(render_products)

for render_product in render_products:
    render_product.hydra_texture.set_updates_enabled(True)
