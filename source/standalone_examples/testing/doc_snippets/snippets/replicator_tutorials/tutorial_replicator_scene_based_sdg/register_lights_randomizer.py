def setup_camera_bounds(
    pallet_prim: Usd.Prim, forklift_prim: Usd.Prim, pallet_tf: Gf.Matrix4d, forklift_tf: Gf.Matrix4d
) -> dict[str, dict[str, tuple[float, float, float]]]:
    """Calculate camera randomization bounds for pallet, top view, and driver cameras."""
    pallet_pos = pallet_tf.ExtractTranslation()
    pallet_cam_bounds = {
        "min": (pallet_pos[0] - 2, pallet_pos[1] - 2, 2),
        "max": (pallet_pos[0] + 2, pallet_pos[1] + 2, 4),
    }

    forklift_pos = forklift_tf.ExtractTranslation()
    top_cam_bounds = {
        "min": (forklift_pos[0], forklift_pos[1], 9),
        "max": (forklift_pos[0], forklift_pos[1], 11),
    }

    driver_cam_pos = forklift_pos + Gf.Vec3d(0.0, 0.0, 1.9)
    driver_cam_bounds = {
        "min": (driver_cam_pos[0], driver_cam_pos[1], driver_cam_pos[2] - 0.25),
        "max": (driver_cam_pos[0], driver_cam_pos[1], driver_cam_pos[2] + 0.25),
    }

    return {
        "pallet_cam": pallet_cam_bounds,
        "top_cam": top_cam_bounds,
        "driver_cam": driver_cam_bounds,
    }


# Calculate camera randomization bounds
camera_bounds = setup_camera_bounds(pallet_prim, forklift_prim, pallet_tf, forklift_tf)
pallet_cam_bounds_min = camera_bounds["pallet_cam"]["min"]
pallet_cam_bounds_max = camera_bounds["pallet_cam"]["max"]
top_cam_bounds_min = camera_bounds["top_cam"]["min"]
top_cam_bounds_max = camera_bounds["top_cam"]["max"]
driver_cam_bounds_min = camera_bounds["driver_cam"]["min"]
driver_cam_bounds_max = camera_bounds["driver_cam"]["max"]
