# Create SDG scope for organizing all generated objects
sdg_scope = stage.DefinePrim("/SDG", "Scope")

# Create cameras
rep.functional.create.scope(name="Cameras", parent="/SDG")
driver_cam = rep.functional.create.camera(
    focus_distance=400.0,
    focal_length=24.0,
    clipping_range=(0.1, 10000000.0),
    name="DriverCam",
    parent="/SDG/Cameras",
)
pallet_cam = rep.functional.create.camera(name="PalletCam", parent="/SDG/Cameras")
top_view_cam = rep.functional.create.camera(clipping_range=(6.0, 1000000.0), name="TopCam", parent="/SDG/Cameras")
