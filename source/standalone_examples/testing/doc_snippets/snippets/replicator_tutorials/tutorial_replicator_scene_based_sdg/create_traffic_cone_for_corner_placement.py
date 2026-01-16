def create_scatter_plane_for_prim(
    prim: Usd.Prim, prim_tf: Gf.Matrix4d, parent_path: str, scale_factor: float = 0.8, visible: bool = False
) -> Usd.Prim:
    """Create scatter plane sized and aligned to prim surface."""
    bb_cache = create_bbox_cache()
    prim_bbox = bb_cache.ComputeLocalBound(prim)
    prim_bbox.Transform(prim_tf)
    prim_size = prim_bbox.GetRange().GetSize()

    prim_quat = prim_tf.ExtractRotation().GetQuaternion()
    prim_quat_xyzw = (prim_quat.GetReal(), *prim_quat.GetImaginary())
    prim_rotation_deg = quat_to_euler_angles(np.array(prim_quat_xyzw), degrees=True)

    prim_pos = prim_tf.ExtractTranslation()
    scatter_plane_scale = (prim_size[0] * scale_factor, prim_size[1] * scale_factor, 1)
    scatter_plane_pos = prim_pos + Gf.Vec3d(0, 0, prim_size[2])

    scatter_plane = rep.functional.create.plane(
        scale=scatter_plane_scale,
        position=tuple(scatter_plane_pos),
        rotation=tuple(prim_rotation_deg),
        visible=visible,
        parent=parent_path,
    )

    return scatter_plane


# Setup scatter plane
pallet_tf = omni.usd.get_world_transform_matrix(pallet_prim)
scatter_plane = create_scatter_plane_for_prim(pallet_prim, pallet_tf, parent_path="/SDG", scale_factor=0.8)
