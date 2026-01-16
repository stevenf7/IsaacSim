def setup_cone_placement_corners(
    forklift_prim: Usd.Prim, bb_cache=None, scale_factor: float = 1.3
) -> tuple[list[list[float]], tuple[float, float, float]]:
    """Calculate forklift OBB corners for cone placement, returns (corner_positions, rotation_degrees)."""
    if bb_cache is None:
        bb_cache = create_bbox_cache()

    forklift_obb_center, forklift_obb_axes, forklift_obb_extent = compute_obb(bb_cache, forklift_prim.GetPrimPath())
    enlarged_extent = (
        forklift_obb_extent[0] * scale_factor,
        forklift_obb_extent[1] * scale_factor,
        forklift_obb_extent[2],
    )
    forklift_obb_corners = get_obb_corners(forklift_obb_center, forklift_obb_axes, enlarged_extent)

    cone_placement_corners = [
        forklift_obb_corners[0].tolist(),
        forklift_obb_corners[2].tolist(),
        forklift_obb_corners[4].tolist(),
        forklift_obb_corners[6].tolist(),
    ]

    forklift_obb_quat = Gf.Matrix3d(forklift_obb_axes).ExtractRotation().GetQuaternion()
    forklift_obb_quat_xyzw = (forklift_obb_quat.GetReal(), *forklift_obb_quat.GetImaginary())
    forklift_rotation_deg = quat_to_euler_angles(np.array(forklift_obb_quat_xyzw), degrees=True)

    return cone_placement_corners, forklift_rotation_deg


# Setup cone placement
cone_placement_corners, forklift_rotation_deg = setup_cone_placement_corners(forklift_prim)
